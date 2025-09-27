from datetime import datetime, timedelta
from urllib.parse import urlencode

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TaLazadaConfig(models.Model):
    _name = 'ta.lazada.config'
    _description = 'Lazada Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char('Configuration Name', required=True)
    active = fields.Boolean('Active', default=True)
    
    # API Configuration
    app_key = fields.Char('App Key', required=True, help='Lazada App Key')
    app_secret = fields.Char('App Secret', required=True, help='Lazada App Secret')
    
    # Store Configuration
    country_code = fields.Selection([
        ('SG', 'Singapore'),
        ('MY', 'Malaysia'),
        ('TH', 'Thailand'),
        ('PH', 'Philippines'),
        ('ID', 'Indonesia'),
        ('VN', 'Vietnam'),
    ], string='Country', required=True, default='VN')
    
    # ISV Configuration
    isv_company_name = fields.Char('ISV Company Name', help='Company name for ISV account')
    isv_contact_email = fields.Char('ISV Contact Email', help='Contact email for ISV account')
    isv_contact_phone = fields.Char('ISV Contact Phone', help='Contact phone for ISV account')
    
    # API URLs
    api_url = fields.Char('API URL', compute='_compute_api_url', store=True)
    
    # OAuth URLs
    auth_url = fields.Char('Auth URL', compute='_compute_auth_url', store=True)
    token_url = fields.Char('Token URL', compute='_compute_token_url', store=True)
    
    # Related records
    authorized_shops = fields.One2many('ta.lazada.authorized.shop', 'isv_config_id', 'Authorized Shops')
    
    @api.depends('country_code')
    def _compute_api_url(self):
        """Compute API URL based on country"""
        api_urls = {
            'SG': 'https://api.lazada.sg/rest',
            'MY': 'https://api.lazada.com.my/rest',
            'TH': 'https://api.lazada.co.th/rest',
            'PH': 'https://api.lazada.com.ph/rest',
            'ID': 'https://api.lazada.co.id/rest',
            'VN': 'https://api.lazada.vn/rest',
        }
        for record in self:
            record.api_url = api_urls.get(record.country_code, 'https://api.lazada.vn/rest')
    
    @api.depends('country_code')
    def _compute_auth_url(self):
        """Compute Auth URL based on country"""
        auth_urls = {
            'SG': 'https://auth.lazada.com/oauth/authorize',
            'MY': 'https://auth.lazada.com.my/oauth/authorize',
            'TH': 'https://auth.lazada.co.th/oauth/authorize',
            'PH': 'https://auth.lazada.com.ph/oauth/authorize',
            'ID': 'https://auth.lazada.co.id/oauth/authorize',
            'VN': 'https://auth.lazada.com/oauth/authorize',
        }
        for record in self:
            record.auth_url = auth_urls.get(record.country_code, 'https://auth.lazada.com/oauth/authorize')
    
    @api.depends('country_code')
    def _compute_token_url(self):
        """Compute Token URL based on country"""
        token_urls = {
            'SG': 'https://auth.lazada.com/rest/auth/token/create',
            'MY': 'https://auth.lazada.com.my/rest/auth/token/create',
            'TH': 'https://auth.lazada.co.th/rest/auth/token/create',
            'PH': 'https://auth.lazada.com.ph/rest/auth/token/create',
            'ID': 'https://auth.lazada.co.id/rest/auth/token/create',
            'VN': 'https://auth.lazada.com/rest/auth/token/create',
        }
        for record in self:
            record.token_url = token_urls.get(record.country_code, 'https://auth.lazada.com/rest/auth/token/create')
    
    def action_ta_lazada_authorized_shop(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Authorized Shops',
            'res_model': 'ta.lazada.authorized.shop',
            'view_mode': 'list,form',
            'context': {'search_default_isv_config_id': self.id}
        }
    
    def get_auth_url(self):
        """Get authorization URL for OAuth flow"""
        self.ensure_one()
        
        if not self.app_key:
            raise ValidationError(_('App Key is required. Please configure your Lazada App Key first.'))
        
        # Force refresh computed fields to get updated URLs
        self._compute_auth_url()
        self._compute_api_url()
        self._compute_token_url()

        params = {
            'response_type': 'code',
            'redirect_uri': self._get_redirect_uri(),
            'client_id': self.app_key,
            'state': f'config_{self.id}',
        }
        
        auth_url = f"{self.auth_url}?{urlencode(params)}"
        return auth_url
    
    def _get_redirect_uri(self):
        """Get redirect URI for OAuth"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/ta_lazada/oauth/callback"