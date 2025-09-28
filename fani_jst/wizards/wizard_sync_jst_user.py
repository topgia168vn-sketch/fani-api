from odoo import models, fields


class JstUser(models.TransientModel):
    _name = 'wizard.sync.jst.user'
    _description = 'Wizard Sync JST User'

    # Basic info from API
    date_from = fields.Datetime("Ngày Bắt đầu")
    date_to = fields.Datetime("Ngày kết thúc")

    def action_sync(self):
        """
        Sync JST User
        """
        self.env['jst.user'].action_sync_jst_users()
