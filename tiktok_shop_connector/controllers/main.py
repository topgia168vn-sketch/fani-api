import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class TiktokShopController(http.Controller):

    @http.route("/tiktok/shop/oauth/callback", auth="user", csrf=False)
    def callback(self, **kw):
        """
        TikTok redirect về: ?auth_code=...&state=shopId:random
        """
        _logger.info(f"TikTok callback: {kw}")
        auth_code = kw.get("auth_code") or kw.get("code")
        state = kw.get("state") or ""

        if not auth_code or ":" not in state:
            _logger.error(f"Missing auth_code/state: {auth_code}, {state}")
            return request.redirect("/odoo")

        try:
            shop_id = int(state.split(":")[0])
        except Exception:
            _logger.error(f"Bad state: {state}")
            return request.redirect("/odoo")

        shop = request.env["tiktok.shop"].sudo().browse(shop_id)
        if not shop.exists():
            _logger.error(f"Shop not found: {shop_id}")
            return request.redirect("/odoo")

        # Verify state để chống CSRF
        if shop.oauth_state != state:
            _logger.error(f"State mismatch: expected {shop.oauth_state}, got {state}")
            return request.redirect("/odoo")

        try:
            shop._exchange_authorization_code(auth_code)
            _logger.info(f"Authorization success: {shop.name}")
            # Clear oauth_state sau khi success
            shop.sudo().write({"oauth_state": False})
        except Exception as e:
            _logger.error(f"Authorization failed: {e}")

        # Redirect về form view của shop record
        action = request.env.ref("tiktok_shop_connector.action_tiktok_shop")
        url = f"/odoo/action-{action.id}/{shop.id}"
        return request.redirect(url)
