from datetime import timedelta, datetime, date, timezone
import time
import hashlib
import requests
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

JST_API_URL = "https://asiaopenapi.jsterp.com"

SHOP_DATETIME_FIELDS = ['created', 'jst_modified']

class JstShop(models.Model):
    _name = 'jst.shop'
    _description = 'JST Shop'
    _rec_name = 'shopName'

    # Basic info from API
    companyId = fields.Integer("Company Id", aggregator=None)
    companyName = fields.Char("Company Name")
    shopId = fields.Integer("Shop Id", aggregator=None)
    shopName = fields.Char("Shop Name")
    platformId = fields.Char("Platform Id")
    platformShopId = fields.Char("Platform Shop Id")
    platformShopNick = fields.Char("Platform Shop Nick")
    platformVersionName = fields.Char("Platform Version Name")
    platformShopData = fields.Text("Platform Shop Data")
    shopUrl = fields.Char("Shop URL")
    sessionStatus = fields.Char("Session Status")
    enabled = fields.Boolean("Enabled")
    created = fields.Datetime("Created (epoch)")
    creator = fields.Integer("Creator", aggregator=None)
    creatorName = fields.Char("Creator Name")
    jst_modified = fields.Datetime("Modified (epoch)")
    modifier = fields.Integer("Modifier", aggregator=None)
    modifierName = fields.Char("Modifier Name")
    remark = fields.Text("Remark")
    mobile = fields.Char("Mobile")
    address = fields.Char("Address")
    logisticProvider = fields.Char("Logistic Provider")
    defaultCurrencyId = fields.Char("Default Currency Id")
    timeZone = fields.Integer("Time Zone", aggregator=None)
    isMainShop = fields.Boolean("Is Main Shop")
    mainShopId = fields.Integer("Main Shop Id", aggregator=None)

    # Toàn bộ payload đơn (để lần vết đầy đủ)
    raw_payload = fields.Json(
        string="Raw Payload",
        help="Full JSON order object as returned by API"
    )

    def action_sync_jst_shops(self, modifiedBegin, modifiedEnd):
        # Check rule
        # 2018 -> 20xx
        body_data = {
            "requestModel": {
              "modifiedBegin": modifiedBegin,
              "modifiedEnd": modifiedEnd
            },
            "dataPage": {
              "pageSize": 500,
              "pageIndex": 1
            }
        }
        resp_data = self.env['res.config.settings']._call_api_jst("/api/Shop/GetShops", body_data)
        if resp_data.get('success'):
            if resp_data.get('data'):
                synced_shops = self.env['jst.shop'].search([])
                synced_shop_ids = synced_shops.mapped('shopId')
                new_vals_list = []
                update_vals_list = []
                map_fields = self._map_fields()
                for line in resp_data['data']:
                    new_line = {'raw_payload': line}
                    for key, value in line.items():
                        field_key = map_fields.get(key)
                        if field_key:
                            if field_key in SHOP_DATETIME_FIELDS:
                                value_dt = datetime.fromtimestamp(value, timezone.utc).replace(tzinfo=None) if value else False
                                new_line[field_key] = value_dt
                            else:
                                new_line[field_key] = value
                    # Kiểm tra shop đã đồng bộ về odoo chưa
                    if new_line.get('shopId', 0) in synced_shop_ids:
                        update_vals_list.append(new_line)
                    else:
                        new_vals_list.append(new_line)
                # tạo shop trên odoo
                if new_vals_list:
                    self.env['jst.shop'].sudo().create(new_vals_list)
                # update shop đã có trên odoo, theo từng line
                if update_vals_list:
                    for vals_line in update_vals_list:
                        shop = synced_shops.filtered(lambda r: r.shopId == vals_line.get('shopId', 0))
                        shop.sudo().write(vals_line)
        else:
            error_msg = resp_data.get('message', 'Unknown error')
            _logger.error("Error (Get JST Shops): %s", error_msg)

    def _map_fields(self):
        # key: JST API key, value: Odoo field name
        return {
            'companyName': 'companyName',
            'companyId': 'companyId',
            'shopId': 'shopId',
            'shopName': 'shopName',
            'platformId': 'platformId',
            'platformShopId': 'platformShopId',
            'shopUrl': 'shopUrl',
            'platformShopNick': 'platformShopNick',
            'sessionStatus': 'sessionStatus',
            'platformVersionName': 'platformVersionName',
            'enabled': 'enabled',
            'created': 'created',
            'creator': 'creator',
            'creatorName': 'creatorName',
            'modified': 'jst_modified',
            'modifier': 'modifier',
            'modifierName': 'modifierName',
            'remark': 'remark',
            'mobile': 'mobile',
            'address': 'address',
            'logisticProvider': 'logisticProvider',
            'platformShopData': 'platformShopData',
            'defaultCurrencyId': 'defaultCurrencyId',
            'timeZone': 'timeZone',
            'isMainShop': 'isMainShop',
            'mainShopId': 'mainShopId',
        }

    def _action_sync_jst_shop_daily(self):
        ts_end = int(fields.Datetime.now().timestamp())
        ts_start = ts_end - 24*3600
        self.env['jst.shop'].action_sync_jst_shops(ts_start, ts_end)

    def action_sync_all_product_shop(self):
        for r in self:
            self.env['jst.shop.product'].sudo().action_sync_jst_shop_products(ShopId=r.shopId)
            time.sleep(0.5)
