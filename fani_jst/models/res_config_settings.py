import time
import hashlib
import requests
import json
import logging
from odoo import fields, models, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


JST_AUTH_URL = "https://asia.jsterp.com/account/companyauth/auth"
JST_API_URL = "https://asiaopenapi.jsterp.com"

class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    jst_appkey = fields.Char(string='JST App Key', config_parameter='jst.appkey')
    jst_appsecret = fields.Char(string='JST App Secret', config_parameter='jst.appsecret')

    def action_test(self):
        pass
        # self.env['jst.shop'].action_sync_jst_shops()

        # self.env['jst.product.template'].action_sync_jst_shops()

    def action_connect_jst(self):
        """Redirect user to JST Auth URL"""
        self.ensure_one()
        if not self.jst_appkey or not self.jst_appsecret:
            raise UserError(_("Please enter JST App Key and JST App Secret."))
        jst_auth_url = self._get_jst_auth_url()
        return {
            'type': 'ir.actions.act_url',
            'url': jst_auth_url,
            'target': 'new'
        }

    def _get_jst_auth_url(self):
        appkey = self.jst_appkey
        appsecret = self.jst_appsecret
        state = "odoo_jst_auth"
        timestamp = int(time.time())

        sign_str = f"appkey={appkey}&appsecret={appsecret}&state={state}&timestamp={timestamp}"
        sign = hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()

        redirect_uri = self.env['ir.config_parameter'].sudo().get_param('web.base.url') + "/jst/callback"
        jst_auth_url = (
                f"{JST_AUTH_URL}?appkey={appkey}"
                f"&timestamp={timestamp}"
                f"&state={state}"
                f"&sign={sign}"
                f"&redirect_uri={redirect_uri}"
            )
        return jst_auth_url

    def _call_api_jst(self, path_url, body_data, headers_data=False):
        url = JST_API_URL + path_url
        ConfigParamater = self.env['ir.config_parameter'].sudo()
        appkey = ConfigParamater.get_param('jst.appkey')
        appsecret = ConfigParamater.get_param('jst.appsecret')
        access_token = ConfigParamater.get_param('jst.access_token')
        company_id = ConfigParamater.get_param('jst.company_id')
        ts = int(time.time() * 1000)

        # Create Sign
        body_str = json.dumps(body_data, separators=(',', ':'), ensure_ascii=False)  #Chuẩn hóa JSON chính xác như sẽ gửi đi (không khoảng trắng)
        sign_src = f"appkey={appkey}&appsecret={appsecret}&data={body_str}&accesstoken={access_token}&companyid={company_id}&ts={ts}"
        sign = hashlib.md5(sign_src.encode("utf-8")).hexdigest().upper()

        # prepare headers
        headers = headers_data or {
            "appkey": appkey,
            "accesstoken": access_token,
            "CompanyId": company_id,
            "sign": sign,
            "ts": str(ts),
            "Content-Type": "application/json",
        }

        # Call api
        try:
            resp = requests.post(url, data=body_str.encode("utf-8"), headers=headers)

        except requests.RequestException as e:
            _logger.exception("Call JST '%s' failed: %s", path_url, e)
            raise UserError(_("Cannot connect to JST: %s") % (e,))

        if resp.status_code != 200:
            body_preview = (resp.text or "")[:800]
            raise UserError(_(
                "JST API error (%(url)s): HTTP %(code)s\n%(body)s"
            ) % {"url": resp.url, "code": resp.status_code, "body": body_preview})

        try:
            return resp.json()
        except Exception:
            _logger.error("Invalid JSON from JST (%s): %s", resp.url, resp.text[:800])
            raise UserError(_("Invalid JSON response from JST"))
