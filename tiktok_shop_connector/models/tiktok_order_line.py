import logging
from odoo import api, models, fields, _

_logger = logging.getLogger(__name__)


class TiktokOrderLine(models.Model):
    _name = "tiktok.order.line"
    _description = "TikTok Order Line Items"
    _order = "order_id desc"

    # ===== Basic Information =====
    tiktok_id = fields.Char(string="TikTok Line ID", required=True, index=True)
    order_id = fields.Many2one("tiktok.order", string="Order", required=True, index=True, ondelete="cascade")
    shop_id = fields.Many2one("tiktok.shop", string="Shop", related="order_id.shop_id", store=True)

    # ===== Product & SKU References =====
    product_id = fields.Many2one("tiktok.product", string="Product", related="sku_id.product_id", store=True, index=True)
    sku_id = fields.Many2one("tiktok.sku", string="SKU", index=True)
    tiktok_product_id = fields.Char(string="TikTok Product ID")
    tiktok_sku_id = fields.Char(string="TikTok SKU ID")
    seller_sku = fields.Char(string="Seller SKU")

    # ===== Product Information =====
    product_name = fields.Char(string="Product Name")
    sku_name = fields.Char(string="SKU Name")
    sku_image = fields.Char(string="SKU Image URL")

    # ===== Pricing Information =====
    currency = fields.Char(string="Currency", default="IDR")
    original_price = fields.Float(string="Original Price", digits="Product Price")
    sale_price = fields.Float(string="Sale Price", digits="Product Price")
    platform_discount = fields.Float(string="Platform Discount", digits="Product Price")
    seller_discount = fields.Float(string="Seller Discount", digits="Product Price")
    small_order_fee = fields.Float(string="Small Order Fee", digits="Product Price")
    retail_delivery_fee = fields.Float(string="Retail Delivery Fee", digits="Product Price")
    buyer_service_fee = fields.Float(string="Buyer Service Fee", digits="Product Price")

    # ===== Tax Information =====
    item_tax = fields.Json(string="Item Tax Details")

    # ===== Status Information =====
    display_status = fields.Selection([
        ('UNPAID', 'Unpaid'),
        ('AWAITING_SHIPMENT', 'Awaiting Shipment'),
        ('AWAITING_COLLECTION', 'Awaiting Collection'),
        ('IN_TRANSIT', 'In Transit'),
        ('DELIVERED', 'Delivered'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ], string="Display Status")
    cancel_user = fields.Selection([
        ('BUYER', 'Buyer'),
        ('SELLER', 'Seller'),
        ('OPERATOR', 'Operator'),
        ('SYSTEM', 'System'),
    ], string="Cancel User")
    cancel_reason = fields.Char(string="Cancel Reason")
    sku_type = fields.Selection([
        ('NORMAL', 'Normal'),
        ('ZERO_LOTTERY', 'Zero Lottery'),
        ('SHOP_PARTNER', 'Shop Partner'),
        ('PRE_ORDER', 'Pre Order'),
        ('MADE_TO_ORDER', 'Made to Order'),
        ('UNKNOWN', 'Unknown'),
    ], string="SKU Type")
    package_status = fields.Selection([
        ('TO_FULFILL', 'To Fulfill'),
        ('PROCESSING', 'Processing'),
        ('FULFILLING', 'Fulfilling'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ], string="Package Status")

    # ===== Shipping Information =====
    shipping_provider_id = fields.Char(string="Shipping Provider ID")
    shipping_provider_name = fields.Char(string="Shipping Provider Name")
    tracking_number = fields.Char(string="Tracking Number")
    package_id = fields.Char(string="Package ID")
    handling_duration_days = fields.Integer(string="Handling Duration (Days)")

    # ===== Additional Line Item Information =====
    request_cancel_time = fields.Datetime(string="Request Cancel Time")
    delivery_time = fields.Datetime(string="Delivery Time")
    collection_time = fields.Datetime(string="Collection Time")
    cancel_time = fields.Datetime(string="Cancel Time")
    delivery_due_time = fields.Datetime(string="Delivery Due Time")
    collection_due_time = fields.Datetime(string="Collection Due Time")
    pick_up_cut_off_time = fields.Datetime(string="Pick Up Cut Off Time")
    fast_dispatch_sla_time = fields.Datetime(string="Fast Dispatch SLA Time")
    is_on_hold_order = fields.Boolean(string="Is On Hold Order")
    shipping_type = fields.Selection([
        ('TIKTOK', 'TikTok'),
        ('SELLER', 'Seller'),
    ], string="Shipping Type")
    sell_order_fee = fields.Float(string="Sell Order Fee", digits="Product Price")

    # ===== Combined Listing SKUs =====
    combined_listing_skus = fields.Json(string="Combined Listing SKUs")

    # ===== Special Flags =====
    is_gift = fields.Boolean(string="Is Gift", default=False)
    is_dangerous_good = fields.Boolean(string="Is Dangerous Good", default=False)
    needs_prescription = fields.Boolean(string="Needs Prescription", default=False)

    # ===== Timestamps =====
    rts_time = fields.Datetime(string="RTS Time")

    _sql_constraints = [
        ('tiktok_id_unique', 'unique(tiktok_id)', 'TikTok Line ID must be unique!'),
    ]

    @api.depends('product_name', 'sku_name', 'seller_sku')
    def _compute_display_name(self):
        """Create display name for the order line."""
        for line in self:
            if line.product_name and line.sku_name:
                if line.seller_sku:
                    line.display_name = f"{line.product_name} - {line.sku_name} ({line.seller_sku})"
                else:
                    line.display_name = f"{line.product_name} - {line.sku_name}"
            else:
                line.display_name = f"Line {line.tiktok_id}"

    def _parse_line_item_data(self, line_data, order_id):
        """Parse line item data from TikTok API response."""
        if not isinstance(line_data, dict):
            return {}

        Shop = self.env['tiktok.shop']

        return {
            'tiktok_id': line_data.get('id'),
            'order_id': order_id,
            'tiktok_product_id': line_data.get('product_id'),
            'tiktok_sku_id': line_data.get('sku_id'),
            'seller_sku': line_data.get('seller_sku'),
            'product_name': line_data.get('product_name'),
            'sku_name': line_data.get('sku_name'),
            'sku_image': line_data.get('sku_image'),
            'currency': line_data.get('currency', 'IDR'),
            'original_price': Shop._parse_number(line_data.get('original_price', 0)),
            'sale_price': Shop._parse_number(line_data.get('sale_price', 0)),
            'platform_discount': Shop._parse_number(line_data.get('platform_discount', 0)),
            'seller_discount': Shop._parse_number(line_data.get('seller_discount', 0)),
            'small_order_fee': Shop._parse_number(line_data.get('small_order_fee', 0)),
            'retail_delivery_fee': Shop._parse_number(line_data.get('retail_delivery_fee', 0)),
            'buyer_service_fee': Shop._parse_number(line_data.get('buyer_service_fee', 0)),
            'item_tax': line_data.get('item_tax', []),
            'display_status': line_data.get('display_status'),
            'cancel_user': line_data.get('cancel_user'),
            'cancel_reason': line_data.get('cancel_reason'),
            'sku_type': line_data.get('sku_type'),
            'package_status': line_data.get('package_status'),
            'shipping_provider_id': line_data.get('shipping_provider_id'),
            'shipping_provider_name': line_data.get('shipping_provider_name'),
            'tracking_number': line_data.get('tracking_number'),
            'package_id': line_data.get('package_id'),
            'handling_duration_days': Shop._parse_number(line_data.get('handling_duration_days', 0)),
            'combined_listing_skus': line_data.get('combined_listing_skus', []),
            'is_gift': line_data.get('is_gift', False),
            'is_dangerous_good': line_data.get('is_dangerous_good', False),
            'needs_prescription': line_data.get('needs_prescription', False),
            'rts_time': Shop._convert_unix_to_datetime(line_data.get('rts_time')),

            # Additional Line Item Information
            'request_cancel_time': Shop._convert_unix_to_datetime(line_data.get('request_cancel_time')),
            'delivery_time': Shop._convert_unix_to_datetime(line_data.get('delivery_time')),
            'collection_time': Shop._convert_unix_to_datetime(line_data.get('collection_time')),
            'cancel_time': Shop._convert_unix_to_datetime(line_data.get('cancel_time')),
            'delivery_due_time': Shop._convert_unix_to_datetime(line_data.get('delivery_due_time')),
            'collection_due_time': Shop._convert_unix_to_datetime(line_data.get('collection_due_time')),
            'pick_up_cut_off_time': Shop._convert_unix_to_datetime(line_data.get('pick_up_cut_off_time')),
            'fast_dispatch_sla_time': Shop._convert_unix_to_datetime(line_data.get('fast_dispatch_sla_time')),
            'is_on_hold_order': line_data.get('is_on_hold_order', False),
            'shipping_type': line_data.get('shipping_type'),
            'sell_order_fee': Shop._parse_number(line_data.get('sell_order_fee', 0)),
        }

    @api.model
    def _upsert_line_item(self, line_data, order_id):
        """Create or update order line item from TikTok API data."""
        if not line_data or not order_id:
            return False

        parsed_data = self._parse_line_item_data(line_data, order_id)
        if not parsed_data.get('tiktok_id'):
            _logger.warning("Line item data missing tiktok_id: %s", line_data)
            return False

        # Find related product and SKU
        if parsed_data.get('tiktok_sku_id'):
            sku = self.env['tiktok.sku'].search([
                ('tiktok_id', '=', parsed_data.get('tiktok_sku_id'))
            ], limit=1)
            if sku:
                parsed_data['sku_id'] = sku.id

        # Upsert order line using helper method
        order_line = self.env['tiktok.shop']._upsert(
            'tiktok.order.line',
            [('tiktok_id', '=', parsed_data['tiktok_id'])],
            parsed_data
        )
        return order_line
