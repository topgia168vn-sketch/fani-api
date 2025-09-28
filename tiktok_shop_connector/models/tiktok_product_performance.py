import logging
from datetime import timedelta, datetime
from odoo import api, models, fields, _
from .tiktok_shop import MAX_CONCURRENT_THREADS

_logger = logging.getLogger(__name__)


class TiktokProductPerformance(models.Model):
    _name = "tiktok.product.performance"
    _description = "TikTok Product Performance Analytics"
    _order = "report_date desc, gmv_amount desc"

    # ===== Basic Information =====
    product_id = fields.Many2one("tiktok.product", string="Product", index=True)
    tiktok_product_id = fields.Char(string="TikTok Product ID", required=True, index=True)
    shop_id = fields.Many2one("tiktok.shop", string="Shop", required=True, index=True)

    # ===== Report Period =====
    report_date = fields.Date(string="Report Date", required=True, index=True)
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    # ===== Performance Metrics =====
    gmv_amount = fields.Float(string="GMV Amount", digits="Product Price")
    gmv_currency = fields.Char(string="GMV Currency")
    orders_count = fields.Integer(string="Orders Count")
    units_sold = fields.Integer(string="Units Sold")
    click_through_rate = fields.Float(string="Click Through Rate", digits=(5, 4))

    # ===== Breakdown Metrics - Live =====
    live_gmv = fields.Float(string="Live GMV", digits="Product Price")
    live_orders = fields.Integer(string="Live Orders")
    live_units_sold = fields.Integer(string="Live Units Sold")
    live_impressions = fields.Integer(string="Live Impressions")
    live_page_views = fields.Integer(string="Live Page Views")
    live_click_through_rate = fields.Float(string="Live CTR", digits=(5, 4))

    # ===== Breakdown Metrics - Video =====
    video_gmv = fields.Float(string="Video GMV", digits="Product Price")
    video_orders = fields.Integer(string="Video Orders")
    video_units_sold = fields.Integer(string="Video Units Sold")
    video_impressions = fields.Integer(string="Video Impressions")
    video_page_views = fields.Integer(string="Video Page Views")
    video_click_through_rate = fields.Float(string="Video CTR", digits=(5, 4))

    # ===== Breakdown Metrics - Product Card =====
    product_card_gmv = fields.Float(string="Product Card GMV", digits="Product Price")
    product_card_orders = fields.Integer(string="Product Card Orders")
    product_card_units_sold = fields.Integer(string="Product Card Units Sold")
    product_card_impressions = fields.Integer(string="Product Card Impressions")
    product_card_page_views = fields.Integer(string="Product Card Page Views")
    product_card_click_through_rate = fields.Float(string="Product Card CTR", digits=(5, 4))

    # ===== Additional Metrics =====
    total_impressions = fields.Integer(string="Total Impressions")
    total_page_views = fields.Integer(string="Total Page Views")
    avg_page_visitors = fields.Integer(string="Average Page Visitors")

    # ===== Raw Data =====
    raw_payload = fields.Json(string="Raw Payload")

    # ===== Constraints =====
    _sql_constraints = [
        ('unique_product_date', 'unique(tiktok_product_id, shop_id, report_date)',
         'Product performance must be unique per shop and date!'),
    ]

    @api.depends('product_id', 'report_date')
    def _compute_display_name(self):
        for record in self:
            if record.product_id and record.report_date:
                record.display_name = f"{record.product_id.title} - {record.report_date}"
            else:
                record.display_name = f"Product {record.tiktok_product_id} - {record.report_date}"

    @api.model
    def _parse_breakdowns(self, shop, interval):
        """Parse breakdown data theo type (LIVE, VIDEO, PRODUCT_CARD)."""
        breakdowns = {}

        # Mapping các breakdown types và field names
        breakdown_configs = [
            {
                'key': 'gmv_breakdowns',
                'suffix': '_gmv',
            },
            {
                'key': 'unit_sold_breakdowns',
                'suffix': '_units_sold',
            },
            {
                'key': 'impression_breakdowns',
                'suffix': '_impressions',
            },
            {
                'key': 'page_view_breakdowns',
                'suffix': '_page_views',
            },
            {
                'key': 'click_through_rate_breakdowns',
                'suffix': '_click_through_rate',
            }
        ]

        # Parse tất cả breakdown types
        for config in breakdown_configs:
            breakdown_data = interval.get(config['key'], [])
            for breakdown in breakdown_data:
                type_key = breakdown.get('type', '').lower()
                amount = breakdown.get('amount', 0)

                if type_key in ['live', 'video', 'product_card']:
                    field_name = f"{type_key}{config['suffix']}"
                    breakdowns[field_name] = shop._parse_number(amount)

        return breakdowns

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

        # 1. Lấy report_date gần nhất từ tiktok.product.performance
        last_report_date = self.env['tiktok.product.performance'].search([
            ('shop_id', '=', shop.id)
        ], order='report_date desc', limit=1).report_date
        if last_report_date:
            start_date = min(last_report_date + timedelta(days=1), (last_call or today))
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
    def _sync_product_performance(self, shop, start_date=None, end_date=None):
        """
        Sync product performance theo batch (7 ngày một lần) để tối ưu tốc độ.
        """
        shop.ensure_one()
        sync_from_cron = self.env.context.get('sync_from_cron', False)

        # Nếu không truyền start_date và end_date thì lấy smart date range
        if not start_date or not end_date:
            start_date, end_date = self._get_smart_report_date_range(shop)

        if not start_date or not end_date:
            _logger.warning(f"Shop {shop.name}: No new product performance data found, stopping sync")
            return {
                'total_synced': 0,
                'has_more_dates': False,
            }

        _logger.info(f"Shop {shop.name}: Starting batch product performance sync from {start_date} to {end_date}")

        page_token = None
        page_number = 1
        total_synced = 0

        while True:
            # Lấy 1 page products từ Product List API với date range
            products_data, next_page_token, latest_available_date = self._get_product_performance_list_page(
                shop, start_date, end_date, page_token
            )

            if not products_data:
                _logger.info(f"Shop {shop.name}: No products with performance data found on page {page_number}")
                
                # Kiểm tra logic thông minh để không bỏ lỡ dữ liệu
                if page_number == 1 and latest_available_date and end_date <= latest_available_date:
                    # Có latest_available_date và end_date chưa đến latest_available_date
                    # Tiếp tục lấy dữ liệu 7 ngày tiếp theo
                    start_date = min(end_date + timedelta(days=1), latest_available_date)  # Bắt đầu từ ngày sau end_date
                    end_date = min(start_date + timedelta(days=7), latest_available_date + timedelta(days=1))
                    _logger.info(f"Shop {shop.name}: Moving product performance date range to {start_date.strftime('%Y-%m-%d')} --> {end_date.strftime('%Y-%m-%d')}")
                    continue
                else:
                    # Không có latest_available_date hoặc đã đến latest_available_date
                    _logger.info(f"Shop {shop.name}: No more product performance data available, stopping sync")
                    break

            _logger.info(f"Shop {shop.name}: Processing page {page_number}, got {len(products_data)} product performances")

            # Xử lý ngay page này với date range
            page_synced = 0
            for product_data in products_data:
                self._get_product_performance_detail(shop, product_data['id'], start_date, end_date)
                page_synced += 1
                total_synced += 1

            # Check pagination
            page_token = next_page_token
            if not page_token:
                break

            page_number += 1

        if total_synced == 0:
            _logger.warning(f"Shop {shop.name}: No product performance data found, stopping sync")
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
                        'message': _('No product performance data found!'),
                        'type': 'warning',
                    }
                }

        _logger.info(f"Shop {shop.name}: Successfully synced {total_synced} product performances across {page_number} pages")

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
                    'message': _('Synced %d product performance records successfully!') % total_synced,
                    'type': 'success',
                }
            }

    def _get_product_performance_list_page(self, shop, start_date, end_date, page_token=None):
        """Gọi API Get Product Performance List cho 1 page với date range"""
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        params = {
            'shop_cipher': shop.shop_cipher,
            'start_date_ge': start_date_str,
            'end_date_lt': end_date_str,
            'page_size': 100,
            'sort_field': 'gmv',
            'sort_order': 'DESC',
            'currency': 'LOCAL'
        }

        if page_token:
            params['page_token'] = page_token

        data = shop._request("GET", "/analytics/202405/shop_products/performance", params=params)

        products = data.get('products', [])
        next_page_token = data.get('next_page_token')
        latest_available_date = data.get('latest_available_date')
        
        # Convert latest_available_date từ string sang date object nếu cần
        if latest_available_date and isinstance(latest_available_date, str):
            latest_available_date = datetime.fromisoformat(latest_available_date.replace('Z', '+00:00')).date()

        return products, next_page_token, latest_available_date

    def _get_product_performance_detail(self, shop, product_id, start_date, end_date):
        """Gọi API Get Product Performance Detail với date range"""
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        params = {
            'shop_cipher': shop.shop_cipher,
            'start_date_ge': start_date_str,
            'end_date_lt': end_date_str,
            'granularity': '1D',
            'currency': 'LOCAL'
        }

        try:
            data = shop._request("GET", f"/analytics/202405/shop_products/{product_id}/performance", params=params)
        except Exception as e:
            _logger.error(f"Shop {shop.name}: Error getting performance for product {product_id}: {e}")
            return

        # Parse và lưu vào model với date range
        self._parse_and_save_product_performance(shop, product_id, data)

    def _parse_and_save_product_performance(self, shop, product_id, data):
        """Parse và lưu product performance data với date range"""
        performance_data = data.get('performance', {})
        intervals = performance_data.get('intervals', [])

        # Tìm product trong hệ thống (không bắt buộc)
        product = self.env['tiktok.product'].search([
            ('tiktok_id', '=', str(product_id)),
            ('shop_id', '=', shop.id)
        ], limit=1)

        for interval in intervals:
            # Parse breakdown data
            breakdowns = self._parse_breakdowns(shop, interval)

            # Prepare values
            values = {
                'product_id': product.id if product else False,
                'tiktok_product_id': str(product_id),
                'shop_id': shop.id,
                'report_date': interval.get('start_date'),  # Sử dụng start_date từ interval
                'start_date': interval.get('start_date'),
                'end_date': interval.get('end_date'),
                'gmv_amount': shop._parse_number(interval.get('gmv', {}).get('amount', 0)),
                'gmv_currency': interval.get('gmv', {}).get('currency'),
                'orders_count': interval.get('orders', 0),
                'units_sold': interval.get('units_sold', 0),
                'click_through_rate': shop._parse_number(interval.get('click_through_rate', 0)),
                'total_impressions': interval.get('impressions', 0),
                'total_page_views': interval.get('page_views', 0),
                'avg_page_visitors': interval.get('avg_page_visitors', 0),
                'raw_payload': interval,
                **breakdowns
            }

            # Upsert performance record using shop's _upsert method
            domain = [
                ('tiktok_product_id', '=', values['tiktok_product_id']),
                ('shop_id', '=', values['shop_id']),
                ('report_date', '=', values['report_date'])
            ]
            shop._upsert('tiktok.product.performance', domain, values)


class TiktokShop(models.Model):
    _inherit = "tiktok.shop"

    def action_sync_product_performance(self):
        """
        Đồng bộ Product Performance từ TikTok Shop API.
        - Single shop: chạy trực tiếp
        - Multiple shops: chạy đa luồng
        """
        if len(self) == 1:
            # Single shop - chạy trực tiếp
            return self.env["tiktok.product.performance"]._sync_product_performance(self)
        else:
            # Multiple shops - chạy đa luồng
            return self._run_multi_thread_tasks(
                self,
                "Sync Product Performance",
                self.env["tiktok.product.performance"]._sync_product_performance,
                max_workers=min(len(self), MAX_CONCURRENT_THREADS)
            )
