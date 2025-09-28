# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ShopeeLabanReport(models.Model):
    _name = 'shopee.laban.report'
    _description = 'Shopee Laban Report (Product Overview)'
    _inherit = 'shopee.report.mixin'
    _order = 'report_date desc, hour desc'

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

    hour = fields.Float(
        string='Hour',
        digits=(4, 2),
        required=True,
        index=True,
        help='Giờ trong ngày (0-23)'
    )

    # ==================== TRAFFIC METRICS ====================
    product_visits = fields.Integer(
        string='Product Visits',
        help='Lượt truy cập sản phẩm'
    )

    product_page_views = fields.Integer(
        string='Product Page Views',
        help='Lượt xem trang sản phẩm'
    )

    products_accessed = fields.Integer(
        string='Products Accessed',
        help='Sản phẩm được truy cập'
    )

    # ==================== ENGAGEMENT METRICS ====================
    bounce_count = fields.Integer(
        string='Bounce Count',
        help='Số lượng khách thoát trang sản phẩm'
    )

    bounce_rate = fields.Float(
        string='Bounce Rate (%)',
        digits=(5, 2),
        help='Tỷ lệ thoát Trang sản phẩm (%)'
    )

    search_clicks = fields.Integer(
        string='Search Clicks',
        help='Lượt click từ Trang tìm kiếm'
    )

    likes = fields.Integer(
        string='Likes',
        help='Lượt thích'
    )

    # ==================== CART METRICS ====================
    add_to_cart_visits = fields.Integer(
        string='Add to Cart Visits',
        help='Lượt truy cập sản phẩm (Thêm vào giỏ hàng)'
    )

    products_added_to_cart = fields.Integer(
        string='Products Added to Cart',
        help='Sản phẩm (Thêm vào giỏ hàng)'
    )

    add_to_cart_conversion_rate = fields.Float(
        string='Add to Cart Conversion Rate (%)',
        digits=(5, 2),
        help='Tỷ lệ chuyển đổi (theo lượt thêm vào giỏ hàng) (%)'
    )

    # ==================== ORDER METRICS ====================
    buyers_placed_orders = fields.Integer(
        string='Buyers Placed Orders',
        help='Người mua đã đặt hàng'
    )

    products_in_placed_orders = fields.Integer(
        string='Products in Placed Orders',
        help='Sản phẩm (Đơn đã đặt)'
    )

    products_sold = fields.Integer(
        string='Products Sold',
        help='Số sản phẩm đã bán'
    )

    placed_orders_revenue = fields.Float(
        string='Placed Orders Revenue (VND)',
        digits=(16, 2),
        help='Doanh số (Đơn đã đặt) (VND)'
    )

    order_conversion_rate = fields.Float(
        string='Order Conversion Rate (%)',
        digits=(5, 2),
        help='Tỷ lệ chuyển đổi (Đơn đã đặt) (%)'
    )

    # ==================== CONFIRMED ORDER METRICS ====================
    buyers_confirmed_orders = fields.Integer(
        string='Buyers Confirmed Orders',
        help='Người mua có đơn đã xác nhận'
    )

    products_in_confirmed_orders = fields.Integer(
        string='Products in Confirmed Orders',
        help='Sản phẩm (Đơn đã xác nhận)'
    )

    approved_products = fields.Integer(
        string='Approved Products',
        help='Sản phẩm được duyệt'
    )

    confirmed_orders_revenue = fields.Float(
        string='Confirmed Orders Revenue (VND)',
        digits=(16, 2),
        help='Doanh số (Đơn đã xác nhận) (VND)'
    )

    confirmed_order_conversion_rate = fields.Float(
        string='Confirmed Order Conversion Rate (%)',
        digits=(5, 2),
        help='Tỷ lệ chuyển đổi (Đơn đã xác nhận) (%)'
    )

    # ==================== CONVERSION FUNNEL ====================
    order_to_confirmed_conversion_rate = fields.Float(
        string='Order to Confirmed Conversion Rate (%)',
        digits=(5, 2),
        help='Tỷ lệ chuyển đổi (Từ Đơn đã đặt thành Đơn đã xác nhận) (%)'
    )

    # ==================== HELPER METHODS ====================
    @api.model
    def _import_row(self, shop_id, report_date, row_data):
        """Create Laban report record from CSV row data"""
        # Parse date and hour from "Ngày" field (format: "HH:MM DD-MM-YYYY")
        date_str = row_data.get('Ngày', '')
        parsed_date = self._parse_date(date_str.split(' ')[-1] if ' ' in date_str else date_str, '%d-%m-%Y')
        parsed_hour = date_str.split(' ')[0] if ' ' in date_str else '00:00'

        vals = {
            'shop_id': shop_id,
            'report_date': parsed_date,
            'hour': self._parse_hour_to_float(parsed_hour),
            'product_visits': int(row_data.get('Lượt truy cập sản phẩm', 0)),
            'product_page_views': int(row_data.get('Lượt xem trang sản phẩm', 0)),
            'products_accessed': int(row_data.get('Sản phẩm được truy cập', 0)),
            'bounce_count': int(row_data.get('Số lượng khách thoát trang sản phẩm', 0)),
            'bounce_rate': self._parse_percentage(row_data.get('Tỷ lệ thoát Trang sản phẩm', '0%')),
            'search_clicks': int(row_data.get('Lượt click từ Trang tìm kiếm', 0)),
            'likes': int(row_data.get('Lượt thích', 0)),
            'add_to_cart_visits': int(row_data.get('Lượt truy cập sản phẩm (Thêm vào giỏ hàng)', 0)),
            'products_added_to_cart': int(row_data.get('Sản phẩm (Thêm vào giỏ hàng)', 0)),
            'add_to_cart_conversion_rate': self._parse_percentage(row_data.get('Tỷ lệ chuyển đổi (theo lượt thêm vào giỏ hàng)', '0%')),
            'buyers_placed_orders': int(row_data.get('Người mua đã đặt hàng', 0)),
            'products_in_placed_orders': int(row_data.get('Sản phẩm (Đơn đã đặt)', 0)),
            'products_sold': int(row_data.get('Số sản phẩm đã bán', 0)),
            'placed_orders_revenue': self._parse_float(row_data.get('Doanh số (Đơn đã đặt) (VND)', '0')),
            'order_conversion_rate': self._parse_percentage(row_data.get('Tỷ lệ chuyển đổi (Đơn đã đặt)', '0%')),
            'buyers_confirmed_orders': int(row_data.get('Người mua có đơn đã xác nhận', 0)),
            'products_in_confirmed_orders': int(row_data.get('Sản phẩm (Đơn đã xác nhận)', 0)),
            'approved_products': int(row_data.get('Sản phẩm được duyệt', 0)),
            'confirmed_orders_revenue': self._parse_float(row_data.get('Doanh số (Đơn đã xác nhận) (VND)', '0')),
            'confirmed_order_conversion_rate': self._parse_percentage(row_data.get('Tỷ lệ chuyển đổi (Đơn đã xác nhận)', '0%')),
            'order_to_confirmed_conversion_rate': self._parse_percentage(row_data.get('Tỷ lệ chuyển đổi (Từ Đơn đã đặt thành Đơn đã xác nhận)', '0%')),
        }

        return self._upsert(
            [
                ('shop_id', '=', shop_id),
                ('report_date', '=', report_date),
                ('hour', '=', vals['hour'])
            ],
            vals
        )
