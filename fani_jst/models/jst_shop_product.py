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

SHOP_PRODUCT_DATETIME_FIELDS = ['created', 'jst_modified'] # -> DATETIME OBJECT


class JstShopProduct(models.Model):
    _name = 'jst.shop.product'
    _description = 'JST Shop Product'
    _rec_name = 'itemName'

    # Core identifiers
    itemId = fields.Char("Item Code")
    itemName = fields.Char("Item Name")
    platformItemId = fields.Char("Platform Model Number")
    platformSkuCode = fields.Char("Platform Product Code")
    platformSkuId = fields.Char("Platform Product Number")
    platformSkuName = fields.Char("Platform Product Name")
    
    # Shop information
    shopId = fields.Integer("Store Number", aggregator=None)
    shopName = fields.Char("Store Name")
    
    # SKU information
    skuId = fields.Char("Product Code")
    skuName = fields.Char("Product Name")
    skuCode = fields.Char("SKU Code")
    
    # Media
    picture = fields.Char("Product Images")
    itemPicture = fields.Char("Item Picture")
    
    # Platform details
    platformItemUrl = fields.Char("Platform Item URL")
    propertyValues = fields.Char("Property Specifications")
    
    # Timestamps
    created = fields.Datetime("Creation Time")
    jst_modified = fields.Datetime("Modification Time")
    
    # Status and mapping
    isManualMapping = fields.Boolean("Is it bound?")
    platformSkuStatus = fields.Char("Status (On Sale 1 Not On Sale 0)")
    
    # Pricing
    price = fields.Float("Price")

    # Toàn bộ payload đơn (để lần vết đầy đủ)
    raw_payload = fields.Json(
        string="Raw Payload",
        help="Full JSON order object as returned by API"
    )

    def action_sync_jst_shop_products(self, skuIds=False, ShopId=False, PlatformSkuCodes=False, pageIndex=1):
        """
        Đồng bộ shop products theo:
            - skuIds: danh sách string
            - ShopId: shop id
            - PlatformSkuCodes: danh sách string
        """
        while True:
            body_data = {
                "requestModel": {},
                "dataPage": {
                  "pageSize": 500,
                  "pageIndex": pageIndex
                }
            }
            if skuIds:
                body_data["requestModel"]["skuIds"] = skuIds
            if ShopId:
                body_data["requestModel"]["ShopId"] = ShopId
            if PlatformSkuCodes:
                body_data["requestModel"]["PlatformSkuCodes"] = PlatformSkuCodes
            resp_data = self.env['res.config.settings']._call_api_jst("/api/Goods/GetShopSkus", body_data)

            # Call API không thành công
            if not resp_data.get('success'):
                _logger.error("Error (Get JST Shop Product): %s", resp_data.get('message'))
                break
            
            data = resp_data.get('data') or []
            if data:
                # Create/Update shop product
                self._update_shop_product(data)

                # Check dataPage
                dp = resp_data.get('dataPage') or {}
                if dp.get('isLast', True):
                    break
                pageIndex = dp.get('pageIndex', pageIndex) + 1
                # Pending 0.5 second before calling API
                time.sleep(0.5)
            else:
                break

    def _update_shop_product(self, data):
        # Lấy danh sách tuple từ data sync
        itemId_list = []
        shopId_list = []
        skuId_list = []
        platformItemId_list = []
        
        for row in data:
            itemId_list.append(row.get('itemId'))
            shopId_list.append(row.get('shopId'))
            skuId_list.append(row.get('skuId'))
            platformItemId_list.append(row.get('platformItemId'))
        
        # Tìm trong DB các order đã tồn tại (chỉ load id + orderId)
        existing_shop_products = self.sudo().search_read(
            domain=[('itemId', 'in', itemId_list), ('shopId', 'in', shopId_list), ('skuId', 'in', skuId_list), ('platformItemId', 'in', platformItemId_list)],
            fields=['id', 'itemId', 'shopId', 'skuId', 'platformItemId']
        )
        existing_shop_product_map = {}
        for sp in existing_shop_products:
            key = "%s_*^%s_*^%s_*^%s" % (sp['itemId'], sp['shopId'], sp['skuId'], sp['platformItemId'])
            existing_shop_product_map[key] = sp['id']
        
        new_vals_list = []
        update_vals_list = []
        map_fields = self._map_fields()

        for line in data:
            new_line = {'raw_payload': line}
            for key, value in line.items():
                field_key = map_fields.get(key)
                if field_key:
                    if field_key in SHOP_PRODUCT_DATETIME_FIELDS:
                        value_dt = datetime.fromtimestamp(value, timezone.utc).replace(tzinfo=None) if value else False
                        new_line[field_key] = value_dt
                    else:
                        new_line[field_key] = value
            
            # Kiểm tra product đã đồng bộ về odoo chưa
            sp_key = f"{line.get('itemId')}_*^{line.get('shopId')}_*^{line.get('skuId')}_*^{line.get('platformItemId')}"
            if sp_key in existing_shop_product_map:
                update_vals_list.append((existing_shop_product_map[sp_key], new_line))
            else:
                new_vals_list.append(new_line)

        # Thực hiện DB transaction
        with self.env.cr.savepoint():
            if new_vals_list:
                self.sudo().create(new_vals_list)
            for sp_id, vals in update_vals_list:
                shop_product = self.browse(sp_id)
                shop_product.sudo().write(vals)

    def _map_fields(self):
        # key: JST API key, value: Odoo field name
        return {
            'itemId': 'itemId',
            'itemName': 'itemName',
            'platformItemId': 'platformItemId',
            'platformSkuCode': 'platformSkuCode',
            'platformSkuId': 'platformSkuId',
            'platformSkuName': 'platformSkuName',
            'shopId': 'shopId',
            'shopName': 'shopName',
            'skuId': 'skuId',
            'skuName': 'skuName',
            'skuCode': 'skuCode',
            'picture': 'picture',
            'itemPicture': 'itemPicture',
            'platformItemUrl': 'platformItemUrl',
            'propertyValues': 'propertyValues',
            'created': 'created',
            'modified': 'jst_modified',
            'isManualMapping': 'isManualMapping',
            'platformSkuStatus': 'platformSkuStatus',
            'price': 'price',
        }

    def _action_sync_jst_shop_products_daily(self):
        """Daily sync for shop products Daily"""
        self.env['jst.shop.product'].sudo().action_sync_jst_shop_products()
