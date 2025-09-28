from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import logging

_logger = logging.getLogger(__name__)


class WizardSyncTiktokAdvertiser(models.TransientModel):
    _name = 'wizard.sync.tiktok.advertiser'
    _description = 'Wizard Sync TikTok Advertiser'


    def _default_advertiser_ids(self):
        return self.env['ir.config_parameter'].sudo().get_param('tiktok_business.advertisers', '[]')

    business_account_ids = fields.Many2many(
        'tiktok.bussiness.account',
        string='Business Accounts',
        help='Những tài khoản doanh nghiệp mà bạn muốn đồng bộ tài khoản quảng cáo'
    )

    def action_sync(self):
        """Thực hiện sync advertisers"""
        check_access_token = self.business_account_ids.filtered(lambda c: not c.access_token)[:1]
        if check_access_token:
            raise UserError(_("Vui lòng ủy quyền để lấy 'Access Token' cho tài khoản doanh nghiệp %s!") % check_access_token.name)
        self.business_account_ids._sync_advertisers()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Synced advertisers successfully!'),
                'type': 'success',
            }
        }
