from odoo import models, fields


class JstSaleOrderStatusHistory(models.Model):
    _name = 'jst.sale.order.tracking'
    _description = 'JST Sale Order Tracking'
    _order = 'jst_modified desc'
    _rec_name = 'orderId'

    orderId = fields.Integer("Order ID", aggregator=None)
    jst_modified = fields.Datetime("JST Modified")
    field_check = fields.Char("JST Field Check")
    field_value = fields.Char("JST Field Value")

    # Tham chiếu
    jst_order_id = fields.Many2one(
        'jst.sale.order',
        string='JST Order',
        required=True,
        ondelete='cascade',
        index=True
    )
    # raw-data to re-check
    raw_payload = fields.Json(
        string="Raw Payload",
        help="Full JSON order object as returned by API at the time of this status change"
    )
