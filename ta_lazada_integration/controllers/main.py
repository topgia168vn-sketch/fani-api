from odoo import http, _
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class TaLazadaController(http.Controller):
    
    @http.route('/ta_lazada/oauth/callback', type='http', auth='public', methods=['GET'])
    def oauth_callback(self, **kwargs):
        """OAuth callback for shop authorization"""
        try:
            code = kwargs.get('code') or request.params.get('code')
            state = kwargs.get('state') or request.params.get('state')
            
            if not code or not state:
                return request.render('ta_lazada_integration.oauth_error', {
                    'error': 'Missing authorization code or state'
                })
            
            if not state.startswith('config_'):
                return request.render('ta_lazada_integration.oauth_error', {
                    'error': 'Invalid state parameter format'
                })
            state_content = state[7:]
            config_id = state_content
            
            # Get configuration
            config = request.env['ta.lazada.config'].browse(int(config_id))
            if not config.exists():
                return request.render('ta_lazada_integration.oauth_error', {
                    'error': 'Configuration not found'
                })
            
            # Process authorization callback
            try:
                # Find or create authorized shop for token exchange
                authorized_shop = request.env['ta.lazada.authorized.shop'].search([
                    ('isv_config_id', '=', config.id)
                ], limit=1)
                
                if not authorized_shop:
                    # Create new authorized shop if none exists
                    authorized_shop = request.env['ta.lazada.authorized.shop'].create({
                        'isv_config_id': config.id,
                        'authorization_status': 'pending',
                    })
                
                # Exchange code for token using shop method
                # This will also update seller_id from API response
                final_shop = authorized_shop.exchange_code_for_token(code)
                
                return request.render('ta_lazada_integration.oauth_success', {
                    'shop_name': final_shop.shop_name or 'Shop',
                    'config_name': config.name
                })
            except Exception as e:
                return request.render('ta_lazada_integration.oauth_error', {
                    'error': f'Authorization failed: {str(e)}'
                })
            
        except Exception as e:
            _logger.error(f"OAuth callback error: {str(e)}")
            return request.render('ta_lazada_integration.oauth_error', {
                'error': str(e)
            })
