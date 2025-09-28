# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ShopeeVideoProductReport(models.Model):
    _name = 'shopee.video.product.report'
    _description = 'Shopee Video Product Report'
    _inherit = 'shopee.report.mixin'
    _order = 'report_date desc, id desc'

    # ==================== BASIC INFO ====================
    shop_id = fields.Many2one(
        'shopee.shop',
        string='Shop',
        required=True,
        index=True,
        ondelete='cascade',
    )

    report_date = fields.Date(
        string='Report Date',
        required=True,
        index=True,
        help='Ngày báo cáo'
    )

    # ==================== STREAMER INFO ====================
    streamer_id = fields.Char(
        string='Streamer ID',
        index=True,
        help='ID của streamer'
    )

    # ==================== PRODUCT INFO ====================
    product_name = fields.Char(
        string='Product Name',
        index=True,
        help='Tên sản phẩm'
    )

    ranking = fields.Integer(
        string='Ranking',
        help='Xếp hạng sản phẩm'
    )

    # ==================== ORDERS INFO ====================
    orders_placed = fields.Integer(
        string='Orders Placed',
        help='Đơn hàng (Đơn đã đặt)'
    )

    orders_confirmed = fields.Integer(
        string='Orders Confirmed',
        help='Đơn hàng (Đơn hàng được xác nhận)'
    )

    # ==================== REVENUE INFO ====================
    revenue_placed = fields.Float(
        string='Revenue Placed',
        digits=(16, 2),
        help='Doanh số (Đơn đã đặt)'
    )

    revenue_confirmed = fields.Float(
        string='Revenue Confirmed',
        digits=(16, 2),
        help='Doanh số (Đơn hàng được xác nhận)'
    )

    # ==================== BUYERS INFO ====================
    buyers_placed = fields.Integer(
        string='Buyers Placed',
        help='Người mua (Đơn đã đặt)'
    )

    buyers_confirmed = fields.Integer(
        string='Buyers Confirmed',
        help='Người mua (Đơn hàng được xác nhận)'
    )

    # ==================== HELPER METHODS ====================
    @api.model
    def _import_row(self, shop_id, report_date, row_data):
        """Create Video Product report record from CSV row data"""
        vals = {
            'shop_id': shop_id,
            'report_date': self._parse_date(row_data.get('Khung Thời Gian', ''), '%d-%m-%Y'),
            'streamer_id': row_data.get('Streamer ID', ''),
            'product_name': row_data.get('Các sản phẩm', ''),
            'ranking': int(self._parse_float(row_data.get('Xếp hạng', '0'))),
            'orders_placed': int(self._parse_float(row_data.get('Đơn hàng(Đơn đã đặt)', '0'))),
            'orders_confirmed': int(self._parse_float(row_data.get('Đơn hàng(Đơn hàng được xác nhận)', '0'))),
            'revenue_placed': self._parse_float(row_data.get('Doanh số(Đơn đã đặt)', '0')),
            'revenue_confirmed': self._parse_float(row_data.get('Doanh số(Đơn hàng được xác nhận)', '0')),
            'buyers_placed': int(self._parse_float(row_data.get('Người mua(Đơn đã đặt)', '0'))),
            'buyers_confirmed': int(self._parse_float(row_data.get('Người mua(Đơn hàng được xác nhận)', '0'))),
        }
        return self._upsert(
            [
                ('shop_id', '=', shop_id),
                ('report_date', '=', report_date),
                ('streamer_id', '=', vals['streamer_id']),
                ('product_name', '=', vals['product_name']),
            ],
            vals
        )
