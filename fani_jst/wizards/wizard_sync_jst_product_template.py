import time
from odoo import models, fields


class WizardSyncJSTProductTemplate(models.TransientModel):
    _name = 'wizard.sync.jst.product.template'
    _description = 'Wizard Sync JST Product Template'

    def _default_date_from(self):
        return fields.Datetime.now()
    def _default_date_to(self):
        return fields.Datetime.now()

    # Basic info from API
    date_from = fields.Datetime("Ngày Bắt đầu", default=_default_date_from)
    date_to = fields.Datetime("Ngày kết thúc", default=_default_date_to)
    enabled = fields.Boolean("Is Enabled", default=True)

    def action_sync(self):
        date_from_tp = int(self.date_from.timestamp())
        modifiedBegin = date_from_tp
        modifiedEnd = int(self.date_to.timestamp())
        seconds_in_3days = 3 * 24 * 3600

        # khoảng thời gian tối đa trong 1 lần gọi api = 3 days
        while modifiedEnd >= date_from_tp:
            modifiedBegin = modifiedEnd - seconds_in_3days
            if modifiedBegin < date_from_tp:
                modifiedBegin = date_from_tp
            time.sleep(1)
            self.env['jst.product.template'].sudo().action_sync_jst_products(modifiedBegin, modifiedEnd, self.enabled)
            modifiedEnd = modifiedBegin - 1
