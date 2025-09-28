import logging
from datetime import timedelta, datetime
from odoo import api, fields, models, _
from .tiktok_shop import MAX_CONCURRENT_THREADS

_logger = logging.getLogger(__name__)


class TiktokSkuPerformance(models.Model):
    _name = "tiktok.sku.performance"
    _description = "TikTok SKU Performance Analytics"
    _order = "report_date desc, tiktok_sku_id"
    _rec_name = "display_name"

    # ===== Basic Information =====
    tiktok_sku_id = fields.Char(string="TikTok SKU ID", required=True, index=True)
    sku_id = fields.Many2one('tiktok.sku', string="SKU", index=True)
    product_id = fields.Many2one('tiktok.product', string="Product", related='sku_id.product_id', store=True, index=True)
    shop_id = fields.Many2one('tiktok.shop', string="Shop", required=True, index=True)
    report_date = fields.Date(string="Report Date", required=True, index=True)

    # ===== Overall Performance Metrics =====
    gmv_amount = fields.Float(string="GMV Amount", digits=(16, 2))
    gmv_currency = fields.Char(string="GMV Currency", size=3)
    units_sold = fields.Integer(string="Units Sold")
    sku_orders = fields.Integer(string="SKU Orders")

    # ===== GMV Breakdown =====
    gmv_live = fields.Float(string="GMV Live", digits=(16, 2))
    gmv_video = fields.Float(string="GMV Video", digits=(16, 2))
    gmv_product_card = fields.Float(string="GMV Product Card", digits=(16, 2))

    # ===== Units Sold Breakdown =====
    units_sold_live = fields.Integer(string="Units Sold Live")
    units_sold_video = fields.Integer(string="Units Sold Video")
    units_sold_product_card = fields.Integer(string="Units Sold Product Card")

    # ===== Raw Data =====
    raw_payload = fields.Json(string="Raw Payload")

    _sql_constraints = [
        ('unique_sku_shop_date', 'unique(tiktok_sku_id, shop_id, report_date)',
         'SKU performance record must be unique per shop and date!'),
    ]

    @api.depends('tiktok_sku_id', 'sku_id.display_name', 'report_date')
    def _compute_display_name(self):
        for record in self:
            if record.sku_id:
                record.display_name = f"{record.sku_id.display_name} - {record.report_date}"
            else:
                record.display_name = f"SKU {record.tiktok_sku_id} - {record.report_date}"

    def _parse_breakdowns(self, shop, breakdowns):
        """Parse breakdown data và trả về dict với các loại"""
        result = {
            'live': 0,
            'video': 0,
            'product_card': 0
        }

        for breakdown in breakdowns:
            breakdown_type_value = breakdown.get('type', '').lower()
            amount = shop._parse_number(breakdown.get('amount', 0))

            if breakdown_type_value in result:
                result[breakdown_type_value] = int(amount)

        return result

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

        # 1. Lấy report_date gần nhất từ tiktok.sku.performance
        last_report_date = self.env['tiktok.sku.performance'].search([
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
    def _sync_sku_performance(self, shop, start_date=None, end_date=None):
        """
        Sync SKU performance theo batch (7 ngày một lần) để tối ưu tốc độ.
        """
        shop.ensure_one()
        sync_from_cron = self.env.context.get('sync_from_cron', False)

        # Nếu không truyền start_date và end_date thì lấy smart date range
        if not start_date or not end_date:
            start_date, end_date = self._get_smart_report_date_range(shop)

        if not start_date or not end_date:
            _logger.warning(f"Shop {shop.name}: No new SKU performance data found, stopping sync")
            return {
                'total_synced': 0,
                'has_more_dates': False,
            }

        _logger.info(f"Shop {shop.name}: Starting batch SKU performance sync from {start_date} to {end_date}")

        page_token = None
        page_number = 1
        total_synced = 0

        while True:
            # Lấy 1 page SKUs từ SKU List API với date range
            skus_data, next_page_token, latest_available_date = self._get_sku_performance_list_page(
                shop, start_date, end_date, page_token
            )

            if not skus_data:
                _logger.info(f"Shop {shop.name}: No SKUs with performance data found on page {page_number}")
                
                # Kiểm tra logic thông minh để không bỏ lỡ dữ liệu
                if page_number == 1 and latest_available_date and end_date <= latest_available_date:
                    # Có latest_available_date và end_date chưa đến latest_available_date
                    # Tiếp tục lấy dữ liệu 7 ngày tiếp theo
                    start_date = min(end_date + timedelta(days=1), latest_available_date)  # Bắt đầu từ ngày sau end_date
                    end_date = min(start_date + timedelta(days=7), latest_available_date + timedelta(days=1))
                    _logger.info(f"Shop {shop.name}: Moving SKU performance date range to {start_date.strftime('%Y-%m-%d')} --> {end_date.strftime('%Y-%m-%d')}")
                    continue
                else:
                    # Không có latest_available_date hoặc đã đến latest_available_date
                    _logger.info(f"Shop {shop.name}: No more SKU performance data available, stopping sync")
                    break

            _logger.info(f"Shop {shop.name}: Processing page {page_number}, got {len(skus_data)} SKU performances")

            # Xử lý ngay page này với date range
            page_synced = 0
            for sku_data in skus_data:
                self._get_sku_performance_detail(shop, sku_data['id'], start_date, end_date)
                page_synced += 1
                total_synced += 1

            # Check pagination
            page_token = next_page_token
            if not page_token:
                break

            page_number += 1

        if total_synced == 0:
            _logger.warning(f"Shop {shop.name}: No SKU performance data found, stopping sync")
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
                        'message': _('No SKU performance data found!'),
                        'type': 'warning',
                    }
                }

        _logger.info(f"Shop {shop.name}: Successfully synced {total_synced} SKU performances across {page_number} pages")

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
                    'message': _('Synced %d SKU performances successfully!') % total_synced,
                    'type': 'success',
                }
            }

    def _get_sku_performance_list_page(self, shop, start_date, end_date, page_token=None):
        """Gọi API Get SKU Performance List cho 1 page với date range"""
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

        data = shop._request("GET", "/analytics/202406/shop_skus/performance", params=params)

        skus = data.get('skus', [])
        next_page_token = data.get('next_page_token')
        latest_available_date = data.get('latest_available_date')
        
        # Convert latest_available_date từ string sang date object nếu cần
        if latest_available_date and isinstance(latest_available_date, str):
            latest_available_date = datetime.fromisoformat(latest_available_date.replace('Z', '+00:00')).date()

        return skus, next_page_token, latest_available_date

    def _get_sku_performance_detail(self, shop, sku_id, start_date, end_date):
        """Gọi API Get SKU Performance Detail với date range"""
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
            data = shop._request("GET", f"/analytics/202406/shop_skus/{sku_id}/performance", params=params)
        except Exception as e:
            _logger.error(f"Shop {shop.name}: Error getting performance for SKU {sku_id}: {e}")
            return

        # Parse và lưu vào model với date range
        self._parse_and_save_sku_performance(shop, sku_id, data)

    def _parse_and_save_sku_performance(self, shop, sku_id, data):
        """Parse và lưu SKU performance data với date range"""
        performance_data = data.get('performance', {})
        intervals = performance_data.get('intervals', [])

        # Tìm product trong hệ thống (không bắt buộc)
        product = self.env['tiktok.product'].search([
            ('shop_id', '=', shop.id),
            ('tiktok_id', '=', performance_data.get('product_id'))
        ], limit=1)

        for interval in intervals:
            report_date = fields.Date.from_string(interval.get('start_date'))

            # Parse GMV
            gmv_data = interval.get('gmv', {})
            gmv_amount = shop._parse_number(gmv_data.get('amount', 0))
            gmv_currency = gmv_data.get('currency', 'USD')

            # Parse GMV breakdowns
            gmv_breakdowns = self._parse_breakdowns(
                shop,
                interval.get('gmv_breakdown', [])
            )

            # Parse units sold breakdowns
            units_sold_breakdowns = self._parse_breakdowns(
                shop,
                interval.get('units_sold_breakdown', [])
            )

            # Tìm SKU trong hệ thống
            sku = self.env['tiktok.sku'].search([
                ('shop_id', '=', shop.id),
                ('tiktok_id', '=', str(sku_id))
            ], limit=1)

            # Tạo values cho upsert
            values = {
                'tiktok_sku_id': str(sku_id),
                'sku_id': sku.id if sku else False,
                'shop_id': shop.id,
                'report_date': report_date,
                'gmv_amount': gmv_amount,
                'gmv_currency': gmv_currency,
                'units_sold': interval.get('units_sold', 0),
                'sku_orders': interval.get('sku_orders', 0),
                'gmv_live': gmv_breakdowns['live'],
                'gmv_video': gmv_breakdowns['video'],
                'gmv_product_card': gmv_breakdowns['product_card'],
                'units_sold_live': units_sold_breakdowns['live'],
                'units_sold_video': units_sold_breakdowns['video'],
                'units_sold_product_card': units_sold_breakdowns['product_card'],
                'raw_payload': interval
            }

            # Upsert record
            domain = [
                ('tiktok_sku_id', '=', str(sku_id)),
                ('shop_id', '=', shop.id),
                ('report_date', '=', report_date)
            ]
            shop._upsert('tiktok.sku.performance', domain, values)


class TiktokShop(models.Model):
    _inherit = "tiktok.shop"

    def action_sync_sku_performance(self):
        """
        Đồng bộ SKU Performance từ TikTok Shop API.
        - Single shop: chạy trực tiếp
        - Multiple shops: chạy đa luồng
        """
        if len(self) == 1:
            # Single shop - chạy trực tiếp
            return self.env["tiktok.sku.performance"]._sync_sku_performance(self)
        else:
            # Multiple shops - chạy đa luồng
            return self._run_multi_thread_tasks(
                self,
                "Sync SKU Performance",
                self.env["tiktok.sku.performance"]._sync_sku_performance,
                max_workers=min(len(self), MAX_CONCURRENT_THREADS)
            )
