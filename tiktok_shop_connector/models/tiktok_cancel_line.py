import logging
from odoo import api, models, fields, _

_logger = logging.getLogger(__name__)


class TiktokCancelLine(models.Model):
    _name = "tiktok.cancel.line"
    _description = "TikTok Cancel Line Items"
    _order = "cancel_id desc"

    # ===== Basic Information =====
    cancel_line_item_id = fields.Char(string="Cancel Line Item ID", required=True, index=True)
    cancel_id = fields.Many2one("tiktok.cancel", string="Cancellation", required=True, index=True, ondelete="cascade")
    shop_id = fields.Many2one("tiktok.shop", string="Shop", related="cancel_id.shop_id", store=True)

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

    _sql_constraints = [
        ('cancel_line_item_id_unique', 'unique(cancel_line_item_id)', 'Cancel Line Item ID must be unique!'),
    ]

    @api.depends('product_name', 'sku_name', 'seller_sku')
    def _compute_display_name(self):
        """Create display name for the cancel line."""
        for line in self:
            if line.product_name and line.sku_name:
                if line.seller_sku:
                    line.display_name = f"{line.product_name} - {line.sku_name} ({line.seller_sku})"
                else:
                    line.display_name = f"{line.product_name} - {line.sku_name}"
            else:
                line.display_name = f"Cancel Line {line.cancel_line_item_id}"

    def _parse_cancel_line_data(self, line_data, cancel_id):
        """Parse cancel line item data from TikTok API response."""
        if not isinstance(line_data, dict):
            return {}

        Shop = self.env['tiktok.shop']

        # Extract product image information
        product_image = line_data.get('product_image', {})
        product_image_uri = product_image.get('url')
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

        return {
            'cancel_line_item_id': line_data.get('cancel_line_item_id'),
            'cancel_id': cancel_id,
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
        }

    @api.model
    def _upsert_cancel_line(self, line_data, cancel_id):
        """Create or update cancel line item from TikTok API data."""
        if not line_data or not cancel_id:
            return False

        parsed_data = self._parse_cancel_line_data(line_data, cancel_id)
        if not parsed_data.get('cancel_line_item_id'):
            _logger.warning("Cancel line data missing cancel_line_item_id: %s", line_data)
            return False

        # Find related product and SKU
        if parsed_data.get('tiktok_sku_id'):
            sku = self.env['tiktok.sku'].search([
                ('tiktok_id', '=', parsed_data.get('tiktok_sku_id'))
            ], limit=1)
            if sku:
                parsed_data['sku_id'] = sku.id

        # Upsert cancel line using helper method
        cancel_line = self.env['tiktok.shop']._upsert(
            'tiktok.cancel.line',
            [('cancel_line_item_id', '=', parsed_data['cancel_line_item_id'])],
            parsed_data
        )
        return cancel_line
