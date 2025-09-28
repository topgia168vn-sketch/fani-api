from odoo import models, fields


class JstLogisticCompany(models.TransientModel):
    _name = 'wizard.sync.jst.logistic.company'
    _description = 'Wizard Sync JST Logistic Company'

    # Basic info from API
    date_from = fields.Datetime("Ngày Bắt đầu")
    date_to = fields.Datetime("Ngày kết thúc")

    def action_sync(self):
        self.env['jst.logistic.company'].action_sync_jst_logistic_companies()
