# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.misc import str2bool


class ShopeeOrderReport(models.Model):
    _name = 'shopee.order.report'
    _description = 'Shopee Order Report'
    _inherit = 'shopee.report.mixin'
    _order = 'order_date desc, id desc'

    # ==================== BASIC INFO ====================
    shop_id = fields.Many2one(
        'shopee.shop',
        string='Shop',
        required=True,
        index=True,
        ondelete='cascade',
    )

    # ==================== ORDER INFO ====================
    order_id = fields.Char(
        string='Order ID',
        required=True,
        index=True,
        help='Mã đơn hàng'
    )

    package_id = fields.Char(
        string='Package ID',
        help='Mã Kiện Hàng'
    )

    order_date = fields.Datetime(
        string='Order Date',
        required=True,
        index=True,
        help='Ngày đặt hàng'
    )

    order_status = fields.Char(
        string='Order Status',
        help='Trạng thái đơn hàng'
    )

    hot_product = fields.Boolean(
        string='Hot Product',
        help='Sản phẩm Bán Chạy'
    )

    cancel_reason = fields.Char(
        string='Cancel Reason',
        help='Lý do hủy'
    )

    customer_review = fields.Text(
        string='Customer Review',
        help='Nhận xét từ Người mua'
    )

    # ==================== SHIPPING INFO ====================
    tracking_number = fields.Char(
        string='Tracking Number',
        help='Mã vận đơn'
    )

    shipping_carrier = fields.Char(
        string='Shipping Carrier',
        help='Đơn Vị Vận Chuyển'
    )

    delivery_method = fields.Char(
        string='Delivery Method',
        help='Phương thức giao hàng'
    )

    order_type = fields.Char(
        string='Order Type',
        help='Loại đơn hàng'
    )

    ship_date = fields.Datetime(
        string='Ship Date',
        help='Ngày xuất hàng'
    )

    expected_delivery_date = fields.Datetime(
        string='Expected Delivery Date',
        help='Ngày giao hàng dự kiến'
    )

    domestic_delivery_date = fields.Date(
        string='Domestic Delivery Date',
        help='Ngày giao hàng nội địa'
    )

    delivery_date = fields.Datetime(
        string='Delivery Date',
        help='Thời gian giao hàng'
    )

    order_completion_date = fields.Datetime(
        string='Order Completion Date',
        help='Thời gian hoàn thành đơn hàng'
    )

    return_refund_status = fields.Char(
        string='Return/Refund Status',
        help='Trạng thái Trả hàng/Hoàn tiền'
    )

    cancel_success_date = fields.Date(
        string='Cancel Success Date',
        help='Ngày hủy thành công'
    )

    processed_by_shopee = fields.Boolean(
        string='Processed by Shopee',
        help='Đơn hàng được xử lý bởi Shopee'
    )

    # ==================== PRODUCT INFO ====================
    product_sku = fields.Char(
        string='Product SKU',
        index=True,
        help='SKU sản phẩm'
    )

    product_name = fields.Char(
        string='Product Name',
        help='Tên sản phẩm'
    )

    product_weight = fields.Float(
        string='Product Weight',
        digits=(8, 2),
        help='Cân nặng sản phẩm'
    )

    total_weight = fields.Float(
        string='Total Weight',
        digits=(8, 2),
        help='Tổng cân nặng'
    )

    # ==================== WAREHOUSE INFO ====================
    warehouse_name = fields.Char(
        string='Warehouse Name',
        help='Tên kho hàng'
    )

    category_sku = fields.Char(
        string='Category SKU',
        help='SKU phân loại hàng'
    )

    category_name = fields.Char(
        string='Category Name',
        help='Tên phân loại hàng'
    )

    owned_by_shopee = fields.Boolean(
        string='Owned by Shopee',
        help='Sở hữu bởi Shopee'
    )

    # ==================== PRICING INFO ====================
    original_price = fields.Float(
        string='Original Price',
        digits=(16, 2),
        help='Giá gốc'
    )

    seller_discount = fields.Float(
        string='Seller Discount',
        digits=(16, 2),
        help='Người bán trợ giá'
    )

    shopee_discount = fields.Float(
        string='Shopee Discount',
        digits=(16, 2),
        help='Được Shopee trợ giá'
    )

    total_seller_discount = fields.Float(
        string='Total Seller Discount',
        digits=(16, 2),
        help='Tổng số tiền được người bán trợ giá'
    )

    discounted_price = fields.Float(
        string='Discounted Price',
        digits=(16, 2),
        help='Giá ưu đãi'
    )

    quantity = fields.Integer(
        string='Quantity',
        help='Số lượng'
    )

    returned_quantity = fields.Integer(
        string='Returned Quantity',
        help='Số lượng sản phẩm được hoàn trả'
    )

    # ==================== REVENUE INFO ====================
    total_product_price = fields.Float(
        string='Total Product Price',
        digits=(16, 2),
        help='Tổng giá bán (sản phẩm)'
    )

    total_order_value = fields.Float(
        string='Total Order Value',
        digits=(16, 2),
        help='Tổng giá trị đơn hàng (VND)'
    )

    shop_discount_code = fields.Char(
        string='Shop Discount Code',
        help='Mã giảm giá của Shop'
    )

    cashback = fields.Float(
        string='Cashback',
        digits=(16, 2),
        help='Hoàn Xu'
    )

    shopee_discount_code = fields.Char(
        string='Shopee Discount Code',
        help='Mã giảm giá của Shopee'
    )

    combo_promotion_target = fields.Char(
        string='Combo Promotion Target',
        help='Chỉ tiêu Combo Khuyến Mãi'
    )

    shopee_combo_discount = fields.Float(
        string='Shopee Combo Discount',
        digits=(16, 2),
        help='Giảm giá từ combo Shopee'
    )

    shop_combo_discount = fields.Float(
        string='Shop Combo Discount',
        digits=(16, 2),
        help='Giảm giá từ Combo của Shop'
    )

    shopee_coin_refund = fields.Float(
        string='Shopee Coin Refund',
        digits=(16, 2),
        help='Shopee Xu được hoàn'
    )

    debit_card_discount = fields.Float(
        string='Debit Card Discount',
        digits=(16, 2),
        help='Số tiền được giảm khi thanh toán bằng thẻ Ghi nợ'
    )

    trade_in_discount = fields.Float(
        string='Trade-in Discount',
        digits=(16, 2),
        help='Trade-in Discount'
    )

    trade_in_bonus = fields.Float(
        string='Trade-in Bonus',
        digits=(16, 2),
        help='Trade-in Bonus'
    )

    expected_shipping_fee = fields.Float(
        string='Expected Shipping Fee',
        digits=(16, 2),
        help='Phí vận chuyển (dự kiến)'
    )

    seller_trade_in_bonus = fields.Float(
        string='Seller Trade-in Bonus',
        digits=(16, 2),
        help='Trade-in Bonus by Seller'
    )

    customer_shipping_fee = fields.Float(
        string='Customer Shipping Fee',
        digits=(16, 2),
        help='Phí vận chuyển mà người mua trả'
    )

    return_fee = fields.Float(
        string='Return Fee',
        digits=(16, 2),
        help='Phí trả hàng'
    )

    total_customer_payment = fields.Float(
        string='Total Customer Payment',
        digits=(16, 2),
        help='Tổng số tiền người mua thanh toán'
    )

    # ==================== PAYMENT INFO ====================
    payment_date = fields.Datetime(
        string='Payment Date',
        help='Thời gian đơn hàng được thanh toán'
    )

    deposit_verification_date = fields.Date(
        string='Deposit Verification Date',
        help='Ngày xác minh ký quỹ'
    )

    payment_method = fields.Char(
        string='Payment Method',
        help='Phương thức thanh toán'
    )

    fixed_fee = fields.Float(
        string='Fixed Fee',
        digits=(16, 2),
        help='Phí cố định'
    )

    service_fee = fields.Float(
        string='Service Fee',
        digits=(16, 2),
        help='Phí Dịch Vụ'
    )

    payment_fee = fields.Float(
        string='Payment Fee',
        digits=(16, 2),
        help='Phí thanh toán'
    )

    deposit_amount = fields.Float(
        string='Deposit Amount',
        digits=(16, 2),
        help='Tiền ký quỹ'
    )

    # ==================== CUSTOMER INFO ====================
    buyer = fields.Char(
        string='Buyer',
        help='Người mua'
    )

    recipient_name = fields.Char(
        string='Recipient Name',
        help='Tên người nhận'
    )

    phone_number = fields.Char(
        string='Phone Number',
        help='Số điện thoại'
    )

    province_city = fields.Char(
        string='Province/City',
        help='Tỉnh/Thành phố'
    )

    city_district = fields.Char(
        string='City/District',
        help='TP / Quận / Huyện'
    )

    district = fields.Char(
        string='District',
        help='Quận'
    )

    delivery_address = fields.Text(
        string='Delivery Address',
        help='Địa chỉ nhận hàng'
    )

    country = fields.Char(
        string='Country',
        help='Quốc gia'
    )

    notes = fields.Text(
        string='Notes',
        help='Ghi chú'
    )

    # ==================== HELPER METHODS ====================
    @api.model
    def _import_row(self, shop_id, order_date, row_data):
        """Create Order report record from CSV row data"""

        vals = {
            'shop_id': shop_id,
            'order_id': row_data.get('Mã đơn hàng', ''),
            'package_id': row_data.get('Mã Kiện Hàng', ''),
            'order_date': self._parse_datetime(row_data.get('Ngày đặt hàng', ''), '%Y-%m-%d %H:%M'),
            'order_status': row_data.get('Trạng Thái Đơn Hàng', ''),
            'hot_product': str2bool(row_data.get('Sản phẩm Bán Chạy', ''), default=False),
            'cancel_reason': row_data.get('Lý do hủy', ''),
            'customer_review': row_data.get('Nhận xét từ Người mua', ''),
            'tracking_number': row_data.get('Mã vận đơn', ''),
            'shipping_carrier': row_data.get('Đơn Vị Vận Chuyển', ''),
            'delivery_method': row_data.get('Phương thức giao hàng', ''),
            'order_type': row_data.get('Loại đơn hàng', ''),
            'ship_date': self._parse_datetime(row_data.get('Ngày xuất hàng', ''), '%Y-%m-%d %H:%M'),
            'expected_delivery_date': self._parse_datetime(row_data.get('Ngày giao hàng dự kiến', ''), '%Y-%m-%d %H:%M'),
            'domestic_delivery_date': self._parse_date(row_data.get('Ngày giao hàng nội địa', '')),
            'delivery_date': self._parse_datetime(row_data.get('Thời gian giao hàng', ''), '%Y-%m-%d %H:%M'),
            'order_completion_date': self._parse_datetime(row_data.get('Thời gian hoàn thành đơn hàng', ''), '%Y-%m-%d %H:%M'),
            'return_refund_status': row_data.get('Trạng thái Trả hàng/Hoàn tiền', ''),
            'cancel_success_date': self._parse_date(row_data.get('Ngày hủy thành công', '')),
            'processed_by_shopee': str2bool(row_data.get('Đơn hàng được xử lý bởi Shopee', ''), default=False),
            'product_sku': row_data.get('SKU sản phẩm', ''),
            'product_name': row_data.get('Tên sản phẩm', ''),
            'product_weight': self._parse_float(row_data.get('Cân nặng sản phẩm', '0')),
            'total_weight': self._parse_float(row_data.get('Tổng cân nặng', '0')),
            'warehouse_name': row_data.get('Tên kho hàng', ''),
            'category_sku': row_data.get('SKU phân loại hàng', ''),
            'category_name': row_data.get('Tên phân loại hàng', ''),
            'owned_by_shopee': str2bool(row_data.get('Sở hữu bởi Shopee', ''), default=False),
            'original_price': self._parse_float(row_data.get('Giá gốc', '0')),
            'seller_discount': self._parse_float(row_data.get('Người bán trợ giá', '0')),
            'shopee_discount': self._parse_float(row_data.get('Được Shopee trợ giá', '0')),
            'total_seller_discount': self._parse_float(row_data.get('Tổng số tiền được người bán trợ giá', '0')),
            'discounted_price': self._parse_float(row_data.get('Giá ưu đãi', '0')),
            'quantity': int(self._parse_float(row_data.get('Số lượng', '0'))),
            'returned_quantity': int(self._parse_float(row_data.get('Số lượng sản phẩm được hoàn trả', '0'))),
            'total_product_price': self._parse_float(row_data.get('Tổng giá bán (sản phẩm)', '0')),
            'total_order_value': self._parse_float(row_data.get('Tổng giá trị đơn hàng (VND)', '0')),
            'shop_discount_code': row_data.get('Mã giảm giá của Shop', ''),
            'cashback': self._parse_float(row_data.get('Hoàn Xu', '0')),
            'shopee_discount_code': row_data.get('Mã giảm giá của Shopee', ''),
            'combo_promotion_target': row_data.get('Chỉ tiêu Combo Khuyến Mãi', ''),
            'shopee_combo_discount': self._parse_float(row_data.get('Giảm giá từ combo Shopee', '0')),
            'shop_combo_discount': self._parse_float(row_data.get('Giảm giá từ Combo của Shop', '0')),
            'shopee_coin_refund': self._parse_float(row_data.get('Shopee Xu được hoàn', '0')),
            'debit_card_discount': self._parse_float(row_data.get('Số tiền được giảm khi thanh toán bằng thẻ Ghi nợ', '0')),
            'trade_in_discount': self._parse_float(row_data.get('Trade-in Discount', '0')),
            'trade_in_bonus': self._parse_float(row_data.get('Trade-in Bonus', '0')),
            'expected_shipping_fee': self._parse_float(row_data.get('Phí vận chuyển (dự kiến)', '0')),
            'seller_trade_in_bonus': self._parse_float(row_data.get('Trade-in Bonus by Seller', '0')),
            'customer_shipping_fee': self._parse_float(row_data.get('Phí vận chuyển mà người mua trả', '0')),
            'return_fee': self._parse_float(row_data.get('Phí trả hàng', '0')),
            'total_customer_payment': self._parse_float(row_data.get('Tổng số tiền người mua thanh toán', '0')),
            'payment_date': self._parse_datetime(row_data.get('Thời gian đơn hàng được thanh toán', ''), '%Y-%m-%d %H:%M'),
            'deposit_verification_date': self._parse_date(row_data.get('Ngày xác minh ký quỹ', '')),
            'payment_method': row_data.get('Phương thức thanh toán', ''),
            'fixed_fee': self._parse_float(row_data.get('Phí cố định', '0')),
            'service_fee': self._parse_float(row_data.get('Phí Dịch Vụ', '0')),
            'payment_fee': self._parse_float(row_data.get('Phí thanh toán', '0')),
            'deposit_amount': self._parse_float(row_data.get('Tiền ký quỹ', '0')),
            'buyer': row_data.get('Người Mua', ''),
            'recipient_name': row_data.get('Tên Người nhận', ''),
            'phone_number': row_data.get('Số điện thoại', ''),
            'province_city': row_data.get('Tỉnh/Thành phố', ''),
            'city_district': row_data.get('TP / Quận / Huyện', ''),
            'district': row_data.get('Quận', ''),
            'delivery_address': row_data.get('Địa chỉ nhận hàng', ''),
            'country': row_data.get('Quốc gia', ''),
            'notes': row_data.get('Ghi chú', ''),
        }

        return self._upsert(
            [
                ('shop_id', '=', shop_id),
                ('order_id', '=', vals['order_id']),
                ('product_sku', '=', vals['product_sku']),
            ],
            vals
        )
