# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import requests
import time
import hashlib
import hmac
from datetime import datetime, timedelta


class TaLazadaAuthorizedShop(models.Model):
    _name = 'ta.lazada.authorized.shop'
    _description = 'Lazada Authorized Shop'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'shop_name'

    # Basic Information
    shop_name = fields.Char('Shop Name', required=True)
    seller_id = fields.Char('Seller ID', required=True)
    user_id = fields.Char('User ID')
    shop_url = fields.Char('Shop URL')
    country_code = fields.Selection([
        ('SG', 'Singapore'),
        ('MY', 'Malaysia'),
        ('TH', 'Thailand'),
        ('PH', 'Philippines'),
        ('ID', 'Indonesia'),
        ('VN', 'Vietnam'),
    ], string='Country', required=True, default='VN')
    account = fields.Char('Account')
    
    # ISV Configuration
    isv_config_id = fields.Many2one('ta.lazada.config', 'ISV Configuration', required=True)
    
    # Related records
    products = fields.One2many('ta.lazada.product', 'authorized_shop_id', 'Products')
    orders = fields.One2many('ta.lazada.order', 'authorized_shop_id', 'Orders')
    campaigns = fields.One2many('ta.lazada.campaign', 'authorized_shop_id', 'Campaigns')
    categories = fields.One2many('ta.lazada.category', 'authorized_shop_id', 'Categories')
    warehouses = fields.One2many('ta.lazada.warehouse', 'authorized_shop_id', 'Warehouses')
    
    # Authorization Details
    access_token = fields.Text('Access Token')
    refresh_token = fields.Text('Refresh Token')
    token_expires_at = fields.Datetime('Token Expires At')
    authorization_status = fields.Selection([
        ('pending', 'Pending Authorization'),
        ('authorized', 'Authorized'),
        ('expired', 'Token Expired'),
        ('revoked', 'Revoked'),
        ('error', 'Authorization Error'),
    ], string='Authorization Status', default='pending')
    
    # Dates
    authorized_date = fields.Datetime('Authorized Date')
    revoked_date = fields.Datetime('Revoked Date')
    last_sync_date = fields.Datetime('Last Sync Date')
    
    # Shop Statistics
    total_products = fields.Integer('Total Products', compute='_compute_shop_statistics')
    total_orders = fields.Integer('Total Orders', compute='_compute_shop_statistics')
    total_campaigns = fields.Integer('Total Campaigns', compute='_compute_shop_statistics')
    total_warehouses = fields.Integer('Total Warehouses', compute='_compute_shop_statistics')
    total_revenue = fields.Float('Total Revenue', compute='_compute_shop_statistics')
    
    # Sync Configuration
    auto_sync = fields.Boolean('Auto Sync', default=True)
    sync_interval = fields.Integer('Sync Interval (minutes)', default=30)
    
    # Order Sync Configuration
    order_sync_created_after = fields.Datetime('Sync Orders Created After', required=True,
                                              default=lambda self: fields.Datetime.now() - timedelta(days=30),
                                              help='Only sync orders created after this date')
    # Campaign Sync Configuration (for searchCampaignList)
    campaign_biz_code = fields.Char('Campaign Biz Code', default='sponsoredSearch',
                                    help="Which advertisement solution to query. Example: sponsoredSearch")
    campaign_start_date = fields.Date('Campaign Start Date', default=lambda self: fields.Date.today() - timedelta(days=30))
    campaign_end_date = fields.Date('Campaign End Date', default=lambda self: fields.Date.today())
    campaign_page_no = fields.Integer('Campaign Page Number', default=1)
    campaign_page_size = fields.Integer('Campaign Page Size', default=50)
    
    # Warehouse Sync Configuration (for /fbl/warehouses/get)
    warehouse_country_code = fields.Selection([
        ('SG', 'Singapore'),
        ('MY', 'Malaysia'),
        ('TH', 'Thailand'),
        ('PH', 'Philippines'),
        ('ID', 'Indonesia'),
        ('VN', 'Vietnam'),
    ], string='Warehouse Country Code', default='VN', help='Country code for warehouse sync')
    warehouse_page_size = fields.Integer('Warehouse Page Size', default=20, help='Maximum number of results per page for warehouse sync')
    
    _sql_constraints = [
        ('seller_isv_unique', 'unique(seller_id, isv_config_id)', 'Seller ID must be unique per ISV configuration'),
    ]
    
    @api.depends('products', 'orders', 'campaigns', 'warehouses')
    def _compute_shop_statistics(self):
        """Compute shop statistics"""
        for record in self:
            record.total_products = len(record.products)
            record.total_orders = len(record.orders)
            record.total_revenue = sum(record.orders.mapped('order_amount'))
            record.total_campaigns = len(record.campaigns)
            record.total_warehouses = len(record.warehouses)
    
    def get_authorization_url(self):
        """Get authorization URL for this shop"""
        self.ensure_one()
        
        # Get base auth URL from config
        auth_url = self.isv_config_id.get_auth_url()
        
        state = f'config_{self.isv_config_id.id}'
        
        if '?' in auth_url:
            auth_url += f'&state={state}'
        else:
            auth_url += f'?state={state}'
        
        return auth_url
    
    def authorize_shop(self):
        """Start authorization process for this shop"""
        self.ensure_one()
        
        if self.authorization_status == 'authorized':
            raise ValidationError(_('Shop is already authorized'))
        
        # Generate authorization URL
        auth_url = self.get_authorization_url()
        
        # Open authorization URL
        return {
            'type': 'ir.actions.act_url',
            'url': auth_url,
            'target': 'new',
        }
    
    def exchange_code_for_token(self, auth_code):
        """Exchange authorization code for access token"""
        self.ensure_one()
        
        if not self.isv_config_id.app_key or not self.isv_config_id.app_secret:
            raise ValidationError(_('App Key and App Secret are required for authentication'))
        
        # Prepare token exchange parameters
        params = {
            'code': auth_code,
            'app_key': self.isv_config_id.app_key.strip().lstrip('+'),
            'timestamp': str(int(time.time() * 1000)),
            'sign_method': 'sha256',
        }
        
        # Generate signature
        signature = self._sign(self.isv_config_id.app_secret, '/auth/token/create', params)
        params['sign'] = signature
        
        try:
            response = self._make_lazada_request(self.isv_config_id.token_url, params, 'POST')
            
            if response.get('code') == '0':
                # Get seller info first
                country_user_info = response.get('country_user_info')
                for shop in country_user_info:
                    api_seller_id = shop.get('short_code')
                    # Check if another shop with same seller_id already exists
                    if api_seller_id:
                        existing_shop = self.env['ta.lazada.authorized.shop'].search([
                            ('isv_config_id', '=', self.isv_config_id.id),
                            ('seller_id', '=', api_seller_id),
                        ], limit=1)
                        
                        if existing_shop:
                            # Update existing shop instead of current one
                            existing_shop.write({
                                'authorization_status': 'authorized',
                                'authorized_date': fields.Datetime.now(),
                                'access_token': response.get('access_token'),
                                'refresh_token': response.get('refresh_token'),
                                'token_expires_at': fields.Datetime.now() + timedelta(seconds=response.get('expires_in', 3600)),
                                'user_id': shop.get('user_id'),
                                'account': response.get('account'),
                            })
                        return existing_shop
                return False
            else:
                error_msg = response.get('message', 'Unknown error during token exchange')
                raise ValidationError(_('Token exchange failed: %s') % error_msg)
                
        except Exception as e:
            raise ValidationError(_('Token exchange failed: %s') % str(e))
    
    def revoke_authorization(self):
        """Revoke authorization for this shop"""
        self.ensure_one()
        
        if self.authorization_status != 'authorized':
            raise ValidationError(_('Shop is not authorized'))
        # Handle revoke locally: clear tokens and mark as revoked
        self.write({
            'access_token': False,
            'refresh_token': False,
            'token_expires_at': False,
            'authorization_status': 'revoked',
            'revoked_date': fields.Datetime.now(),
        })
        try:
            self.message_post(body=_('Shop authorization revoked and tokens cleared'))
        except:
            pass
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Shop authorization revoked successfully'),
                'type': 'success',
            }
        }
    
    def refresh_access_token(self):
        """Refresh access token for this shop"""
        self.ensure_one()
        
        if not self.refresh_token:
            raise ValidationError(_('No refresh token available'))
        
        try:
            # Lazada refresh token endpoint requires signed params
            url = "https://auth.lazada.com/rest/auth/token/refresh"
            app_key = (self.isv_config_id.app_key or '').strip().lstrip('+')
            app_secret = (self.isv_config_id.app_secret or '').strip()
            # IMPORTANT: api_path used for signature must NOT include '/rest'
            api_path = '/auth/token/refresh'
            base_params = {
                'app_key': app_key,
                'refresh_token': self.refresh_token,
                'sign_method': 'sha256',
                'timestamp': str(int(time.time() * 1000)),
            }
            # Generate signature using the official guide logic
            signature = self._sign(app_secret, api_path, base_params)
            data = {**base_params, 'sign': signature}
            
            # Use common request function
            token_data = self._make_lazada_request(url, data, 'POST', timeout=30)
            
            # Normalize nested data
            data_node = token_data.get('data') if isinstance(token_data, dict) else None
            payload = data_node if isinstance(data_node, dict) else token_data

            if isinstance(payload, dict) and payload.get('access_token'):
                self.access_token = payload['access_token']
                if payload.get('refresh_token'):
                    self.refresh_token = payload['refresh_token']
                
                # Set default expiry to 3600 seconds (1 hour) if not provided by API
                expires_in = payload.get('expires_in', 3600)
                self.token_expires_at = fields.Datetime.now() + timedelta(seconds=expires_in)
                
                self.authorization_status = 'authorized'
                self.last_sync_date = fields.Datetime.now()
                
                self.message_post(body=_('Access token refreshed successfully'))
            else:
                raise Exception(token_data.get('message', 'Failed to refresh token'))
                
        except Exception as e:
            self.authorization_status = 'error'
            self.message_post(body=_('Failed to refresh access token: %s') % str(e))
            raise ValidationError(_('Failed to refresh access token: %s') % str(e))
    
    def sync_categories(self):
        """Sync categories for this shop"""
        self.ensure_one()
        if self.authorization_status != 'authorized':
            raise ValidationError(_('Shop is not authorized'))
        
        # Check if token is expired
        if self.token_expires_at and self.token_expires_at < fields.Datetime.now():
            self.refresh_access_token()
        
        try:
            self._sync_categories()
            self.last_sync_date = fields.Datetime.now()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Categories synced successfully for shop %s') % self.shop_name,
                    'type': 'success',
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Failed to sync categories: %s') % str(e),
                    'type': 'danger',
                }
            }
    
    def _sync_categories(self):
        """Sync categories for this shop"""
        self.ensure_one()
        try:
            if not self.access_token:
                return
            
            # Call the category import method for this specific shop
            categories = self.env['ta.lazada.category']
            categories.import_from_lazada_for_shop(self)
            
        except Exception as e:
            raise
    
    def sync_products(self):
        """Sync only products for this shop"""
        self.ensure_one()
        if self.authorization_status != 'authorized':
            raise ValidationError(_('Shop is not authorized'))
        
        # Check if token is expired
        if self.token_expires_at and self.token_expires_at < fields.Datetime.now():
            self.refresh_access_token()
        
        try:
            self._sync_products()
            self.last_sync_date = fields.Datetime.now()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Products synced successfully for shop %s') % self.shop_name,
                    'type': 'success',
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Failed to sync products: %s') % str(e),
                    'type': 'danger',
                }
            }
    
    def sync_orders(self):
        """Sync only orders for this shop"""
        self.ensure_one()
        if self.authorization_status != 'authorized':
            raise ValidationError(_('Shop is not authorized'))
        
        # Check if token is expired
        if self.token_expires_at and self.token_expires_at < fields.Datetime.now():
            self.refresh_access_token()
        
        try:
            self._sync_orders()
            self.last_sync_date = fields.Datetime.now()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Orders synced successfully for shop %s') % self.shop_name,
                    'type': 'success',
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Failed to sync orders: %s') % str(e),
                    'type': 'danger',
                }
            }
    
    def _sync_products(self):
        """Sync products for this shop"""
        self.ensure_one()
        try:
            if not self.access_token:
                return
            
            # Call the product import method for this specific shop
            products = self.env['ta.lazada.product']
            products.import_from_lazada_for_shop(self)
            
        except Exception as e:
            raise
    
    def _sync_orders(self):
        """Sync orders for this shop"""
        self.ensure_one()
        try:
            if not self.access_token:
                return
            
            # Call the order import method for this specific shop
            orders = self.env['ta.lazada.order']
            orders.import_from_lazada_for_shop(self)
            
        except Exception as e:
            raise
    
    def _make_api_request(self, endpoint, params=None, method='GET', files=None):
        """Make API request using shop's access token"""
        self.ensure_one()
        
        # Validate ISV config
        if not self.isv_config_id:
            raise ValidationError(_('ISV Configuration is required'))
        
        if not self.isv_config_id.app_key:
            raise ValidationError(_('App Key is required in ISV Configuration. Please configure your Lazada App Key first.'))
        
        if not self.isv_config_id.app_secret:
            raise ValidationError(_('App Secret is required in ISV Configuration. Please configure your Lazada App Secret first.'))
        
        if not self.access_token:
            raise ValidationError(_('Access token is required for this shop'))
        
        # Check if token is expired
        if self.token_expires_at and self.token_expires_at < fields.Datetime.now():
            self.refresh_access_token()
        
        url = f"{self.isv_config_id.api_url}{endpoint}"
        
        # Prepare parameters
        if params is None:
            params = {}
        
        params.update({
            'access_token': self.access_token,
            'app_key': self.isv_config_id.app_key.strip().lstrip('+'),  # Remove leading + and whitespace
            'timestamp': str(int(time.time() * 1000)),
            'sign_method': 'sha256',
        })
        # offset = False
        # if params.get('offset', False):
        #     offset = params.get('offset')
        #     params['offset'] = 0
        if params.get('sign', False):
            params.pop('sign')
        # Generate signature using the same method as token exchange
        signature = self._sign(self.isv_config_id.app_secret, endpoint, params)
        params['sign'] = signature
        # if offset:
        #     params['offset'] = offset
        # Use common request function
        return self._make_lazada_request(url, params, method, files, 30)
    
    def _sign(self, secret, api, parameters):
        """Sign function exactly as in the official guide"""
        #===========================================================================
        # @param secret
        # @param parameters
        #===========================================================================
        sort_dict = sorted(parameters)
        
        parameters_str = "%s%s" % (api,
            str().join('%s%s' % (key, parameters[key]) for key in sort_dict))

        h = hmac.new(secret.encode(encoding="utf-8"), parameters_str.encode(encoding="utf-8"), digestmod=hashlib.sha256)

        return h.hexdigest().upper()
    
    def _make_lazada_request(self, url, params, method='GET', files=None, timeout=None):
        """Common function to make Lazada API requests"""
        if timeout is None:
            timeout = 30
        
        try:
            # Use the pattern you suggested: direct parameter passing
            if method.upper() == 'POST' or files is not None:
                r = requests.post(url, params, files=files, timeout=timeout)
            else:
                r = requests.get(url, params, timeout=timeout)
            
            r.raise_for_status()
            return r.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
    
    def sync_campaign(self):
        """Sync only campaigns for this shop (public action)."""
        self.ensure_one()
        if self.authorization_status != 'authorized':
            raise ValidationError(_('Shop is not authorized'))
        
        # Check if token is expired
        if self.token_expires_at and self.token_expires_at < fields.Datetime.now():
            self.refresh_access_token()
        
        try:
            self._sync_campaign()
            self.last_sync_date = fields.Datetime.now()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Campaigns synced successfully for shop %s') % self.shop_name,
                    'type': 'success',
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Failed to sync campaigns: %s') % str(e),
                    'type': 'danger',
                }
            }

    def _sync_campaign(self):
        """Sync campaigns for this shop (internal), delegates to campaign model."""
        self.ensure_one()
        try:
            if not self.access_token:
                return
            campaigns = self.env['ta.lazada.campaign']
            campaigns.import_from_lazada_for_shop(self)
        except Exception as e:
            raise
    
    def sync_warehouses(self):
        """Sync only warehouses for this shop"""
        self.ensure_one()
        if self.authorization_status != 'authorized':
            raise ValidationError(_('Shop is not authorized'))
        
        # Check if token is expired
        if self.token_expires_at and self.token_expires_at < fields.Datetime.now():
            self.refresh_access_token()
        
        try:
            self._sync_warehouses()
            self.last_sync_date = fields.Datetime.now()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Warehouses synced successfully for shop %s') % self.shop_name,
                    'type': 'success',
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Failed to sync warehouses: %s') % str(e),
                    'type': 'danger',
                }
            }

    def _sync_warehouses(self):
        """Sync warehouses for this shop"""
        self.ensure_one()
        try:
            if not self.access_token:
                return
            
            # Call the warehouse import method for this specific shop
            warehouses = self.env['ta.lazada.warehouse']
            warehouses.import_from_lazada_for_shop(self)
            
        except Exception as e:
            raise
    
    def action_view_products(self):
        """Action to view products for this shop"""
        self.ensure_one()
        return {
            'name': _('Products'),
            'type': 'ir.actions.act_window',
            'res_model': 'ta.lazada.product',
            'view_mode': 'list,form',
            'domain': [('authorized_shop_id', '=', self.id)],
            'context': {
                'default_authorized_shop_id': self.id,
                'search_default_authorized_shop_id': self.id,
            },
        }
    
    def action_view_orders(self):
        """Action to view orders for this shop"""
        self.ensure_one()
        return {
            'name': _('Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'ta.lazada.order',
            'view_mode': 'list,form',
            'domain': [('authorized_shop_id', '=', self.id)],
            'context': {
                'default_authorized_shop_id': self.id,
                'search_default_authorized_shop_id': self.id,
            },
        }
    
    def action_view_campaigns(self):
        """Action to view campaigns for this shop"""
        self.ensure_one()
        return {
            'name': _('Campaigns'),
            'type': 'ir.actions.act_window',
            'res_model': 'ta.lazada.campaign',
            'view_mode': 'list,form',
            'domain': [('authorized_shop_id', '=', self.id)],
            'context': {
                'default_authorized_shop_id': self.id,
                'search_default_authorized_shop_id': self.id,
            },
        }
    
    def action_view_warehouses(self):
        """Action to view warehouses for this shop"""
        self.ensure_one()
        return {
            'name': _('Warehouses'),
            'type': 'ir.actions.act_window',
            'res_model': 'ta.lazada.warehouse',
            'view_mode': 'list,form',
            'domain': [('authorized_shop_id', '=', self.id)],
            'context': {
                'default_authorized_shop_id': self.id,
                'search_default_authorized_shop_id': self.id,
            },
        }