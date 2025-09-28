from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    lark_app_id = fields.Char(string='Lark App ID', config_parameter='lark.app.id')
    lark_app_secret = fields.Char(string='Lark App Secret', config_parameter='lark.app.secret')
    lark_app_access_token = fields.Char(string='Lark App Access Token', readonly=True, config_parameter='lark.app.access.token')
    lark_app_access_token_expiry = fields.Datetime(string='Lark App Token Expiry', readonly=True, config_parameter='lark.app.access.token.expiry')

    def get_app_access_token(self):
        self.env['lark.api']._get_app_access_token()
