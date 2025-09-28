import logging
from odoo import api, models, fields, _

_logger = logging.getLogger(__name__)


class TiktokReturnLine(models.Model):
    _name = "tiktok.return.line"
    _description = "TikTok Return Line Items"
    _order = "return_id desc"

    # ===== Basic Information =====
    return_line_item_id = fields.Char(string="Return Line Item ID", required=True, index=True)
    return_id = fields.Many2one("tiktok.return", string="Return", required=True, index=True, ondelete="cascade")
    shop_id = fields.Many2one("tiktok.shop", string="Shop", related="return_id.shop_id", store=True)

    # ===== Product & SKU References =====
    product_id = fields.Many2one("tiktok.product", string="Product", related="sku_id.product_id", store=True, index=True)
    sku_id = fields.Many2one("tiktok.sku", string="SKU", index=True)
    order_line_item_id = fields.Char(string="Order Line Item ID")
    tiktok_sku_id = fields.Char(string="TikTok SKU ID")
    seller_sku = fields.Char(string="Seller SKU")

    # ===== Product Information =====
    product_name = fields.Char(string="Product Name")
    sku_name = fields.Char(string="SKU Name")
    product_image_uri = fields.Char(string="Product Image URL")
    product_image_width = fields.Integer(string="Product Image Width")
    product_image_height = fields.Integer(string="Product Image Height")

    # ===== Refund Amount Information =====
    refund_currency = fields.Char(string="Refund Currency")
    refund_total = fields.Float(string="Refund Total", digits="Product Price")
    refund_subtotal = fields.Float(string="Refund Subtotal", digits="Product Price")
    refund_shipping_fee = fields.Float(string="Refund Shipping Fee", digits="Product Price")
    refund_tax = fields.Float(string="Refund Tax", digits="Product Price")
    retail_delivery_fee = fields.Float(string="Retail Delivery Fee", digits="Product Price")
    buyer_service_fee = fields.Float(string="Buyer Service Fee", digits="Product Price")

    # ===== Discount Amount Information =====
    discount_currency = fields.Char(string="Discount Currency")
    product_seller_discount = fields.Float(string="Product Seller Discount", digits="Product Price")
    shipping_fee_platform_discount = fields.Float(string="Shipping Fee Platform Discount", digits="Product Price")
    shipping_fee_seller_discount = fields.Float(string="Shipping Fee Seller Discount", digits="Product Price")
    product_platform_discount = fields.Float(string="Product Platform Discount", digits="Product Price")

    # ===== Shipping Fee Amount Information =====
    shipping_fee_currency = fields.Char(string="Shipping Fee Currency")
    seller_paid_return_shipping_fee = fields.Float(string="Seller Paid Return Shipping Fee", digits="Product Price")
    platform_paid_return_shipping_fee = fields.Float(string="Platform Paid Return Shipping Fee", digits="Product Price")
    buyer_paid_return_shipping_fee = fields.Float(string="Buyer Paid Return Shipping Fee", digits="Product Price")

    _sql_constraints = [
        ('return_line_item_id_unique', 'unique(return_line_item_id)', 'Return Line Item ID must be unique!'),
    ]

    @api.depends('product_name', 'sku_name', 'seller_sku')
    def _compute_display_name(self):
        """Create display name for the return line."""
        for line in self:
            if line.product_name and line.sku_name:
                if line.seller_sku:
                    line.display_name = f"{line.product_name} - {line.sku_name} ({line.seller_sku})"
                else:
                    line.display_name = f"{line.product_name} - {line.sku_name}"
            else:
                line.display_name = f"Return Line {line.return_line_item_id}"

    def _parse_return_line_data(self, line_data, return_id):
        """Parse return line item data from TikTok API response."""
        if not isinstance(line_data, dict):
            return {}

        Shop = self.env['tiktok.shop']

        # Extract product image information
        product_image = line_data.get('product_image', {})
        product_image_uri = product_image.get('uri')
        product_image_width = product_image.get('width')
        product_image_height = product_image.get('height')

        # Extract refund amount
        refund_amount = line_data.get('refund_amount', {})
        refund_currency = refund_amount.get('currency')
        refund_total = Shop._parse_number(refund_amount.get('refund_total', 0))
        refund_subtotal = Shop._parse_number(refund_amount.get('refund_subtotal', 0))
        refund_shipping_fee = Shop._parse_number(refund_amount.get('refund_shipping_fee', 0))
        refund_tax = Shop._parse_number(refund_amount.get('refund_tax', 0))
        retail_delivery_fee = Shop._parse_number(refund_amount.get('retail_delivery_fee', 0))
        buyer_service_fee = Shop._parse_number(refund_amount.get('buyer_service_fee', 0))

        # Extract discount amount (first item in array)
        discount_amounts = line_data.get('discount_amount', [])
        discount_currency = None
        product_seller_discount = 0
        shipping_fee_platform_discount = 0
        shipping_fee_seller_discount = 0
        product_platform_discount = 0

        if discount_amounts and isinstance(discount_amounts, list) and len(discount_amounts) > 0:
            discount_data = discount_amounts[0]
            discount_currency = discount_data.get('currency')
            product_seller_discount = Shop._parse_number(discount_data.get('product_seller_discount', 0))
            shipping_fee_platform_discount = Shop._parse_number(discount_data.get('shipping_fee_platform_discount', 0))
            shipping_fee_seller_discount = Shop._parse_number(discount_data.get('shipping_fee_seller_discount', 0))
            product_platform_discount = Shop._parse_number(discount_data.get('product_platform_discount', 0))

        # Extract shipping fee amount (first item in array)
        shipping_fee_amounts = line_data.get('shipping_fee_amount', [])
        shipping_fee_currency = None
        seller_paid_return_shipping_fee = 0
        platform_paid_return_shipping_fee = 0
        buyer_paid_return_shipping_fee = 0

        if shipping_fee_amounts and isinstance(shipping_fee_amounts, list) and len(shipping_fee_amounts) > 0:
            shipping_data = shipping_fee_amounts[0]
            shipping_fee_currency = shipping_data.get('currency')
            seller_paid_return_shipping_fee = Shop._parse_number(shipping_data.get('seller_paid_return_shipping_fee', 0))
            platform_paid_return_shipping_fee = Shop._parse_number(shipping_data.get('platform_paid_return_shipping_fee', 0))
            buyer_paid_return_shipping_fee = Shop._parse_number(shipping_data.get('buyer_paid_return_shipping_fee', 0))

        return {
            'return_line_item_id': line_data.get('return_line_item_id'),
            'return_id': return_id,
            'order_line_item_id': line_data.get('order_line_item_id'),
            'tiktok_sku_id': line_data.get('sku_id'),
            'seller_sku': line_data.get('seller_sku'),
            'product_name': line_data.get('product_name'),
            'sku_name': line_data.get('sku_name'),
            'product_image_uri': product_image_uri,
            'product_image_width': product_image_width,
            'product_image_height': product_image_height,
            'refund_currency': refund_currency,
            'refund_total': refund_total,
            'refund_subtotal': refund_subtotal,
            'refund_shipping_fee': refund_shipping_fee,
            'refund_tax': refund_tax,
            'retail_delivery_fee': retail_delivery_fee,
            'buyer_service_fee': buyer_service_fee,
            'discount_currency': discount_currency,
            'product_seller_discount': product_seller_discount,
            'shipping_fee_platform_discount': shipping_fee_platform_discount,
            'shipping_fee_seller_discount': shipping_fee_seller_discount,
            'product_platform_discount': product_platform_discount,
            'shipping_fee_currency': shipping_fee_currency,
            'seller_paid_return_shipping_fee': seller_paid_return_shipping_fee,
            'platform_paid_return_shipping_fee': platform_paid_return_shipping_fee,
            'buyer_paid_return_shipping_fee': buyer_paid_return_shipping_fee,
        }

    @api.model
    def _upsert_return_line(self, line_data, return_id):
        """Create or update return line item from TikTok API data."""
        if not line_data or not return_id:
            return False

        parsed_data = self._parse_return_line_data(line_data, return_id)
        if not parsed_data.get('return_line_item_id'):
            _logger.warning("Return line data missing return_line_item_id: %s", line_data)
            return False

        # Find related product and SKU
        if parsed_data.get('tiktok_sku_id'):
            sku = self.env['tiktok.sku'].search([
                ('tiktok_id', '=', parsed_data.get('tiktok_sku_id'))
            ], limit=1)
            if sku:
                parsed_data['sku_id'] = sku.id

        # Upsert return line using helper method
        return_line = self.env['tiktok.shop']._upsert(
            'tiktok.return.line',
            [('return_line_item_id', '=', parsed_data['return_line_item_id'])],
            parsed_data
        )
        return return_line
