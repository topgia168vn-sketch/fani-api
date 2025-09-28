from odoo import http
import requests
import logging
import time
import hashlib
import json
from datetime import datetime 
from odoo.http import request
_logger = logging.getLogger(__name__)


JST_GET_TOKEN_URL = "https://asiaopenapi.jsterp.com/api/Authentication/GetToken"

class JSTCallbackController(http.Controller):

    @http.route('/jst/callback', type='http', auth='public', methods=['GET'], csrf=False)
    def jst_callback(self, **kwargs):
        """
        Callback URL that receives the authorization code from JST
        Example redirect:
        https://nvp10.com/jst/callback?code=xxxxxx&state=abc
        """
        code = kwargs.get('code')
        state = kwargs.get('state')

        if not code:
            return "Missing authorization 'code' parameter"
        elif not state:
            return "Missing 'state' parameter"

        # Log or store the code (you will use it to get access_token)
        _logger.info("Received JST authorization callback: code=%s, state=%s", code, state)

        # TODO: Call JST API to exchange 'code' -> 'access_token'
        appkey = request.env['ir.config_parameter'].sudo().get_param('jst.appkey')
        appsecret = request.env['ir.config_parameter'].sudo().get_param('jst.appsecret')
    
        body = {"Code": code}
        # Chuẩn hóa JSON chính xác như sẽ gửi đi (không khoảng trắng)
        body_str = json.dumps(body, separators=(',', ':'), ensure_ascii=False)

        # ts dùng mili-giây
        timestamp = int(time.time() * 1000)

        # sign = MD5("appkey=xxx&appsecret=xxx&data=<body_str>&ts=<timestamp>").upper()
        sign_src = f"appkey={appkey}&appsecret={appsecret}&data={body_str}&ts={timestamp}"
        sign = hashlib.md5(sign_src.encode("utf-8")).hexdigest().upper()

        headers = {
            "appkey": appkey,
            "sign": sign,
            "ts": str(timestamp),
            "Content-Type": "application/json",
        }

        # Gửi đúng chuỗi đã dùng để ký (không dùng json=..., dùng data=...)
        resp = requests.post(JST_GET_TOKEN_URL, data=body_str.encode("utf-8"), headers=headers)
        resp_data = resp.json()
        _logger.info("JST API response: %s", resp_data)

        # Update các thông tin vào company hiện tại
        if resp_data.get('success') and resp_data.get('data'):
            jst_data = resp_data['data']
            
            access_token_expired = jst_data.get('expiredTime', "") # '2025-09-21T19:28:39.5878202+08:00'
            access_refresh_token_expired = jst_data.get('refreshTokenExpireTime', "") # '2026-02-21T19:28:39.5878214+08:00'

            def _to_date(val):
                if not val:
                    return False
                date_str = val.split('T', 1)[0]
                return date_str

            # Cập nhật các trường JST vào system parameter
            ts_now = str(int(datetime.now().timestamp()))
            request.env['ir.config_parameter'].sudo().set_param('jst.access_token', jst_data.get('accessToken'))
            request.env['ir.config_parameter'].sudo().set_param('jst.refresh_token', jst_data.get('refreshToken'))
            request.env['ir.config_parameter'].sudo().set_param('jst.access_token_expired', _to_date(access_token_expired))
            request.env['ir.config_parameter'].sudo().set_param('jst.refresh_token_expired', _to_date(access_refresh_token_expired))
            request.env['ir.config_parameter'].sudo().set_param('jst.company_id', str(jst_data.get('companyId')))
            request.env['ir.config_parameter'].sudo().set_param('jst.next_ts_sync_order', ts_now)
            request.env['ir.config_parameter'].sudo().set_param('jst.next_ts_sync_after_order', ts_now)
            request.env['ir.config_parameter'].sudo().set_param('jst.next_ts_sync_inout', ts_now)
            request.env['ir.config_parameter'].sudo().set_param('jst.next_ts_sync_other_inout', ts_now)
            
            _logger.info("Successfully updated JST fields to system parameters")
            return "Authorization successful! JST tokens have been updated."
        else:
            error_msg = resp_data.get('message', 'Unknown error')
            _logger.error("JST API error: %s", error_msg)
            return f"JST API error: {error_msg}"
