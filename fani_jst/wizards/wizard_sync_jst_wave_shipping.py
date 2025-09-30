from odoo import models, fields, _


class WizardSyncJSTWaveShipping(models.TransientModel):
    _name = 'wizard.sync.jst.wave.shipping'
    _description = 'Wizard Sync JST Wave Shipping'

    def _default_date_from(self):
        return fields.Datetime.now()
    def _default_date_to(self):
        return fields.Datetime.now()

    # Basic info from API
    date_from = fields.Datetime("Ngày Bắt đầu", default=_default_date_from)
    date_to = fields.Datetime("Ngày kết thúc", default=_default_date_to)

    def action_sync(self):
        self.ensure_one()
        modifiedBegin = int(self.date_from.timestamp())
        modifiedEnd = int(self.date_to.timestamp())

        requestModel = {
            "BeginTime": modifiedBegin,
            "EndTime": modifiedEnd
        }
        self.env['jst.wave.shipping']._sync_wave_shippings(requestModel)
