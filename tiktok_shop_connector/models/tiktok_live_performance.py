import logging
from datetime import timedelta, datetime
from odoo import api, models, fields, _
from .tiktok_shop import MAX_CONCURRENT_THREADS

_logger = logging.getLogger(__name__)


class TiktokLivePerformance(models.Model):
    _name = "tiktok.live.performance"
    _description = "TikTok Live Performance Analytics"
    _order = "start_time desc, gmv_amount desc"

    # ===== Basic Information =====
    live_id = fields.Char(string="Live ID", required=True, index=True)
    shop_id = fields.Many2one("tiktok.shop", string="Shop", required=True, index=True)

    # ===== Live Stream Info =====
    title = fields.Char(string="Live Title")
    username = fields.Char(string="Host Username")
    start_time = fields.Datetime(string="Start Time", required=True, index=True)
    end_time = fields.Datetime(string="End Time")
    duration_minutes = fields.Float(string="Duration (Minutes)", compute="_compute_duration", store=True)

    # ===== Sales Performance =====
    gmv_amount = fields.Float(string="GMV Amount", digits=(16, 2))
    gmv_currency = fields.Char(string="GMV Currency", default="USD")

    products_added = fields.Integer(string="Products Added")
    different_products_sold = fields.Integer(string="Different Products Sold")
    created_sku_orders = fields.Integer(string="Created SKU Orders")
    sku_orders = fields.Integer(string="SKU Orders")
    unit_sold = fields.Integer(string="Units Sold")
    customers = fields.Integer(string="Customers")

    avg_price_amount = fields.Float(string="Average Price", digits=(16, 2))
    avg_price_currency = fields.Char(string="Avg Price Currency", default="USD")
    click_to_order_rate = fields.Float(string="Click to Order Rate (%)", digits=(5, 2))

    # 24h Live GMV
    live_gmv_24h_amount = fields.Float(string="24h Live GMV", digits=(16, 2))
    live_gmv_24h_currency = fields.Char(string="24h Live GMV Currency", default="USD")

    # ===== Interaction Performance =====
    acu = fields.Integer(string="Average Concurrent Users")
    pcu = fields.Integer(string="Peak Concurrent Users")
    viewers = fields.Integer(string="Viewers")
    views = fields.Integer(string="Views")
    avg_viewing_duration = fields.Float(string="Avg Viewing Duration (seconds)")
    comments = fields.Integer(string="Comments")
    shares = fields.Integer(string="Shares")
    likes = fields.Integer(string="Likes")
    new_followers = fields.Integer(string="New Followers")

    # Product Engagement
    product_impressions = fields.Integer(string="Product Impressions")
    product_clicks = fields.Integer(string="Product Clicks")
    click_through_rate = fields.Float(string="Click Through Rate (%)", digits=(5, 2))

    @api.depends('live_id', 'start_time')
    def _compute_display_name(self):
        for record in self:
            if record.end_time:
                record.display_name = f"Live {record.live_id} - {record.start_time.strftime('%Y-%m-%d')} -> {record.end_time.strftime('%Y-%m-%d')}"
            else:
                record.display_name = f"Live {record.live_id} - {record.start_time.strftime('%Y-%m-%d')} -> Unknown"

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for record in self:
            if record.start_time and record.end_time:
                duration = record.end_time - record.start_time
                record.duration_minutes = duration.total_seconds() / 60
            else:
                record.duration_minutes = 0

    @api.model
    def _get_smart_report_date_range(self, shop):
        """
        Lấy date range thông minh cho shop (start_date, end_date).
        """
        shop.ensure_one()
        context_today = fields.Date.context_today
        today = context_today(self)
        last_call = self.env.context.get('last_call', False)
        if last_call:
            last_call = context_today(last_call)
        sync_data_since = context_today(self, shop.sync_data_since) if shop.sync_data_since else False

        start_date = end_date = False

        # 1. Lấy start_time gần nhất từ tiktok.live.performance
        last_start_time = self.env['tiktok.live.performance'].search([
            ('shop_id', '=', shop.id)
        ], order='start_time desc', limit=1).start_time
        if last_start_time:
            start_date = min(context_today(self, last_start_time) + timedelta(days=1), (last_call or today))
            if sync_data_since:
                start_date = max(start_date, sync_data_since)

        # 2. Chưa có báo cáo, lấy ngày đơn hàng đầu tiên
        if not start_date:
            first_order_date = self.env['tiktok.order'].search([
                ('shop_id', '=', shop.id)
            ], order='create_time asc', limit=1).create_time
            if first_order_date:
                start_date = context_today(self, first_order_date)
                if sync_data_since:
                    start_date = max(start_date, sync_data_since)

        # 3. Chưa có đơn hàng, lấy 7 ngày trước
        if not start_date:
            start_date = today - timedelta(days=7)
            if sync_data_since:
                start_date = max(start_date, sync_data_since)

        end_date = min(start_date + timedelta(days=7), today)

        # Nếu start_date >= end_date thì không còn gì mới để lấy
        if start_date >= end_date:
            return False, False

        return start_date, end_date

    @api.model
    def _sync_live_performance(self, shop, start_date=None, end_date=None):
        """
        Sync live performance theo batch (7 ngày một lần) để tối ưu tốc độ.
        """
        shop.ensure_one()
        sync_from_cron = self.env.context.get('sync_from_cron', False)

        # Nếu không truyền start_date và end_date thì lấy smart date range
        if not start_date or not end_date:
            start_date, end_date = self._get_smart_report_date_range(shop)

        if not start_date or not end_date:
            _logger.warning(f"Shop {shop.name}: No new live performance data found, stopping sync")
            return {
                'total_synced': 0,
                'has_more_dates': False,
            }

        _logger.info(f"Shop {shop.name}: Starting batch live performance sync from {start_date} to {end_date}")

        page_token = None
        page_number = 1
        total_synced = 0

        while True:
            # Lấy 1 page live sessions từ Live List API với date range
            live_sessions, next_page_token, latest_available_date = self._get_live_performance_list_page(
                shop, start_date, end_date, page_token
            )

            if not live_sessions:
                _logger.info(f"Shop {shop.name}: No live sessions with performance data found on page {page_number}")

                # Kiểm tra logic thông minh để không bỏ lỡ dữ liệu
                if page_number == 1 and latest_available_date and end_date <= latest_available_date:
                    # Có latest_available_date và end_date chưa đến latest_available_date
                    # Tiếp tục lấy dữ liệu 7 ngày tiếp theo
                    start_date = min(end_date + timedelta(days=1), latest_available_date)  # Bắt đầu từ ngày sau end_date
                    end_date = min(start_date + timedelta(days=7), latest_available_date + timedelta(days=1))
                    _logger.info(f"Shop {shop.name}: Moving live performance date range to {start_date.strftime('%Y-%m-%d')} --> {end_date.strftime('%Y-%m-%d')}")
                    continue
                else:
                    # Không có latest_available_date hoặc đã đến latest_available_date
                    _logger.info(f"Shop {shop.name}: No more live performance data available, stopping sync")
                    break

            _logger.info(f"Shop {shop.name}: Processing page {page_number}, got {len(live_sessions)} live performances")

            # Xử lý ngay page này với date range
            page_synced = 0
            for live_data in live_sessions:
                self._upsert_live_performance(shop, live_data)
                page_synced += 1
                total_synced += 1

            # Check pagination
            page_token = next_page_token
            if not page_token:
                break

            page_number += 1

        if total_synced == 0:
            _logger.warning(f"Shop {shop.name}: No live performance data found, stopping sync")
            if sync_from_cron:
                return {
                    'total_synced': total_synced,
                    'has_more_dates': end_date <= latest_available_date,
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Warning'),
                        'message': _('No live performance data found!'),
                        'type': 'warning',
                    }
                }

        _logger.info(f"Shop {shop.name}: Successfully synced {total_synced} live performances across {page_number} pages")

        if sync_from_cron:
            return {
                'total_synced': total_synced,
                'has_more_dates': end_date <= latest_available_date,
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Synced %d live performances successfully!') % total_synced,
                    'type': 'success',
                }
            }

    def _get_live_performance_list_page(self, shop, start_date, end_date, page_token=None):
        """Get 1 page of live performance data from TikTok API"""
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        params = {
            'shop_cipher': shop.shop_cipher,
            'start_date_ge': start_date_str,
            'end_date_lt': end_date_str,
            'page_size': 100,
            'sort_field': 'gmv',
            'sort_order': 'DESC',
            'currency': 'LOCAL',
            'account_type': 'ALL'
        }

        if page_token:
            params['page_token'] = page_token

        data = shop._request("GET", "/analytics/202508/shop_lives/performance", params=params)

        live_sessions = data.get('live_stream_sessions', [])
        next_page_token = data.get('next_page_token')
        latest_available_date = data.get('latest_available_date')

        # Convert latest_available_date từ string sang date object nếu cần
        if latest_available_date and isinstance(latest_available_date, str):
            latest_available_date = datetime.fromisoformat(latest_available_date.replace('Z', '+00:00')).date()

        return live_sessions, next_page_token, latest_available_date

    def _upsert_live_performance(self, shop, live_data):
        """Create or update live performance record"""
        live_id = live_data.get('id')
        if not live_id:
            return

        # Convert timestamps to datetime
        start_time = None
        end_time = None

        if live_data.get('start_time'):
            start_time = shop._convert_unix_to_datetime(int(live_data['start_time']))
        if live_data.get('end_time'):
            end_time = shop._convert_unix_to_datetime(int(live_data['end_time']))

        # Extract sales performance
        sales_perf = live_data.get('sales_performance', {})
        gmv = sales_perf.get('gmv', {})
        avg_price = sales_perf.get('avg_price', {})
        live_gmv_24h = sales_perf.get('24h_live_gmv', {})

        # Extract interaction performance
        interaction_perf = live_data.get('interaction_performance', {})

        # Prepare values
        values = {
            'live_id': live_id,
            'shop_id': shop.id,
            'title': live_data.get('title'),
            'username': live_data.get('username'),
            'start_time': start_time,
            'end_time': end_time,

            # Sales Performance
            'gmv_amount': shop._parse_number(gmv.get('amount', 0)),
            'gmv_currency': gmv.get('currency', 'USD'),
            'products_added': sales_perf.get('products_added', 0),
            'different_products_sold': sales_perf.get('different_products_sold', 0),
            'created_sku_orders': sales_perf.get('created_sku_orders', 0),
            'sku_orders': sales_perf.get('sku_orders', 0),
            'unit_sold': sales_perf.get('unit_sold', 0),
            'customers': sales_perf.get('customers', 0),
            'avg_price_amount': shop._parse_number(avg_price.get('amount', 0)),
            'avg_price_currency': avg_price.get('currency', 'USD'),
            'click_to_order_rate': shop._parse_number(sales_perf.get('click_to_order_rate', 0)),
            'live_gmv_24h_amount': shop._parse_number(live_gmv_24h.get('amount', 0)),
            'live_gmv_24h_currency': live_gmv_24h.get('currency', 'USD'),

            # Interaction Performance
            'acu': interaction_perf.get('acu', 0),
            'pcu': interaction_perf.get('pcu', 0),
            'viewers': interaction_perf.get('viewers', 0),
            'views': interaction_perf.get('views', 0),
            'avg_viewing_duration': shop._parse_number(interaction_perf.get('avg_viewing_duration', 0)),
            'comments': interaction_perf.get('comments', 0),
            'shares': interaction_perf.get('shares', 0),
            'likes': interaction_perf.get('likes', 0),
            'new_followers': interaction_perf.get('new_followers', 0),
            'product_impressions': interaction_perf.get('product_impressions', 0),
            'product_clicks': interaction_perf.get('product_clicks', 0),
            'click_through_rate': shop._parse_number(interaction_perf.get('click_through_rate', 0)),
        }

        # Upsert record
        shop._upsert('tiktok.live.performance', [('live_id', '=', live_id), ('shop_id', '=', shop.id)], values)


class TiktokShop(models.Model):
    _inherit = "tiktok.shop"

    def action_sync_live_performance(self):
        """
        Đồng bộ Live Performance từ TikTok Shop API.
        - Single shop: chạy trực tiếp
        - Multiple shops: chạy đa luồng
        """
        if len(self) == 1:
            # Single shop - chạy trực tiếp
            return self.env["tiktok.live.performance"]._sync_live_performance(self)
        else:
            # Multiple shops - chạy đa luồng
            return self._run_multi_thread_tasks(
                self,
                "Sync Live Performance",
                self.env["tiktok.live.performance"]._sync_live_performance,
                max_workers=min(len(self), MAX_CONCURRENT_THREADS)
            )

