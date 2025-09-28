# -*- coding: utf-8 -*-

import requests
import time
import hmac
import hashlib
import base64
import urllib.parse
import logging
from dateutil.relativedelta import relativedelta


from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class YonsuiteApi(models.TransientModel):
    _name = 'yonsuite.api'
    _description = 'YonSuite API Service'

    def _generate_signature(self, params, app_secret):
        """
        Tạo signature theo logic SignHelper.sign() trong Java
        """
        # Sắp xếp key theo alphabet (TreeMap behavior trong Java)
        sorted_keys = sorted(params.keys())

        # Nối chuỗi: tên + giá trị (giống StringBuilder trong Java)
        param_string = ""
        for key in sorted_keys:
            param_string += key + str(params[key])

        # Tính HMAC-SHA256 (giống Mac.getInstance("HmacSHA256") trong Java)
        hmac_obj = hmac.new(
            app_secret.encode('utf-8'),
            param_string.encode('utf-8'),
            hashlib.sha256
        )
        hmac_binary = hmac_obj.digest()

        # Base64 encode (giống Base64.getEncoder().encodeToString() trong Java)
        base64_encoded = base64.b64encode(hmac_binary).decode('utf-8')

        # URLEncode với UTF-8 (giống URLEncoder.encode(base64String, "UTF-8") trong Java)
        signature = urllib.parse.quote(base64_encoded, encoding='utf-8')
        return signature

    def get_access_token(self):
        """
        Lấy access token từ YonSuite API

        Args:
            base_url (str): Base URL của API
            app_key (str): App Key
            app_secret (str): App Secret

        Returns:
            dict: {'access_token': str, 'expire_time': datetime}
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        app_key = config_parameter.get_param('yonsuite_integration.app_key')
        app_secret = config_parameter.get_param('yonsuite_integration.app_secret')

        if not base_url or not app_key or not app_secret:
            raise UserError(_('Please provide Base URL, App Key and App Secret.'))

        try:
            timestamp = str(int(time.time() * 1000))

            params = {
                "appKey": app_key,
                "timestamp": timestamp
            }

            signature = self._generate_signature(params, app_secret)
            params["signature"] = signature

            endpoint = "/open-auth/selfAppAuth/getAccessToken"
            request_url = base_url + endpoint

            query_string = "&".join([f"{key}={value}" for key, value in params.items()])
            full_url = f"{request_url}?{query_string}"

            response = requests.get(full_url, timeout=30)
            response.raise_for_status()

            result = response.json()

            if result.get("code") == "00000":
                data = result.get("data", {})
                access_token = data.get("access_token")
                expire_seconds = data.get("expire", 7200)  # Default 2 hours

                if access_token:
                    expire_time = fields.Datetime.now() + relativedelta(seconds=expire_seconds)
                    _logger.info("YonSuite access token retrieved successfully")
                    config_parameter.set_param('yonsuite_integration.access_token', access_token)
                    config_parameter.set_param('yonsuite_integration.token_expire_time', expire_time)
                    config_parameter.set_param('yonsuite_integration.last_token_refresh', fields.Datetime.now())
                    current_count = int(config_parameter.get_param('yonsuite_integration.refresh_count', '0'))
                    config_parameter.set_param('yonsuite_integration.refresh_count', str(current_count + 1))
                else:
                    raise UserError(_('No access token in response'))
            else:
                code = result.get("code", "UNKNOWN")
                message = result.get("message", "Unknown error")
                raise UserError(_('YonSuite API Error: %s - %s') % (code, message))

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite API request failed: %s", str(e))
            raise UserError(_('Request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite API error: %s", str(e))
            raise UserError(_('Error: %s') % str(e))

    def get_partners_from_api(self, page_index=1, page_size=50):
        """
        Lấy danh sách partners từ YonSuite API với phân trang
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho partners
            endpoint = "/yonbip/digitalModel/merchant/newlist"
            request_url = base_url + endpoint

            # Headers cho request
            headers = {
                'Content-Type': 'application/json'
            }

            # Parameters cho query string (chỉ access_token)
            params = {
                'access_token': access_token
            }

            # Data cho POST request body (pageSize, pageIndex)
            data = {
                'pageIndex': page_index,
                'pageSize': page_size
            }

            # Gửi POST request với data trong body
            response = requests.post(request_url, headers=headers, params=params, json=data, timeout=30)

            # Debug: Log URL và request details
            _logger.info("Partners Request URL: %s", response.url)
            _logger.info("Partners Request params: %s", params)
            _logger.info("Partners Request data: %s", data)

            response.raise_for_status()

            # Parse JSON response
            result = response.json()

            _logger.info("YonSuite Partners API successful - Page %d: %d records", page_index, len(result.get("data", [])))
            _logger.info("Response status code: %s", response.status_code)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite Partners API request failed: %s", str(e))
            raise UserError(_('Partners API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite Partners API error: %s", str(e))
            raise UserError(_('Partners API error: %s') % str(e))

    def _convert_datetime_string(self, datetime_str):
        """
        Chuyển đổi datetime string từ API format sang Odoo format
        """
        if not datetime_str:
            return None

        try:
            # Chuyển đổi từ ISO format sang Odoo format
            if 'T' in datetime_str:
                # Format: 2025-09-18T16:21:54 -> 2025-09-18 16:21:54
                datetime_str = datetime_str.replace('T', ' ')

            # Loại bỏ timezone info nếu có (ví dụ: +07:00, Z)
            if '+' in datetime_str or datetime_str.endswith('Z'):
                datetime_str = datetime_str.split('+')[0].split('Z')[0].strip()

            return fields.Datetime.from_string(datetime_str)
        except Exception as e:
            _logger.warning("Failed to convert datetime string '%s': %s", datetime_str, str(e))
            return None

    def get_products_from_api(self, page_index=1, page_size=50):
        """
        Get products from YonSuite API
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            endpoint = "/yonbip/digitalModel/product/integration/querylist"
            request_url = base_url + endpoint

            headers = {
                'Content-Type': 'application/json'
            }

            params = {
                'access_token': access_token
            }

            data = {
                'pageIndex': page_index,
                'pageSize': page_size
            }

            response = requests.post(request_url, headers=headers, params=params, json=data, timeout=30)

            _logger.info("Products Request URL: %s", response.url)
            _logger.info("Products Request params: %s", params)
            _logger.info("Products Request data: %s", data)

            response.raise_for_status()

            result = response.json()

            _logger.info("YonSuite Products API successful - Page %d: %d records", page_index, len(result.get("data", {}).get("recordList", [])))
            _logger.info("Response status code: %s", response.status_code)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite Products API request failed: %s", str(e))
            raise UserError(_('Products API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite Products API error: %s", str(e))
            raise UserError(_('Products API error: %s') % str(e))

    def get_orders_from_api(self, page_index=1, page_size=50):
        """
        Get orders from YonSuite API
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            endpoint = "/yonbip/sd/quote/salesquotation/list"
            request_url = base_url + endpoint

            headers = {
                'Content-Type': 'application/json'
            }

            params = {
                'access_token': access_token
            }

            data = {
                'pageIndex': page_index,
                'pageSize': page_size
            }

            response = requests.post(request_url, headers=headers, params=params, json=data, timeout=30)

            _logger.info("Orders Request URL: %s", response.url)
            _logger.info("Orders Request params: %s", params)
            _logger.info("Orders Request data: %s", data)

            response.raise_for_status()

            result = response.json()

            _logger.info("YonSuite Orders API successful - Page %d: %d records", page_index, len(result.get("data", {}).get("recordList", [])))
            _logger.info("Response status code: %s", response.status_code)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite Orders API request failed: %s", str(e))
            raise UserError(_('Orders API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite Orders API error: %s", str(e))
            raise UserError(_('Orders API error: %s') % str(e))

    def get_order_detail_from_api(self, order_id):
        """
        Get order detail from YonSuite API
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            endpoint = "/yonbip/sd/quote/salesquotation/detail"
            request_url = base_url + endpoint

            headers = {
                'Content-Type': 'application/json'
            }

            params = {
                'access_token': access_token,
                'id': order_id
            }

            response = requests.get(request_url, headers=headers, params=params, timeout=30)

            response.raise_for_status()

            result = response.json()

            _logger.info("YonSuite Order Detail API successful - Order ID: %s", order_id)
            _logger.info("Response status code: %s", response.status_code)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite Order Detail API request failed: %s", str(e))
            raise UserError(_('Order Detail API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite Order Detail API error: %s", str(e))
            raise UserError(_('Order Detail API error: %s') % str(e))

    def sync_orders_with_pagination(self):
        """
        Sync orders from YonSuite API with pagination
        """

    def get_vendors_from_api(self, page_index=1, page_size=50):
        """
        Lấy danh sách vendors từ YonSuite API với phân trang
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho vendors
            endpoint = "/yonbip/digitalModel/vendor/list"
            request_url = base_url + endpoint

            # Headers cho request
            headers = {
                'Content-Type': 'application/json'
            }

            # Parameters cho query string (chỉ access_token)
            params = {
                'access_token': access_token
            }

            # Data cho POST request body (pageSize, pageIndex)
            data = {
                'pageIndex': page_index,
                'pageSize': page_size
            }

            # Gửi POST request với data trong body
            response = requests.post(request_url, headers=headers, params=params, json=data, timeout=30)

            # Debug: Log URL và request details
            _logger.info("Vendors Request URL: %s", response.url)
            _logger.info("Vendors Request params: %s", params)
            _logger.info("Vendors Request data: %s", data)

            response.raise_for_status()

            # Parse JSON response
            result = response.json()

            _logger.info("YonSuite Vendors API successful - Page %d: %d records", page_index, len(result.get("data", {}).get("recordList", [])))
            _logger.info("Response status code: %s", response.status_code)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite Vendors API request failed: %s", str(e))
            raise UserError(_('Vendors API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite Vendors API error: %s", str(e))
            raise UserError(_('Vendors API error: %s') % str(e))

    def get_brands_from_api(self, page_index=1, page_size=50):
        """
        Lấy danh sách brands từ YonSuite API với phân trang
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho brands
            endpoint = "/yonbip/digitalModel/brand/newlist"
            request_url = base_url + endpoint

            # Headers cho request
            headers = {
                'Content-Type': 'application/json'
            }

            # Parameters cho query string (chỉ access_token)
            params = {
                'access_token': access_token
            }

            # Data cho POST request body (pageSize, pageIndex)
            data = {
                'pageIndex': page_index,
                'pageSize': page_size
            }

            # Gửi POST request với data trong body
            response = requests.post(request_url, headers=headers, params=params, json=data, timeout=30)

            # Debug: Log URL và request details
            _logger.info("Brands Request URL: %s", response.url)
            _logger.info("Brands Request params: %s", params)
            _logger.info("Brands Request data: %s", data)

            response.raise_for_status()

            # Parse JSON response
            result = response.json()

            _logger.info("YonSuite Brands API successful - Page %d: %d records", page_index, len(result.get("data", {})))
            _logger.info("Response status code: %s", response.status_code)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite Brands API request failed: %s", str(e))
            raise UserError(_('Brands API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite Brands API error: %s", str(e))
            raise UserError(_('Brands API error: %s') % str(e))

    def get_units_from_api(self, page_index=1, page_size=50):
        """
        Lấy danh sách units từ YonSuite API với phân trang
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho units
            endpoint = "/yonbip/digitalModel/unit/list"
            request_url = base_url + endpoint

            # Headers cho request
            headers = {
                'Content-Type': 'application/json'
            }

            # Parameters cho query string (chỉ access_token)
            params = {
                'access_token': access_token
            }

            # Data cho POST request body (pageSize, pageIndex)
            data = {
                'pageIndex': page_index,
                'pageSize': page_size
            }

            # Gửi POST request với data trong body
            response = requests.post(request_url, headers=headers, params=params, json=data, timeout=30)

            # Debug: Log URL và request details
            _logger.info("Units Request URL: %s", response.url)
            _logger.info("Units Request params: %s", params)
            _logger.info("Units Request data: %s", data)

            response.raise_for_status()

            # Parse JSON response
            result = response.json()

            _logger.info("YonSuite Units API successful - Page %d: %d records", page_index, len(result.get("data", [])))
            _logger.info("Response status code: %s", response.status_code)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite Units API request failed: %s", str(e))
            raise UserError(_('Units API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite Units API error: %s", str(e))
            raise UserError(_('Units API error: %s') % str(e))

    def get_warehouses_from_api(self, page_index=1, page_size=50):
        """
        Lấy danh sách warehouses từ YonSuite API với phân trang
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho warehouses
            endpoint = "/yonbip/digitalModel/warehouse/list"
            request_url = base_url + endpoint

            # Headers cho request
            headers = {
                'Content-Type': 'application/json'
            }

            # Parameters cho query string (chỉ access_token)
            params = {
                'access_token': access_token
            }

            # Data cho POST request body (pageSize, pageIndex)
            data = {
                'pageIndex': page_index,
                'pageSize': page_size
            }

            # Gửi POST request với data trong body
            response = requests.post(request_url, headers=headers, params=params, json=data, timeout=30)

            # Debug: Log URL và request details
            _logger.info("Warehouses Request URL: %s", response.url)
            _logger.info("Warehouses Request params: %s", params)
            _logger.info("Warehouses Request data: %s", data)

            response.raise_for_status()

            # Parse JSON response
            result = response.json()

            _logger.info("YonSuite Warehouses API successful - Page %d: %d records", page_index, len(result.get("data", {}).get("recordList", [])))
            _logger.info("Response status code: %s", response.status_code)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite Warehouses API request failed: %s", str(e))
            raise UserError(_('Warehouses API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite Warehouses API error: %s", str(e))
            raise UserError(_('Warehouses API error: %s') % str(e))

    def get_warehouse_detail_from_api(self, warehouse_id):
        """
        Lấy chi tiết warehouse từ YonSuite API
        TODO: Kiểm tra phân quyền để thêm được phần kho
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho warehouse detail
            endpoint = "/yonbip/digitalModel/warehouse/detail"
            request_url = base_url + endpoint

            # Headers cho request
            headers = {
                'Content-Type': 'application/json'
            }

            # Parameters cho query string (chỉ access_token)
            params = {
                'access_token': access_token
            }

            # Data cho POST request body (warehouse ID)
            data = {
                'id': warehouse_id
            }

            # Gửi POST request với data trong body
            response = requests.post(request_url, headers=headers, params=params, json=data, timeout=30)

            # Debug: Log URL và request details
            _logger.info("Warehouse Detail Request URL: %s", response.url)
            _logger.info("Warehouse Detail Request params: %s", params)
            _logger.info("Warehouse Detail Request data: %s", data)

            response.raise_for_status()

            # Parse JSON response
            result = response.json()

            _logger.info("YonSuite Warehouse Detail API successful for ID: %s", warehouse_id)
            _logger.info("Response status code: %s", response.status_code)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite Warehouse Detail API request failed: %s", str(e))
            raise UserError(_('Warehouse Detail API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite Warehouse Detail API error: %s", str(e))
            raise UserError(_('Warehouse Detail API error: %s') % str(e))

    def get_carriers_from_api(self, page_index=1, page_size=50):
        """
        Lấy danh sách carriers từ YonSuite API với phân trang
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho carriers
            endpoint = "/yonbip/digitalModel/carrier/list"
            request_url = base_url + endpoint

            # Headers cho request
            headers = {
                'Content-Type': 'application/json'
            }

            # Parameters cho query string (chỉ access_token)
            params = {
                'access_token': access_token
            }

            # Data cho POST request body (pageSize, pageIndex)
            data = {
                'pageIndex': page_index,
                'pageSize': page_size
            }

            # Gửi POST request với data trong body
            response = requests.post(request_url, headers=headers, params=params, json=data, timeout=30)

            # Debug: Log URL và request details
            _logger.info("Carriers Request URL: %s", response.url)
            _logger.info("Carriers Request params: %s", params)
            _logger.info("Carriers Request data: %s", data)

            response.raise_for_status()

            # Parse JSON response
            result = response.json()

            _logger.info("YonSuite Carriers API successful - Page %d: %d records", page_index, len(result.get("data", {}).get("recordList", [])))
            _logger.info("Response status code: %s", response.status_code)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite Carriers API request failed: %s", str(e))
            raise UserError(_('Carriers API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite Carriers API error: %s", str(e))
            raise UserError(_('Carriers API error: %s') % str(e))

    def get_carrier_detail_from_api(self, carrier_id):
        """
        Lấy chi tiết carrier từ YonSuite API
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho carrier detail
            endpoint = "/yonbip/digitalModel/carrier/detail"
            request_url = base_url + endpoint

            # Headers cho request
            headers = {
                'Content-Type': 'application/json'
            }

            # Parameters cho query string (chỉ access_token)
            params = {
                'access_token': access_token
            }

            # Data cho POST request body (carrier ID)
            data = {
                'id': carrier_id
            }

            # Gửi POST request với data trong body
            response = requests.post(request_url, headers=headers, params=params, json=data, timeout=30)

            # Debug: Log URL và request details
            _logger.info("Carrier Detail Request URL: %s", response.url)
            _logger.info("Carrier Detail Request params: %s", params)
            _logger.info("Carrier Detail Request data: %s", data)

            response.raise_for_status()

            # Parse JSON response
            result = response.json()

            _logger.info("YonSuite Carrier Detail API successful for ID: %s", carrier_id)
            _logger.info("Response status code: %s", response.status_code)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite Carrier Detail API request failed: %s", str(e))
            raise UserError(_('Carrier Detail API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite Carrier Detail API error: %s", str(e))
            raise UserError(_('Carrier Detail API error: %s') % str(e))

    def get_staff_from_api(self, page_index=1, page_size=50):
        """
        Lấy danh sách staff từ YonSuite API với phân trang
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho staff
            endpoint = "/yonbip/digitalModel/staff/list"
            request_url = base_url + endpoint

            # Headers cho request
            headers = {
                'Content-Type': 'application/json'
            }

            # Parameters cho query string (chỉ access_token)
            params = {
                'access_token': access_token
            }

            # Data cho POST request body (pageSize, pageIndex)
            data = {
                'pageIndex': page_index,
                'pageSize': page_size
            }

            # Gửi POST request với data trong body
            response = requests.post(request_url, headers=headers, params=params, json=data, timeout=30)

            # Debug: Log URL và request details
            _logger.info("Staff Request URL: %s", response.url)
            _logger.info("Staff Request params: %s", params)
            _logger.info("Staff Request data: %s", data)

            response.raise_for_status()

            # Parse JSON response
            result = response.json()

            _logger.info("YonSuite Staff API successful - Page %d: %d records", page_index, len(result.get("data", {}).get("recordList", [])))
            _logger.info("Response status code: %s", response.status_code)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite Staff API request failed: %s", str(e))
            raise UserError(_('Staff API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite Staff API error: %s", str(e))
            raise UserError(_('Staff API error: %s') % str(e))

    def get_countries_from_api(self, page_index=1, page_size=50):
        """
        Lấy danh sách countries từ YonSuite API với phân trang
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho countries
            endpoint = "/yonbip/digitalModel/country/batchQueryDetail"
            request_url = base_url + endpoint

            # Headers cho request
            headers = {
                'Content-Type': 'application/json'
            }

            # Parameters cho query string (chỉ access_token)
            params = {
                'access_token': access_token
            }

            # Data cho POST request body (pageSize, pageIndex)
            data = {
                'pageIndex': page_index,
                'pageSize': page_size
            }

            # Gửi POST request với data trong body
            response = requests.post(request_url, headers=headers, params=params, json=data, timeout=30)

            # Debug: Log URL và request details
            _logger.info("Countries Request URL: %s", response.url)
            _logger.info("Countries Request params: %s", params)
            _logger.info("Countries Request data: %s", data)

            response.raise_for_status()

            # Parse JSON response
            result = response.json()

            _logger.info("YonSuite Countries API successful - Page %d: %d records", page_index, len(result.get("data", {}).get("recordList", [])))
            _logger.info("Response status code: %s", response.status_code)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite Countries API request failed: %s", str(e))
            raise UserError(_('Countries API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite Countries API error: %s", str(e))
            raise UserError(_('Countries API error: %s') % str(e))

    def get_currencies_from_api(self, page_index=1, page_size=50):
        """
        Lấy danh sách currencies từ YonSuite API với phân trang
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho currencies
            endpoint = "/yonbip/digitalModel/currencytenant/batchQueryDetail"
            request_url = base_url + endpoint

            # Headers cho request
            headers = {
                'Content-Type': 'application/json'
            }

            # Parameters cho query string (chỉ access_token)
            params = {
                'access_token': access_token
            }

            # Data cho POST request body (pageSize, pageIndex)
            data = {
                'pageIndex': page_index,
                'pageSize': page_size
            }

            # Gửi POST request với data trong body
            response = requests.post(request_url, headers=headers, params=params, json=data, timeout=30)

            # Debug: Log URL và request details
            _logger.info("Currencies Request URL: %s", response.url)
            _logger.info("Currencies Request params: %s", params)
            _logger.info("Currencies Request data: %s", data)

            response.raise_for_status()

            # Parse JSON response
            result = response.json()

            _logger.info("YonSuite Currencies API successful - Page %d: %d records", page_index, len(result.get("data", {}).get("recordList", [])))
            _logger.info("Response status code: %s", response.status_code)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite Currencies API request failed: %s", str(e))
            raise UserError(_('Currencies API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite Currencies API error: %s", str(e))
            raise UserError(_('Currencies API error: %s') % str(e))

    def get_admindepts_from_api(self):
        """
        Lấy danh sách admin departments từ YonSuite API
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho admin departments
            endpoint = "/yonbip/digitalModel/admindept/tree"
            request_url = base_url + endpoint

            # Headers cho request
            headers = {
                'Content-Type': 'application/json'
            }

            # Parameters cho query string (chỉ access_token)
            params = {
                'access_token': access_token
            }
            data = {
                "externalData": {
                    "enable": [
                    ],
                }
            }

            # Gửi GET request (API này không yêu cầu data)
            response = requests.post(request_url, headers=headers, params=params, json=data, timeout=30)

            # Debug: Log URL và request details
            _logger.info("AdminDepts Request URL: %s", response.url)
            _logger.info("AdminDepts Request params: %s", params)

            response.raise_for_status()

            # Parse JSON response
            result = response.json()

            _logger.info("YonSuite AdminDepts API successful: %d records", len(result.get("data", [])))
            _logger.info("Response status code: %s", response.status_code)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite AdminDepts API request failed: %s", str(e))
            raise UserError(_('AdminDepts API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite AdminDepts API error: %s", str(e))
            raise UserError(_('AdminDepts API error: %s') % str(e))

    def get_admindept_detail_from_api(self, dept_id):
        """
        Lấy chi tiết admin department từ YonSuite API
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho admin department detail
            endpoint = "/yonbip/digitalModel/admindept/detail"
            request_url = base_url + endpoint

            # Headers cho request
            headers = {
                'Content-Type': 'application/json'
            }

            # Parameters cho query string
            params = {
                'access_token': access_token,
                'id': dept_id
            }

            # Gửi GET request
            response = requests.get(request_url, headers=headers, params=params, timeout=30)

            # Debug: Log URL và request details
            _logger.info("AdminDept Detail Request URL: %s", response.url)
            _logger.info("AdminDept Detail Request params: %s", params)

            response.raise_for_status()

            # Parse JSON response
            result = response.json()

            _logger.info("YonSuite AdminDept Detail API successful for ID: %s", dept_id)
            _logger.info("Response status code: %s", response.status_code)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite AdminDept Detail API request failed: %s", str(e))
            raise UserError(_('AdminDept Detail API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite AdminDept Detail API error: %s", str(e))
            raise UserError(_('AdminDept Detail API error: %s') % str(e))

    def get_orgunits_from_api(self):
        """
        Lấy danh sách organization units từ YonSuite API
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho organization units
            endpoint = "/yonbip/digitalModel/orgunit/querytree"
            request_url = base_url + endpoint

            # Headers cho request
            headers = {
                'Content-Type': 'application/json'
            }

            # Parameters
            params = {
                'access_token': access_token
            }

            response = requests.post(request_url, headers=headers, params=params, timeout=30)
            response.raise_for_status()

            result = response.json()
            _logger.info("YonSuite OrgUnit API response received")
            _logger.info("Response status code: %s", response.status_code)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite OrgUnit API request failed: %s", str(e))
            raise UserError(_('OrgUnit API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite OrgUnit API error: %s", str(e))
            raise UserError(_('OrgUnit API error: %s') % str(e))

    def get_orgunit_detail_from_api(self, orgunit_id):
        """
        Lấy chi tiết organization unit từ YonSuite API
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho organization unit detail
            endpoint = "/yonbip/digitalModel/orgunit/detail"
            request_url = base_url + endpoint

            # Headers cho request
            headers = {
                'Content-Type': 'application/json'
            }

            # Parameters
            params = {
                'access_token': access_token,
                'id': orgunit_id
            }

            response = requests.get(request_url, headers=headers, params=params, timeout=30)
            response.raise_for_status()

            result = response.json()
            _logger.info("YonSuite OrgUnit Detail API response received")
            _logger.info("Response status code: %s", response.status_code)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite OrgUnit Detail API request failed: %s", str(e))
            raise UserError(_('OrgUnit Detail API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite OrgUnit Detail API error: %s", str(e))
            raise UserError(_('OrgUnit Detail API error: %s') % str(e))

    def get_root_orgunit_from_api(self):
        """
        Lấy thông tin root organization unit (cấp 0) từ YonSuite API
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')
        root_org_code = config_parameter.get_param('yonsuite_integration.root_org_code', 'global00')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho root organization
            endpoint = "/yonbip/digitalModel/queryRootOrgInfos"
            request_url = base_url + endpoint

            # Headers cho request
            headers = {
                'Content-Type': 'application/json'
            }

            # Parameters cho query string (chỉ access_token)
            params = {
                'access_token': access_token
            }

            # Data cho POST request body
            data = {
                'funcType': 'salesorg',
                'code': root_org_code
            }

            # Gửi POST request với data trong body
            response = requests.post(request_url, headers=headers, params=params, json=data, timeout=30)

            # Debug: Log URL và request details
            _logger.info("Root OrgUnit Request URL: %s", response.url)
            _logger.info("Root OrgUnit Request params: %s", params)
            _logger.info("Root OrgUnit Request data: %s", data)

            response.raise_for_status()

            # Parse JSON response
            result = response.json()

            _logger.info("YonSuite Root OrgUnit API successful")
            _logger.info("Response status code: %s", response.status_code)
            _logger.info("Response data: %s", result)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite Root OrgUnit API request failed: %s", str(e))
            raise UserError(_('Root OrgUnit API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite Root OrgUnit API error: %s", str(e))
            raise UserError(_('Root OrgUnit API error: %s') % str(e))

    def get_all_orgdept_from_api(self):
        """
        Lấy danh sách tất cả organizations/departments từ YonSuite API
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho get all org/dept
            endpoint = "/yonbip/digitalModel/openapi/orgdatasync/getallorgdeptbaseinfo"
            request_url = base_url + endpoint

            # Headers cho request
            headers = {
                'Content-Type': 'application/json'
            }

            # Parameters
            params = {
                'access_token': access_token
            }

            # Body data
            body_data = {
                "funcTypeCode": "adminorg",
                "sourceType": "1",
                "externalOrg": "0",
                "pageSize": "5000",
                "pageIndex": "1"
            }

            response = requests.post(request_url, headers=headers, params=params, json=body_data, timeout=30)
            response.raise_for_status()

            result = response.json()
            _logger.info("YonSuite GetAllOrgDept API response received")
            _logger.info("Response status code: %s", response.status_code)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite GetAllOrgDept API request failed: %s", str(e))
            raise UserError(_('GetAllOrgDept API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite GetAllOrgDept API error: %s", str(e))
            raise UserError(_('GetAllOrgDept API error: %s') % str(e))

    def get_saleareas_from_api(self):
        """
        Lấy danh sách sale areas từ YonSuite API
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho sale areas
            endpoint = "/yonbip/digitalModel/salearea/newtree"
            request_url = base_url + endpoint

            # Headers cho request
            headers = {
                'Content-Type': 'application/json'
            }

            # Parameters
            params = {
                'access_token': access_token
            }

            response = requests.post(request_url, headers=headers, params=params, timeout=30)
            response.raise_for_status()

            result = response.json()
            _logger.info("YonSuite SaleArea API response received")
            _logger.info("Response status code: %s", response.status_code)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite SaleArea API request failed: %s", str(e))
            raise UserError(_('SaleArea API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite SaleArea API error: %s", str(e))
            raise UserError(_('SaleArea API error: %s') % str(e))

    def push_saleareas_to_api(self, salearea_data):
        """
        Push sale area data to YonSuite API
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho push sale area
            endpoint = "/yonbip/digitalModel/salearea/idempotent/newinsert"
            request_url = base_url + endpoint

            # Headers cho request
            headers = {
                'Content-Type': 'application/json'
            }

            # Parameters (chỉ access_token)
            params = {
                'access_token': access_token
            }

            # Gửi POST request với data trong body
            response = requests.post(request_url, headers=headers, params=params, json=salearea_data, timeout=30)

            # Debug: Log URL và request details
            _logger.info("Push SaleArea Request URL: %s", response.url)
            _logger.info("Push SaleArea Request params: %s", params)
            _logger.info("Push SaleArea Request data: %s", salearea_data)

            response.raise_for_status()

            # Parse JSON response
            result = response.json()

            _logger.info("YonSuite Push SaleArea API successful")
            _logger.info("Response status code: %s", response.status_code)
            _logger.info("Response data: %s", result)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite Push SaleArea API request failed: %s", str(e))
            raise UserError(_('Push SaleArea API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite Push SaleArea API error: %s", str(e))
            raise UserError(_('Push SaleArea API error: %s') % str(e))

    def get_stores_from_api(self, page_index=1, page_size=50):
        """
        Lấy danh sách stores từ YonSuite API với phân trang
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho stores
            endpoint = "/yonbip/sd/uretail/storelist/query"
            request_url = base_url + endpoint

            # Headers cho request
            headers = {
                'Content-Type': 'application/json'
            }

            # Parameters cho query string (chỉ access_token)
            params = {
                'access_token': access_token
            }

            # Data cho POST request body (pageSize, pageIndex)
            data = {
                'pageIndex': page_index,
                'pageSize': page_size
            }

            # Gửi POST request với data trong body
            response = requests.post(request_url, headers=headers, params=params, json=data, timeout=30)

            # Debug: Log URL và request details
            _logger.info("Stores Request URL: %s", response.url)
            _logger.info("Stores Request params: %s", params)
            _logger.info("Stores Request data: %s", data)

            response.raise_for_status()

            # Parse JSON response
            result = response.json()

            _logger.info("YonSuite Stores API successful - Page %d: %d records", page_index, len(result.get("data", {}).get("recordList", [])))
            _logger.info("Response status code: %s", response.status_code)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite Stores API request failed: %s", str(e))
            raise UserError(_('Stores API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite Stores API error: %s", str(e))
            raise UserError(_('Stores API error: %s') % str(e))

    def push_store_to_api(self, data):
        """
        Push store data to YonSuite API
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho push store
            endpoint = "/yonbip/sd/uretail/store/save"
            request_url = base_url + endpoint

            # Headers cho request
            headers = {
                'Content-Type': 'application/json'
            }

            # Parameters cho query string (chỉ access_token)
            params = {
                'access_token': access_token
            }

            # Gửi POST request với data trong body
            response = requests.post(request_url, headers=headers, params=params, json=data, timeout=30)

            # Debug: Log URL và request details
            _logger.info("Push Store Request URL: %s", response.url)
            _logger.info("Push Store Request params: %s", params)
            _logger.info("Push Store Request data: %s", data)

            response.raise_for_status()

            # Parse JSON response
            result = response.json()

            _logger.info("YonSuite Push Store API successful")
            _logger.info("Response status code: %s", response.status_code)
            _logger.info("Response data: %s", result)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite Push Store API request failed: %s", str(e))
            raise UserError(_('Push Store API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite Push Store API error: %s", str(e))
            raise UserError(_('Push Store API error: %s') % str(e))

    def get_store_detail_from_api(self, store_id):
        """
        Lấy thông tin chi tiết store từ YonSuite API
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho store detail
            endpoint = "/yonbip/sd/uretail/store/detail"
            request_url = base_url + endpoint

            # Parameters cho query string
            params = {
                'access_token': access_token,
                'id': store_id
            }

            # Gửi GET request
            response = requests.get(request_url, params=params, timeout=30)

            # Debug: Log URL và request details
            _logger.info("Store Detail Request URL: %s", response.url)
            _logger.info("Store Detail Request params: %s", params)

            response.raise_for_status()

            # Parse JSON response
            result = response.json()

            _logger.info("YonSuite Store Detail API successful for ID: %s", store_id)
            _logger.info("Response status code: %s", response.status_code)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite Store Detail API request failed: %s", str(e))
            raise UserError(_('Store Detail API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite Store Detail API error: %s", str(e))
            raise UserError(_('Store Detail API error: %s') % str(e))

    def push_product_to_api(self, data):
        """
        Push product data to YonSuite API
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho push product
            endpoint = "/yonbip/digitalModel/product/batch/save"
            request_url = base_url + endpoint

            # Headers cho request
            headers = {
                'Content-Type': 'application/json'
            }

            # Parameters cho query string (chỉ access_token)
            params = {
                'access_token': access_token
            }

            # Gửi POST request với data trong body
            response = requests.post(request_url, headers=headers, params=params, json=data, timeout=30)

            # Debug: Log URL và request details
            _logger.info("Push Product Request URL: %s", response.url)
            _logger.info("Push Product Request params: %s", params)
            _logger.info("Push Product Request data: %s", data)

            response.raise_for_status()

            # Parse JSON response
            result = response.json()

            _logger.info("YonSuite Push Product API successful")
            _logger.info("Response status code: %s", response.status_code)
            _logger.info("Response data: %s", result)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite Push Product API request failed: %s", str(e))
            raise UserError(_('Push Product API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite Push Product API error: %s", str(e))
            raise UserError(_('Push Product API error: %s') % str(e))

    def get_product_detail_from_api(self, product_id, org_id):
        """
        Get product detail from YonSuite API
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho product detail
            endpoint = "/yonbip/digitalModel/product/batchdetailnew"
            request_url = base_url + endpoint

            # Headers cho request
            headers = {
                'Content-Type': 'application/json'
            }

            # Parameters cho query string (chỉ access_token)
            params = {
                'access_token': access_token,
            }

            # Body data theo format mới
            body_data = [{
                "id": int(product_id),
                "orgId": org_id
            }]

            # Gửi POST request với data trong body
            response = requests.post(request_url, headers=headers, params=params, json=body_data, timeout=30)

            # Debug: Log URL và request details
            _logger.info("Product Detail Request URL: %s", response.url)
            _logger.info("Product Detail Request params: %s", params)
            _logger.info("Product Detail Request body: %s", body_data)

            response.raise_for_status()

            # Parse JSON response
            result = response.json()

            _logger.info("YonSuite Product Detail API successful for ID: %s", product_id)
            _logger.info("Response status code: %s", response.status_code)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite Product Detail API request failed: %s", str(e))
            raise UserError(_('Product Detail API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite Product Detail API error: %s", str(e))
            raise UserError(_('Product Detail API error: %s') % str(e))

    def get_management_classes_from_api(self, page_index=1, page_size=50):
        """
        Lấy danh sách management classes từ YonSuite API với phân trang
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho management classes
            endpoint = "/yonbip/digitalModel/managementclass/integration/newtree"
            request_url = base_url + endpoint

            # Parameters cho query string
            params = {
                'access_token': access_token,
                'pageIndex': page_index,
                'pageSize': page_size
            }

            # Gửi GET request
            response = requests.post(request_url, params=params, timeout=30)

            # Debug: Log URL và request details
            _logger.info("Management Classes Request URL: %s", response.url)
            _logger.info("Management Classes Request params: %s", params)

            response.raise_for_status()

            # Parse JSON response
            result = response.json()

            _logger.info("YonSuite Management Classes API successful")
            _logger.info("Response status code: %s", response.status_code)
            _logger.info("Response data: %s", result)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite Management Classes API request failed: %s", str(e))
            raise UserError(_('Management Classes API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite Management Classes API error: %s", str(e))
            raise UserError(_('Management Classes API error: %s') % str(e))

    def get_purchase_classes_from_api(self):
        """
        Lấy danh sách purchase classes từ YonSuite API
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho purchase classes
            endpoint = "/yonbip/digitalModel/purchaseclass/newtree"
            request_url = base_url + endpoint

            # Parameters cho query string
            params = {
                'access_token': access_token
            }

            # Gửi GET request
            response = requests.post(request_url, params=params, timeout=30)

            # Debug: Log URL và request details
            _logger.info("Purchase Classes Request URL: %s", response.url)
            _logger.info("Purchase Classes Request params: %s", params)

            response.raise_for_status()

            # Parse JSON response
            result = response.json()

            _logger.info("YonSuite Purchase Classes API successful")
            _logger.info("Response status code: %s", response.status_code)
            _logger.info("Response data: %s", result)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite Purchase Classes API request failed: %s", str(e))
            raise UserError(_('Purchase Classes API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite Purchase Classes API error: %s", str(e))
            raise UserError(_('Purchase Classes API error: %s') % str(e))

    def get_sale_classes_from_api(self):
        """
        Lấy danh sách sale classes từ YonSuite API
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        base_url = config_parameter.get_param('yonsuite_integration.base_url')
        access_token = config_parameter.get_param('yonsuite_integration.access_token')

        if not base_url or not access_token:
            raise UserError(_('Please configure YonSuite API and get access token first.'))

        try:
            # Endpoint cho sale classes
            endpoint = "/yonbip/digitalModel/saleclass/list"
            request_url = base_url + endpoint

            # Parameters cho query string
            params = {
                'access_token': access_token
            }

            # Gửi POST request
            response = requests.post(request_url, params=params, timeout=30)

            # Debug: Log URL và request details
            _logger.info("Sale Classes Request URL: %s", response.url)
            _logger.info("Sale Classes Request params: %s", params)

            response.raise_for_status()

            # Parse JSON response
            result = response.json()

            _logger.info("YonSuite Sale Classes API successful")
            _logger.info("Response status code: %s", response.status_code)
            _logger.info("Response data: %s", result)

            return result

        except requests.exceptions.RequestException as e:
            _logger.error("YonSuite Sale Classes API request failed: %s", str(e))
            raise UserError(_('Sale Classes API request failed: %s') % str(e))
        except Exception as e:
            _logger.error("YonSuite Sale Classes API error: %s", str(e))
            raise UserError(_('Sale Classes API error: %s') % str(e))
