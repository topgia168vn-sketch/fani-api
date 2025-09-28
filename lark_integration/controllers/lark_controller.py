
import requests
from datetime import datetime, timedelta

from odoo import http
from odoo.http import request


class LarkController(http.Controller):

    @http.route('/lark/callback', type='http', auth='public', website=True)
    def lark_callback(self, **kwargs):
        code = kwargs.get('code')
        state = kwargs.get('state')
        if not code or not state:
            return "Error: Missing code or state"

        try:
            user_id = int(state.split('_')[-1])
            user = http.request.env['res.users'].sudo().search([('id', '=', user_id)], limit=1)
            if not user:
                return "Error: Invalid state or configuration"
        except ValueError:
            return "Error: Invalid state format"

        url = 'https://open.feishu.cn/open-apis/authen/v1/access_token'
        headers = {'Content-Type': 'application/json'}
        config_parameter = request.env['ir.config_parameter'].sudo()
        app_id = config_parameter.get_param('lark.app.id')
        app_secret = config_parameter.get_param('lark.app.secret')
        payload = {
            'grant_type': 'authorization_code',
            'app_id': app_id,
            'app_secret': app_secret,
            'code': code,
            'redirect_uri': request.env['lark.api']._lark_get_redirect_uri()
        }
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 0:
                user.sudo().write({
                    'lark_user_access_token': data['data']['access_token'],
                    'lark_user_access_token_expiry': datetime.now() + timedelta(seconds=data['data']['expires_in']),
                    'lark_user_refresh_token': data['data']['refresh_token']
                })
                user._get_lark_user_info()
                user.fetch_items_in_root_folder()
                return request.redirect("/odoo")
            else:
                return f"Error: {data.get('msg', 'Unknown error')}"
        except requests.RequestException as e:
            return f"Failed to get User Access Token: {str(e)}"
