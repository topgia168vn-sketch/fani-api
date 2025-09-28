from odoo import models, fields


class JstPurchaseOrderProcess(models.Model):
    _name = 'jst.purchase.order.process'
    _description = 'JST Purchase Process'
    _rec_name = 'title'
    _order = 'processId desc'

    # Many2one relationship back to Purchase Order
    jst_purchase_order_id = fields.Many2one(
        'jst.purchase.order',
        string='Purchase Order',
        required=True,
        ondelete='cascade',
        help="Related purchase order"
    )

    # ==== Purchase Process Fields ====
    processId = fields.Integer("Process ID", help="Process number", index=True)
    purchaseId = fields.Char("Purchase ID", help="Purchase Order Number", index=True)
    title = fields.Char("Title", help="Process title", index=True)
    remark = fields.Text("Remark", help="Notes (Image)")
    bussinessTime = fields.Datetime("Business Time", help="Business time")

    def _map_fields(self):
        return {
            'processId': 'boxCapacity',
            'purchaseId': 'boxQuantity',
            'title': 'companyId',
            'remark': 'created',
            'bussinessTime': 'bussinessTime'
        }
