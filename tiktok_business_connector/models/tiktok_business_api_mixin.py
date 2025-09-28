from datetime import datetime
import requests
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class TiktokBusinessApiMixin(models.AbstractModel):
    """
    Abstract model chứa các method chung để tương tác với TikTok Business API
    """
    _name = 'tiktok.business.api.mixin'
    _description = 'TikTok Business API Mixin'

    def _call_tiktok_api(self, endpoint, access_token, method='GET', data=None, params=None):
        """
        Gọi TikTok Business API
        
        Args:
            endpoint (str): API endpoint (không bao gồm base URL)
            method (str): HTTP method ('GET', 'POST', 'PUT', 'DELETE')
            data (dict): Data để gửi trong body (cho POST/PUT)
            params (dict): Query parameters (cho GET)
        
        Returns:
            dict: Dữ liệu trả về từ API
        """
        base_url = 'https://business-api.tiktok.com/open_api/v1.3'
        url = f"{base_url}/{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'Access-Token': access_token
        }
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, params=params)
            else:
                raise UserError(_('Tiktok Marketing API: Method không được hỗ trợ: %s') % method)
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') != 0:
                error_message = result.get('message', 'Unknown error')
                error_code = result.get('code', 'Unknown')
                _logger.error(f"Tiktok Marketing API {url}: Lỗi Code: {error_code} - {error_message}")
                raise UserError(_('Tiktok Marketing API %s: Lỗi Code: %s - %s') % (url, error_code, error_message))
            
            return result.get('data', {})
            
        except requests.exceptions.RequestException as e:
            _logger.error(f"Tiktok Marketing API {url}: Lỗi khi gọi TikTok API: {str(e)}")
            raise UserError(_('Tiktok Marketing API %s: Lỗi khi gọi TikTok API: %s') % (url, str(e)))
        except Exception as e:
            _logger.error(f"Tiktok Marketing API {url}: Unexpected error calling TikTok API: {str(e)}")
            raise UserError(_('Tiktok Marketing API %s: Lỗi không mong muốn: %s') % (url, str(e)))

    def _get_tiktok_config(self):
        """Lấy cấu hình TikTok từ settings"""
        Config = self.env['ir.config_parameter'].sudo()
        return {
            'app_id': Config.get_param('tiktok_business.app_id'),
            'client_secret': Config.get_param('tiktok_business.client_secret')
        }

    def _convert_timestamp_to_datetime(self, dt_string):
        """
        Convert datetime string to Datetime object
        Args:
            dt_string: datetime string
        Returns:
            Datetime object
        """

        if not dt_string: # '2025-06-15 12:27:17'
            return False
        try:
            # Convert datetime string to Datetime object
            return datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError) as e:
            return False

    def _convert_array_to_text(self, array_data):
        """Convert array sang Text field"""
        return json.dumps(array_data)

    def _convert_string_to_float(self, string_data):
        """Convert string sang Float field"""
        try:
            return float(string_data)
        except (ValueError, TypeError) as e:
            return False
