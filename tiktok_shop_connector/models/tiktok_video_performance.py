import logging
from datetime import timedelta, datetime
from odoo import api, models, fields, _
from .tiktok_shop import MAX_CONCURRENT_THREADS

_logger = logging.getLogger(__name__)


class TiktokVideoPerformance(models.Model):
    _name = "tiktok.video.performance"
    _description = "TikTok Video Performance Analytics"
    _order = "report_date desc, gmv_amount desc"

    # ===== Basic Information =====
    video_id = fields.Char(string="Video ID", required=True, index=True)
    shop_id = fields.Many2one("tiktok.shop", string="Shop", required=True, index=True)

    # ===== Report Period =====
    report_date = fields.Date(string="Report Date", required=True, index=True)
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    # ===== Performance Metrics =====
    gmv_amount = fields.Float(string="GMV Amount", digits="Product Price")
    gmv_currency = fields.Char(string="GMV Currency")
    click_through_rate = fields.Float(string="Click Through Rate", digits=(5, 4))
    daily_avg_buyers = fields.Float(string="Daily Average Buyers", digits=(5, 2))
    views = fields.Integer(string="Views")

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

    # ===== Video-specific Fields =====
    video_post_time = fields.Datetime(string="Video Post Time")
    engagement_data = fields.Json(string="Engagement Data")
    latest_available_date = fields.Datetime(string="Latest Available Date")

    # ===== Raw Data =====
    raw_payload = fields.Json(string="Raw Payload")

    # ===== Constraints =====
    _sql_constraints = [
        ('unique_video_date', 'unique(video_id, shop_id, report_date)',
         'Video performance must be unique per shop and date!'),
    ]

    @api.depends('video_id', 'report_date')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"Video {record.video_id} - {record.report_date}"

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

        # 1. Lấy report_date gần nhất từ tiktok.video.performance
        last_report_date = self.env['tiktok.video.performance'].search([
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
    def _sync_video_performance(self, shop, start_date=None, end_date=None):
        """
        Sync video performance theo batch (7 ngày một lần) để tối ưu tốc độ.
        """
        shop.ensure_one()
        sync_from_cron = self.env.context.get('sync_from_cron', False)

        # Nếu không truyền start_date và end_date thì lấy smart date range
        if not start_date or not end_date:
            start_date, end_date = self._get_smart_report_date_range(shop)

        if not start_date or not end_date:
            _logger.warning(f"Shop {shop.name}: No new video performance data found, stopping sync")
            return {
                'total_synced': 0,
                'has_more_dates': False,
            }

        _logger.info(f"Shop {shop.name}: Starting batch video performance sync from {start_date} to {end_date}")

        page_token = None
        page_number = 1
        total_synced = 0

        while True:
            # Lấy 1 page videos từ Video List API với date range
            videos_data, next_page_token, latest_available_date = self._get_video_performance_list_page(
                shop, start_date, end_date, page_token
            )

            if not videos_data:
                _logger.info(f"Shop {shop.name}: No videos with performance data found on page {page_number}")

                # Kiểm tra logic thông minh để không bỏ lỡ dữ liệu
                if page_number == 1 and latest_available_date and end_date <= latest_available_date:
                    # Có latest_available_date và end_date chưa đến latest_available_date
                    # Tiếp tục lấy dữ liệu 7 ngày tiếp theo
                    start_date = min(end_date + timedelta(days=1), latest_available_date)  # Bắt đầu từ ngày sau end_date
                    end_date = min(start_date + timedelta(days=7), latest_available_date + timedelta(days=1))
                    _logger.info(f"Shop {shop.name}: Moving video performance date range to {start_date.strftime('%Y-%m-%d')} --> {end_date.strftime('%Y-%m-%d')}")
                    continue
                else:
                    # Không có latest_available_date hoặc đã đến latest_available_date
                    _logger.info(f"Shop {shop.name}: No more video performance data available, stopping sync")
                    break

            _logger.info(f"Shop {shop.name}: Processing page {page_number}, got {len(videos_data)} video performances")

            # Xử lý ngay page này với date range
            page_synced = 0
            for video_data in videos_data:
                self._get_video_performance_detail(shop, video_data['id'], start_date, end_date)
                page_synced += 1
                total_synced += 1

            # Check pagination
            page_token = next_page_token
            if not page_token:
                break

            page_number += 1

        if total_synced == 0:
            _logger.warning(f"Shop {shop.name}: No video performance data found, stopping sync")
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
                        'message': _('No video performance data found!'),
                        'type': 'warning',
                    }
                }

        _logger.info(f"Shop {shop.name}: Successfully synced {total_synced} video performances across {page_number} pages")

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
                    'message': _('Synced %d video performances successfully!') % total_synced,
                    'type': 'success',
                }
            }

    def _get_video_performance_list_page(self, shop, start_date, end_date, page_token=None):
        """Gọi API Get Video Performance List cho 1 page với date range"""
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

        data = shop._request("GET", "/analytics/202409/shop_videos/performance", params=params)

        videos = data.get('videos', [])
        next_page_token = data.get('next_page_token')
        latest_available_date = data.get('latest_available_date')

        # Convert latest_available_date từ string sang date object nếu cần
        if latest_available_date and isinstance(latest_available_date, str):
            latest_available_date = datetime.fromisoformat(latest_available_date.replace('Z', '+00:00')).date()

        return videos, next_page_token, latest_available_date

    def _get_video_performance_detail(self, shop, video_id, start_date, end_date):
        """Gọi API Get Video Performance Detail với date range"""
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        params = {
            'shop_cipher': shop.shop_cipher,
            'start_date_ge': start_date_str,
            'end_date_lt': end_date_str,
            'granularity': '1D',
            'currency': 'LOCAL',
            'with_comparison': False
        }

        try:
            data = shop._request("GET", f"/analytics/202409/shop_videos/{video_id}/performance", params=params)
        except Exception as e:
            _logger.error(f"Shop {shop.name}: Error getting performance for video {video_id}: {e}")
            return

        # Parse và lưu vào model với date range
        self._parse_and_save_video_performance(shop, video_id, data)

    def _parse_and_save_video_performance(self, shop, video_id, data):
        """Parse và lưu video performance data với date range"""
        performance_data = data.get('performance', {})
        intervals = performance_data.get('intervals', [])

        # Video-specific root data
        video_post_time = performance_data.get('video_post_time')
        engagement_data = performance_data.get('engagement_data', {})
        latest_available_date = performance_data.get('latest_available_date')

        for interval in intervals:
            # Parse breakdown data
            breakdowns = self._parse_breakdowns(shop, interval)

            # Prepare values
            values = {
                'video_id': str(video_id),
                'shop_id': shop.id,
                'report_date': interval.get('start_date'),
                'start_date': interval.get('start_date'),
                'end_date': interval.get('end_date'),

                # Performance metrics
                'gmv_amount': shop._parse_number(interval.get('gmv', {}).get('amount', 0)),
                'gmv_currency': interval.get('gmv', {}).get('currency'),
                'click_through_rate': shop._parse_number(interval.get('click_through_rate', 0)),
                'daily_avg_buyers': shop._parse_number(interval.get('daily_avg_buyers', 0)),
                'views': interval.get('views', 0),

                # Video-specific fields
                'video_post_time': shop._convert_unix_to_datetime(video_post_time) if video_post_time else False,
                'engagement_data': engagement_data,
                'latest_available_date': shop._convert_unix_to_datetime(latest_available_date) if latest_available_date else False,

                # Breakdown metrics
                **breakdowns,
                'raw_payload': interval
            }

            # Upsert performance record using shop's _upsert method
            domain = [
                ('video_id', '=', str(video_id)),
                ('shop_id', '=', shop.id),
                ('report_date', '=', values['report_date'])
            ]
            shop._upsert('tiktok.video.performance', domain, values)


class TiktokShop(models.Model):
    _inherit = "tiktok.shop"

    def action_sync_video_performance(self):
        """
        Đồng bộ Video Performance từ TikTok Shop API.
        - Single shop: chạy trực tiếp
        - Multiple shops: chạy đa luồng
        """
        if len(self) == 1:
            # Single shop - chạy trực tiếp
            return self.env["tiktok.video.performance"]._sync_video_performance(self)
        else:
            # Multiple shops - chạy đa luồng
            return self._run_multi_thread_tasks(
                self,
                "Sync Video Performance",
                self.env["tiktok.video.performance"]._sync_video_performance,
                max_workers=min(len(self), MAX_CONCURRENT_THREADS)
            )
