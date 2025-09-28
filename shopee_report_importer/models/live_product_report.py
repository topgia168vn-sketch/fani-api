# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ShopeeLiveProductReport(models.Model):
    _name = 'shopee.live.product.report'
    _description = 'Shopee Live Product Report'
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
        required=True,
        index=True,
        help='ID của streamer'
    )

    ranking = fields.Integer(
        string='Ranking',
        required=True,
        help='Xếp hạng sản phẩm trong livestream'
    )

    # ==================== PRODUCT INFO ====================
    product_name = fields.Char(
        string='Product Name',
        required=True,
        index=True,
        help='Tên sản phẩm'
    )

    # ==================== ENGAGEMENT METRICS ====================
    product_clicks = fields.Integer(
        string='Product Clicks',
        help='Lượt click vào sản phẩm'
    )

    add_to_cart = fields.Integer(
        string='Add to Cart',
        help='Thêm vào Giỏ hàng'
    )

    # ==================== ORDER METRICS ====================
    orders_placed = fields.Integer(
        string='Orders Placed',
        help='Đơn hàng(Đơn đã đặt)'
    )

    orders_confirmed = fields.Integer(
        string='Orders Confirmed',
        help='Đơn hàng(Đơn hàng được xác nhận)'
    )

    products_sold_placed = fields.Integer(
        string='Products Sold (Placed)',
        help='Sản phẩm đã bán(Đơn đã đặt)'
    )

    products_sold_confirmed = fields.Integer(
        string='Products Sold (Confirmed)',
        help='Sản phẩm đã bán(Đơn hàng được xác nhận)'
    )

    # ==================== REVENUE METRICS ====================
    revenue_placed = fields.Float(
        string='Revenue (Placed)',
        digits=(16, 2),
        help='Doanh số(Đơn đã đặt) (VND)'
    )

    revenue_confirmed = fields.Float(
        string='Revenue (Confirmed)',
        digits=(16, 2),
        help='Doanh số(Đơn hàng được xác nhận) (VND)'
    )

    # ==================== HELPER METHODS ====================
    @api.model
    def _import_row(self, shop_id, report_date, row_data):
        """Create Live Product report record from CSV row data"""
        vals = {
            'shop_id': shop_id,
            'report_date': self._parse_date(row_data.get('Khung Thời Gian', ''), '%d-%m-%Y'),
            'streamer_id': row_data.get('Streamer ID', ''),
            'ranking': int(row_data.get('Xếp hạng', 0)),
            'product_name': row_data.get('Các sản phẩm', ''),
            'product_clicks': int(row_data.get('Lượt click vào sản phẩm', 0)),
            'add_to_cart': int(row_data.get('Thêm vào Giỏ hàng', 0)),
            'orders_placed': int(row_data.get('Đơn hàng(Đơn đã đặt)', 0)),
            'orders_confirmed': int(row_data.get('Đơn hàng(Đơn hàng được xác nhận)', 0)),
            'products_sold_placed': int(row_data.get('Sản phẩm đã bán(Đơn đã đặt)', 0)),
            'products_sold_confirmed': int(row_data.get('Sản phẩm đã bán(Đơn hàng được xác nhận)', 0)),
            'revenue_placed': self._parse_float(row_data.get('Doanh số(Đơn đã đặt)', '0')),
            'revenue_confirmed': self._parse_float(row_data.get('Doanh số(Đơn hàng được xác nhận)', '0')),
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
