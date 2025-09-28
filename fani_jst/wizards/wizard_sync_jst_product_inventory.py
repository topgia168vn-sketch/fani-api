from datetime import timedelta
from odoo import models, fields


class JstProductInventory(models.TransientModel):
    _name = 'wizard.sync.jst.product.inventory'
    _description = 'Wizard Sync JST Product Inventory'

    def _default_date_from(self):
        return fields.Datetime.now() - timedelta(days=1)
    def _default_date_to(self):
        return fields.Datetime.now()

    # Basic info from API
    date_from = fields.Datetime("Ngày Bắt đầu", default=_default_date_from)
    date_to = fields.Datetime("Ngày kết thúc", default=_default_date_to)

    def action_sync(self):
        modifiedBegin = int(self.date_from.timestamp())
        modifiedEnd = int(self.date_to.timestamp())
        self.env['jst.product.inventory'].action_sync_jst_product_inventory(modifiedBegin, modifiedEnd)
