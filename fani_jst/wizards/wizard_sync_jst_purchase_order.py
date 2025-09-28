from odoo import models, fields


class WizardSyncJSTPurchaseOrder(models.TransientModel):
    _name = 'wizard.sync.jst.purchase.order'
    _description = 'Wizard Sync JST Purchase Order'

    def _default_date_from(self):
        return fields.Datetime.now()
    def _default_date_to(self):
        return fields.Datetime.now()

    # Basic info from API
    date_from = fields.Datetime("Ngày Bắt đầu", default=_default_date_from)
    date_to = fields.Datetime("Ngày kết thúc", default=_default_date_to)

    def action_sync(self):
        requestModel = {
            "modifiedBegin": int(self.date_from.timestamp()),
            "modifiedEnd": int(self.date_to.timestamp())
        }
        self.env['jst.purchase.order']._sync_jst_purchase_orders(requestModel)
