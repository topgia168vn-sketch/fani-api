from odoo import models, fields


class JstShop(models.TransientModel):
    _name = 'wizard.sync.jst.shop'
    _description = 'Wizard Sync JST Shops'

    def _default_date_from(self):
        return fields.Datetime.to_datetime('2020-01-01 00:00:00')
    def _default_date_to(self):
        return fields.Datetime.now()

    # Basic info from API
    date_from = fields.Datetime("Ngày Bắt đầu", default=_default_date_from)
    date_to = fields.Datetime("Ngày kết thúc", default=_default_date_to)

    def action_sync(self):
        modifiedBegin = int(self.date_from.timestamp())
        modifiedEnd = int(self.date_to.timestamp())
        self.env['jst.shop'].action_sync_jst_shops(modifiedBegin, modifiedEnd)
