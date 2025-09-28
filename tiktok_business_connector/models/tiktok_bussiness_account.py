from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import json
_logger = logging.getLogger(__name__)


class TiktokBussinessAccount(models.Model):
    _name = 'tiktok.bussiness.account'
    _description = 'TikTok Bussiness Account'
    _inherit = ['tiktok.business.api.mixin']

    name = fields.Char(string='Name')

    access_token = fields.Char(
        string='TikTok Access Token',
        groups='base.group_system',
        help='Access Token để truy cập TikTok Business API'
    )
    scope = fields.Text(string='Scope')
    advertiser_ids = fields.Text(string='Advertiser ID')
    # 1 business account có thể có nhiều advertisers
    advertiser_ids_synced = fields.Many2many(
        'tiktok.advertiser',
        string='Advertiser IDs Synced',
        readonly=True
    )

    def action_tiktok_authorize(self):
        """Tạo URL authorization để người dùng đăng nhập TikTok"""
        self.ensure_one()

        config = self._get_tiktok_config()
        tiktok_app_id = config.get('app_id')
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        # Loại bỏ dấu / ở cuối nếu có
        base_url = base_url.rstrip('/')
        tiktok_redirect_uri = f"{base_url}/tiktok/business/callback"

        if not tiktok_app_id:
            raise UserError(_('Vui lòng nhập TikTok App ID trước khi ủy quyền.'))
        
        # Tạo authorization URL theo format TikTok Business API
        state = f"auth_account:{self.id}"
        auth_url = (
            f"https://business-api.tiktok.com/portal/auth"
            f"?app_id={tiktok_app_id}"
            f"&state={state}"
            f"&redirect_uri={tiktok_redirect_uri}"
        )
        
        return {
            'type': 'ir.actions.act_url',
            'url': auth_url,
            'target': 'new',
        }

    def _update_auth_data(self, token_data):
        """
        Lưu token và thông tin khác tài khoản vào business account sau khi auth
        """
        try:
            # Lưu access token
            access_token = token_data.get('access_token')
            scope = token_data.get('scope', [])
            advertiser_ids = token_data.get('advertiser_ids', [])

            self.write({
                'access_token': access_token,
                'scope': json.dumps(scope),
                'advertiser_ids': json.dumps(advertiser_ids),
            })

            # Sync advertisers
            if advertiser_ids:
                self.env['tiktok.advertiser'].sync_advertisers(advertiser_ids=advertiser_ids, access_token=access_token)

            _logger.info("Tiktok Marketing API: Tokens and other info saved to business account!")
            
        except Exception as e:
            _logger.error(f"Tiktok Marketing API: Error saving tokens to business account: {str(e)}")
            return None

    def _sync_advertisers(self):
        for business_account in self:
            advertiser_ids = json.loads(business_account.advertiser_ids) if business_account.advertiser_ids else []
            if not advertiser_ids:
                continue

            sync_advertisers = self.env['tiktok.advertiser'].sync_advertisers(advertiser_ids=advertiser_ids, access_token=business_account.sudo().access_token)
            # tạo các liên kết mới
            business_account.write({
                'advertiser_ids_synced': [(6, 0, sync_advertisers.ids)]
            })


    def action_sync_advertisers(self):
        """
        Đồng bộ advertisers của business accounts
        """
        self._sync_advertisers()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Synced advertisers successfully!'),
                'type': 'success',
            }
        }

    # def action_tiktok_disconnect(self):
    # pass