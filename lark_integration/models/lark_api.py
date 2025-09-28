import requests
from datetime import datetime, timedelta

import logging
from time import sleep
from datetime import datetime

import lark_oapi as lark
from lark_oapi.api.approval.v4 import *

from lark_oapi.api.auth.v3 import *
from lark_oapi.api.authen.v1 import *
from lark_oapi.api.bitable.v1 import *
from lark_oapi.api.drive.v1 import *

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class LarkAPI(models.TransientModel):
    _name = 'lark.api'
    _description = "Lark API"

    def _lark_get_redirect_uri(self):
        return self.get_base_url() + '/lark/callback'

    def _get_app_access_token(self, **kw):
        url = 'https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal'
        headers = {'Content-Type': 'application/json'}

        config_parameter = self.env['ir.config_parameter'].sudo()
        app_id = config_parameter.get_param('lark.app.id')
        app_secret = config_parameter.get_param('lark.app.secret')
        payload = {
            'app_id': app_id,
            'app_secret': app_secret
        }
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 0:
                config_parameter.set_param('lark.app.access.token', data.get('app_access_token'))
                config_parameter.set_param('lark.app.access.token.expiry', fields.Datetime.now() + timedelta(seconds=data.get('expire_in', 7200)))
            else:
                raise Exception(data.get('msg', 'Unknown error'))
        except requests.RequestException as e:
            raise Exception(f"Failed to get App Access Token: {str(e)}")


