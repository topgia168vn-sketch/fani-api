import requests
from datetime import datetime, timedelta
from datetime import datetime
import logging
import lark_oapi as lark
from urllib.parse import urlencode

from odoo import models, fields, api


_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    lark_user_access_token = fields.Char(string="Lark User Access Token", readonly=True)
    lark_user_access_token_expiry = fields.Datetime(string="Lark User Token Expiry", readonly=True)
    lark_user_refresh_token = fields.Char(string="Lark User Refresh Token", readonly=True)

    lark_user_name = fields.Char(string="Lark User Name", readonly=True)
    lark_user_email = fields.Char(string="Lark User Email", readonly=True)
    lark_user_open_id = fields.Char(string="Lark User Open ID", readonly=True)
    lark_user_union_id = fields.Char(string="Lark User Union ID", readonly=True)

    def _refresh_user_access_token(self):
        self.ensure_one()
        if not self.lark_user_refresh_token:
            raise Exception("No refresh token available.")
        url = 'https://open.feishu.cn/open-apis/authen/v1/refresh_access_token'
        headers = {'Content-Type': 'application/json'}

        config_parameter = self.env['ir.config_parameter'].sudo()
        app_id = config_parameter.get_param('lark.app.id')
        app_secret = config_parameter.get_param('lark.app.secret')

        payload = {
            'grant_type': 'refresh_token',
            'app_id': app_id,
            'app_secret': app_secret,
            'refresh_token': self.lark_user_refresh_token
        }
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 0:
                self.write({
                    'lark_user_access_token': data['data']['access_token'],
                    'lark_user_access_token_expiry': datetime.now() + timedelta(seconds=data['data']['expires_in']),
                    'lark_user_refresh_token': data['data']['refresh_token']
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Success',
                        'message': 'User Access Token refreshed successfully!',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise Exception(data.get('msg', 'Unknown error'))
        except requests.RequestException as e:
            raise Exception(f"Failed to refresh User Access Token: {str(e)}")

    @api.model
    def _auto_refresh_user_access_token(self):
        threshold = datetime.now() + timedelta(minutes=10)
        user_ids = self.env['res.users'].search([
            ('lark_user_access_token', '!=', False),
            ('lark_user_refresh_token', '!=', False),
            ('lark_user_access_token_expiry', '!=', False),
            ('lark_user_access_token_expiry', '<=', threshold),
        ])
        for user in user_ids:
            user._refresh_user_access_token()

    def _get_client(self):
        self.ensure_one()
        # return lark.Client.builder()\
        #     .app_id(self.app_id)\
        #     .app_secret(self.app_secret)\
        #     .domain('https://open.larksuite.com')\
        #     .timeout(3)\
        #     .log_level(lark.LogLevel.DEBUG).build()
        return lark.Client.builder() \
            .enable_set_token(True) \
            .log_level(lark.LogLevel.DEBUG) \
            .domain('https://open.larksuite.com') \
            .timeout(30)\
            .build()

    def _get_lark_user_info(self):
        self.ensure_one()
        if not self.lark_user_access_token:
            raise Exception("No User Access Token available.")
        url = 'https://open.feishu.cn/open-apis/authen/v1/user_info'
        headers = {
            'Authorization': f'Bearer {self.lark_user_access_token}',
            'Content-Type': 'application/json'
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            _logger.info(f"User Info response: {data}")
            if data.get('code') == 0:
                self.write({
                    'lark_user_name': data['data'].get('name'),
                    'lark_user_email': data['data'].get('email'),
                    'lark_user_open_id': data['data'].get('open_id'),
                    'lark_user_union_id': data['data'].get('union_id')
                })
            else:
                raise Exception(data.get('msg', 'Unknown error'))
        except requests.RequestException as e:
            _logger.error(f"Failed to get User Info: {str(e)}")
            raise Exception(f"Failed to get User Info: {str(e)}")

    def connect_to_lark(self):
        self.ensure_one()
        base_url = 'https://open.feishu.cn/open-apis/authen/v1/authorize'
        config_parameter = self.env['ir.config_parameter'].sudo()
        params = {
            'app_id':  config_parameter.get_param('lark.app.id'),
            'redirect_uri': self.env['lark.api']._lark_get_redirect_uri(),
            'scope': 'approval:approval contact:contact contact:contact.base:readonly contact:department.organize:readonly contact:user.employee_id:readonly contact:department.base:readonly contact:user.department:readonly contact:user.user_geo contact:user.dotted_line_leader_info.read contact:user.email:readonly directory:employee.base.email:read contact:user.gender:readonly contact:user.base:readonly contact:user.subscription_ids:write contact:user.department_path:readonly contact:user.assign_info:read contact:user.employee:readonly contact:user.phone:readonly bitable:app drive:drive drive:drive:readonly space:document:retrieve',
            'state': f'odoo_lark_{self.id}',
        }
        auth_url = f"{base_url}?{urlencode(params)}"
        return {
            'type': 'ir.actions.act_url',
            'url': auth_url,
            'target': 'new',
        }

    def fetch_items_in_root_folder(self):
        self.env['lark.file'].fetch_items_in_folder(self.env.user)
