# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ShopeeBookingReport(models.Model):
    _name = 'shopee.booking.report'
    _description = 'Shopee Booking Report (Product Performance)'
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

    # ==================== PRODUCT INFO ====================
    product_id = fields.Char(
        string='Product ID',
        required=True,
        index=True,
        help='Mã sản phẩm'
    )

    product_name = fields.Char(
        string='Product Name',
        help='Tên sản phẩm'
    )

    price = fields.Float(
        string='Price',
        digits=(15, 2),
        help='Giá sản phẩm (₫)'
    )

    # ==================== SALES METRICS ====================
    revenue = fields.Float(
        string='Revenue',
        digits=(15, 2),
        help='Doanh thu (₫)'
    )

    products_sold = fields.Integer(
        string='Products Sold',
        help='Sản phẩm đã bán'
    )

    orders = fields.Integer(
        string='Orders',
        help='Số đơn hàng'
    )

    # ==================== COMMISSION METRICS ====================
    estimated_commission = fields.Float(
        string='Estimated Commission',
        digits=(15, 2),
        help='Hoa hồng ước tính (₫)'
    )

    estimated_commission_rate = fields.Float(
        string='Estimated Commission Rate',
        digits=(5, 2),
        help='Hoa hồng ước tính (%)'
    )

    roi = fields.Float(
        string='ROI',
        digits=(5, 2),
        help='ROI (%)'
    )

    # ==================== CUSTOMER METRICS ====================
    total_buyers = fields.Integer(
        string='Total Buyers',
        help='Tất cả người mua'
    )

    new_buyers = fields.Integer(
        string='New Buyers',
        help='Người mua mới'
    )

    # ==================== HELPER METHODS ====================
    @api.model
    def _import_row(self, shop_id, report_date, row_data):
        """Tạo record từ dữ liệu CSV row"""
        # Parse row data (row_data là dict từ CSV)
        vals = {
            'shop_id': shop_id,
            'report_date': report_date,
            'product_id': row_data.get('Mã sản phẩm', ''),
            'product_name': row_data.get('Tên sản phẩm', ''),
            'price': self._parse_float(row_data.get('Giá(₫)', '0')),
            'revenue': self._parse_float(row_data.get('Doanh thu(₫)', '0')),
            'products_sold': int(row_data.get('Sản phẩm đã bán', 0)),
            'orders': int(row_data.get('Số đơn hàng', 0)),
            'estimated_commission': self._parse_float(row_data.get('Hoa hồng ước tính(₫)', '0')),
            'estimated_commission_rate': self._parse_float(row_data.get('Hoa hồng ước tính', '0')),
            'roi': float(row_data.get('ROI', 0)),
            'total_buyers': int(row_data.get('Tất cả người mua', 0)),
            'new_buyers': int(row_data.get('Người mua mới', 0)),
        }

        return self._upsert(
            [
                ('shop_id', '=', shop_id),
                ('report_date', '=', report_date),
                ('product_id', '=', vals['product_id'])
            ],
            vals
        )
