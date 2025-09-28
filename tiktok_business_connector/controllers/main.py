import logging
import requests
import json
from datetime import datetime, timedelta
from odoo import http, fields
from odoo.http import request
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TiktokBusinessController(http.Controller):

    @http.route('/tiktok/business/callback', type='http', auth='public', methods=['GET'], csrf=False)
    def tiktok_business_callback(self, **kwargs):
        """
        Xử lý callback từ TikTok Business API sau khi authorization
        """
        try:
            # Lấy các tham số từ callback
            code = kwargs.get('auth_code')
            state = kwargs.get('state')
            # _logger.info(f"TikTok callback received: code={code}, state={state}")
            
            # Kiểm tra code và state
            if not code or not state:
                _logger.error("Tiktok Marketing API: Missing code or state in TikTok callback")
                return "TikTok authorization failed: Missing code or state"
                # return self._render_error_page("missing_params", "Missing authorization code or state")
            
            # Xác thực state
            state_id = state.split(':')[1]
            business_account = request.env['tiktok.bussiness.account'].sudo().search([('id', '=', state_id)], limit=1)
            if not business_account:
                _logger.error(f"Tiktok Marketing API: Không xác định được state: {state_id}")
                return "TikTok authorization failed: Không xác định được state: {state_id}"
            
            # Lấy thông tin cấu hình App
            app_id = request.env['ir.config_parameter'].sudo().get_param('tiktok_business.app_id')
            client_secret = request.env['ir.config_parameter'].sudo().get_param('tiktok_business.client_secret')
            
            if not all([app_id, client_secret]):
                _logger.error("Tiktok Marketing API: Missing TikTok configuration parameters")
                return "TikTok authorization failed: Missing TikTok configuration"
                # return self._render_error_page("missing_config", "Missing TikTok configuration")
            
            # Trao đổi authorization code lấy access token
            token_data = self._exchange_code_for_token(code, app_id, client_secret)
            
            if token_data:
                # Lưu token vào business account
                business_account.sudo()._update_auth_data(token_data)

                _logger.info("Tiktok Marketing API: TikTok authorization successful, tokens saved")
                return "TikTok authorization successful"
                # return self._render_success_page()
            else:
                return "TikTok authorization failed"
                # return self._render_error_page("token_exchange_failed", "Failed to exchange code for token")
                
        except Exception as e:
            _logger.error(f"Tiktok Marketing API: Error in TikTok callback: {str(e)}")
            return "TikTok authorization failed"
            # return self._render_error_page("callback_error", str(e))
    
    def _exchange_code_for_token(self, code, app_id, client_secret):
        """
        Trao đổi authorization code lấy access token
        """
        try:
            url = "https://business-api.tiktok.com/open_api/v1.3/oauth2/access_token/"
            
            data = {
                'app_id': app_id,
                'secret': client_secret,
                'auth_code': code
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            _logger.info(f"Tiktok Marketing API: Exchanging code for token: {url}")
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                _logger.info(f"Tiktok Marketing API: Token exchange response: {result}")
                
                if result.get('code') == 0:
                    return result.get('data', {})
                else:
                    _logger.error(f"Tiktok Marketing API: TikTok API error: {result.get('message', 'Unknown error')}")
                    return None
            else:
                _logger.error(f"Tiktok Marketing API: HTTP error {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            _logger.error(f"Tiktok Marketing API: Request error during token exchange: {str(e)}")
            return None
        except Exception as e:
            _logger.error(f"Tiktok Marketing API: Error during token exchange: {str(e)}")
            return None