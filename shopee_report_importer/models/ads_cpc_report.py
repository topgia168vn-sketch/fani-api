# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ShopeeAdsCpcReport(models.Model):
    _name = 'shopee.ads.cpc.report'
    _description = 'Shopee Ads CPC Report'
    _inherit = 'shopee.report.mixin'
    _order = 'report_date desc, id desc'

    # ==================== HEADER INFO ====================
    shop_id = fields.Many2one(
        'shopee.shop',
        string='Shop',
        required=True,
        index=True,
        ondelete='cascade'
    )

    # Report metadata
    report_date = fields.Date(
        string='Report Date',
        required=True,
        index=True,
        help='Ngày báo cáo'
    )

    # ==================== CAMPAIGN INFO ====================
    campaign_name = fields.Char(
        string='Campaign Name',
        index=True,
        help='Tên Dịch vụ Hiển thị'
    )

    status = fields.Char(
        string='Status',
        help='Trạng thái'
    )

    campaign_type = fields.Char(
        string='Campaign Type',
        help='Loại Dịch vụ Hiển thị'
    )

    product_id = fields.Char(
        string='Product ID',
        help='Mã sản phẩm'
    )

    target_setting = fields.Char(
        string='Target Setting',
        help='Cài đặt Đối tượng'
    )

    campaign_content = fields.Char(
        string='Campaign Content',
        help='Nội dung Dịch vụ Hiển thị'
    )

    bidding_method = fields.Char(
        string='Bidding Method',
        help='Phương thức đấu thầu'
    )

    position = fields.Char(
        string='Position',
        help='Vị trí'
    )


    # ==================== METRICS ====================
    # Views & Clicks
    views = fields.Integer(
        string='Views',
        help='Số lượt xem'
    )

    clicks = fields.Integer(
        string='Clicks',
        help='Số lượt click'
    )

    click_rate = fields.Float(
        string='Click Rate',
        digits=(5, 2),
        help='Tỷ lệ Click (%)'
    )

    # Conversions
    conversions = fields.Integer(
        string='Conversions',
        help='Lượt chuyển đổi'
    )

    direct_conversions = fields.Integer(
        string='Direct Conversions',
        help='Lượt chuyển đổi trực tiếp'
    )

    conversion_rate = fields.Float(
        string='Conversion Rate',
        digits=(5, 2),
        help='Tỷ lệ chuyển đổi (%)'
    )

    direct_conversion_rate = fields.Float(
        string='Direct Conversion Rate',
        digits=(5, 2),
        help='Tỷ lệ chuyển đổi trực tiếp (%)'
    )

    # Cost per conversion
    cost_per_conversion = fields.Float(
        string='Cost Per Conversion',
        digits=(10, 2),
        help='Chi phí cho mỗi lượt chuyển đổi'
    )

    cost_per_direct_conversion = fields.Float(
        string='Cost Per Direct Conversion',
        digits=(10, 2),
        help='Chi phí cho mỗi lượt chuyển đổi trực tiếp'
    )

    # Sales
    products_sold = fields.Integer(
        string='Products Sold',
        help='Sản phẩm đã bán'
    )

    direct_products_sold = fields.Integer(
        string='Direct Products Sold',
        help='Sản phẩm đã bán trực tiếp'
    )

    # GMV
    gmv = fields.Float(
        string='GMV',
        digits=(15, 2),
        help='GMV'
    )

    direct_gmv = fields.Float(
        string='Direct GMV',
        digits=(15, 2),
        help='GMV trực tiếp'
    )

    # Cost
    cost = fields.Float(
        string='Cost',
        digits=(15, 2),
        help='Chi phí'
    )

    # ROAS
    roas = fields.Float(
        string='ROAS',
        digits=(5, 2),
        help='ROAS'
    )

    direct_roas = fields.Float(
        string='Direct ROAS',
        digits=(5, 2),
        help='ROAS trực tiếp'
    )

    # ACOS
    acos = fields.Float(
        string='ACOS',
        digits=(5, 2),
        help='ACOS (%)'
    )

    direct_acos = fields.Float(
        string='Direct ACOS',
        digits=(5, 2),
        help='ACOS trực tiếp (%)'
    )

    # Product views & clicks
    product_views = fields.Integer(
        string='Product Views',
        help='Lượt xem Sản phẩm'
    )

    product_clicks = fields.Integer(
        string='Product Clicks',
        help='Lượt clicks Sản phẩm'
    )

    product_click_rate = fields.Float(
        string='Product Click Rate',
        digits=(5, 2),
        help='Tỷ lệ Click Sản phẩm (%)'
    )

    # ==================== HELPER METHODS ====================
    @api.model
    def _import_row(self, shop_id, report_date, row_data):
        """Tạo record từ dữ liệu CSV row"""
        # Parse row data (row_data là dict từ CSV)
        vals = {
            'shop_id': shop_id,
            'report_date': report_date,
            'campaign_name': row_data.get('Tên Dịch vụ Hiển thị', ''),
            'status': row_data.get('Trạng thái', ''),
            'campaign_type': row_data.get('Loại Dịch vụ Hiển thị', ''),
            'product_id': row_data.get('Mã sản phẩm', ''),
            'target_setting': row_data.get('Cài đặt Đối tượng', ''),
            'campaign_content': row_data.get('Nội dung Dịch vụ Hiển thị', ''),
            'bidding_method': row_data.get('Phương thức đấu thầu', ''),
            'position': row_data.get('Vị trí', ''),
            'views': int(row_data.get('Số lượt xem', 0)),
            'clicks': int(row_data.get('Số lượt click', 0)),
            'click_rate': self._parse_percentage(row_data.get('Tỷ Lệ Click', '0%')),
            'conversions': int(row_data.get('Lượt chuyển đổi', 0)),
            'direct_conversions': int(row_data.get('Lượt chuyển đổi trực tiếp', 0)),
            'conversion_rate': self._parse_percentage(row_data.get('Tỷ lệ chuyển đổi', '0%')),
            'direct_conversion_rate': self._parse_percentage(row_data.get('Tỷ lệ chuyển đổi trực tiếp', '0%')),
            'cost_per_conversion': float(row_data.get('Chi phí cho mỗi lượt chuyển đổi', 0)),
            'cost_per_direct_conversion': float(row_data.get('Chi phí cho mỗi lượt chuyển đổi trực tiếp', 0)),
            'products_sold': int(row_data.get('Sản phẩm đã bán', 0)),
            'direct_products_sold': int(row_data.get('Sản phẩm đã bán trực tiếp', 0)),
            'gmv': float(row_data.get('GMV', 0)),
            'direct_gmv': float(row_data.get('GMV trực tiếp', 0)),
            'cost': float(row_data.get('Chi phí', 0)),
            'roas': float(row_data.get('ROAS', 0)),
            'direct_roas': float(row_data.get('ROAS trực tiếp', 0)),
            'acos': self._parse_percentage(row_data.get('ACOS', '0%')),
            'direct_acos': self._parse_percentage(row_data.get('ACOS trực tiếp', '0%')),
            'product_views': int(row_data.get('Lượt xem Sản phẩm', 0) or 0),
            'product_clicks': int(row_data.get('Lượt clicks Sản phẩm', 0) or 0),
            'product_click_rate': self._parse_percentage(row_data.get('Tỷ lệ Click Sản phẩm', '0%')),
        }

        return self._upsert(
            [
                ('shop_id', '=', shop_id),
                ('report_date', '=', report_date),
                ('campaign_name', '=', vals['campaign_name'])
            ],
            vals
        )
