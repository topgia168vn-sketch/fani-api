# -*- coding: utf-8 -*-
import logging
import requests
from dateutil import parser
from odoo import models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PancakeApiMixin(models.AbstractModel):
    _name = "pancake.api.mixin"
    _description = "Reusable Pancake API client"

    def _pancake_base_url(self):
        icp = self.env["ir.config_parameter"].sudo()
        return icp.get_param("pancake.base_url", "https://pos.pages.fm/api/v1")

    def _normalize_method(self, method):
        m = (method or "GET").upper()
        if m not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
            raise UserError(_("Unsupported HTTP method: %s") % m)
        return m

    def _pancake_request(
        self,
        api_key,
        path,
        method="GET",
        params=None,
        json=None,
        headers=None,
        timeout=30,
    ):
        """
        Low-level HTTP caller for Pancake.
        - Always injects api_key as query param.
        - Supports GET/POST/PUT/PATCH/DELETE.
        - Returns parsed JSON (dict/list).
        """
        if not api_key:
            raise UserError(_("Missing API key for Pancake"))
        method = self._normalize_method(method)

        # Base URL ưu tiên: đối tượng (vd: shop.base_url) > system parameter
        base = self._pancake_base_url()
        if not path.startswith("/"):
            path = "/" + path
        url = f"{base}{path}"

        q = dict(params or {})
        q["api_key"] = api_key

        req_headers = {"Accept": "application/json"}
        if headers:
            req_headers.update(headers)

        try:
            if method == "GET":
                resp = requests.get(url, params=q, headers=req_headers, timeout=timeout)
            elif method == "POST":
                resp = requests.post(url, params=q, json=json, headers=req_headers, timeout=timeout)
            elif method == "PUT":
                resp = requests.put(url, params=q, json=json, headers=req_headers, timeout=timeout)
            elif method == "PATCH":
                resp = requests.patch(url, params=q, json=json, headers=req_headers, timeout=timeout)
            elif method == "DELETE":
                resp = requests.delete(url, params=q, headers=req_headers, timeout=timeout)
            else:
                # Should never reach here due to _normalize_method
                raise UserError(_("Unsupported HTTP method: %s") % method)
        except requests.RequestException as e:
            _logger.exception("Pancake %s %s failed: %s", method, url, e)
            raise UserError(_("Cannot connect to Pancake: %s") % (e,))

        if resp.status_code != 200:
            body_preview = (resp.text or "")[:800]
            raise UserError(_(
                "Pancake API error (%(method)s %(url)s): HTTP %(code)s\n%(body)s"
            ) % {"method": method, "url": resp.url, "code": resp.status_code, "body": body_preview})

        try:
            return resp.json()
        except Exception:
            _logger.error("Invalid JSON from Pancake (%s %s): %s", method, resp.url, resp.text[:800])
            raise UserError(_("Invalid JSON response from Pancake"))

    def _pancake_get(self, api_key, path, params=None, timeout=30):
        """Wrapper GET để dùng nhanh ở các tác vụ đọc."""
        return self._pancake_request(
            api_key=api_key,
            path=path,
            method="GET",
            params=params,
            timeout=timeout,
        )

    def _upsert(self, model, domain, values):
        """search→write / create"""
        
        rec = self.env[model].search(domain, limit=1)
        if rec:
            rec.write(values)
            return rec
        return self.env[model].create(values)

    def _parse_dt(self, s):
        """Parse ISO-8601 datetime strings (e.g., 2020-04-01T10:18:41, with/without Z/ms)."""
        if not s:
            return False
        try:
            dt = parser.isoparse(str(s).strip())
            return dt
        except Exception:
            return False

    def _parse_date(self, s):
        """Parse date strings like '2020-04-01'."""
        if not s:
            return False
        try:
            d = parser.parse(str(s).strip()).date()
            return d
        except Exception:
            return False
