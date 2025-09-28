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

PRODUCT_TEAMPLATE_DATETIME_FIELDS = ['created', 'jst_modified'] # -> DATETIME OBJECT
PRODUCT_TEAMPLATE_LIST_OBJECT_FIELDS = ['bagCodes', 'auxiliaryCodes'] # -> "[X, Y, X]"


class JstProductTemplate(models.Model):
    _name = 'jst.product.template'
    _description = 'JST Product Template'
    _rec_name = 'name'

    # Core identifiers and names
    companyId = fields.Integer("Company Id", aggregator=None)
    itemId = fields.Char("Item Id")
    itemName = fields.Char("Item Name")
    skuId = fields.Char("SKU Id")
    name = fields.Char("Product Name")
    skuCode = fields.Char("SKU Code")
    fullName = fields.Char("Full Name")
    shortName = fields.Char("Short Name")

    # Categorization
    brandName = fields.Char("Brand Name")
    categoryName = fields.Char("Category Name")
    vcName = fields.Char("VC Name")
    categoryPropertyContent = fields.Text("Category Property Content")

    # Pricing
    averageCostPrice = fields.Float("Average Cost Price")
    costPrice = fields.Float("Cost Price")
    lowestSalePrice = fields.Float("Lowest Sale Price")
    memberPrice = fields.Float("Member Price")
    nameplatePrice = fields.Float("Nameplate Price")
    salePrice = fields.Float("Sale Price")
    wholesalePrice = fields.Float("Wholesale Price")

    # Dimensions / weight
    height = fields.Float("Height")
    length = fields.Float("Length")
    width = fields.Float("Width")
    cube = fields.Float("Cube")
    weight = fields.Float("Weight")
    weightUnit = fields.Char("Weight Unit")

    # Limits / quantities
    lowerLimitQty = fields.Integer("Lower Limit Qty")
    upperLimitQty = fields.Integer("Upper Limit Qty")
    virtualQty = fields.Integer("Virtual Qty")
    safetyStockQty = fields.Integer("Safety Stock Qty")
    standardBoxQty = fields.Integer("Standard Box Qty")

    # Shelf life / expiry
    expireWarningDay = fields.Integer("Expire Warning Day")
    expiryDay = fields.Integer("Expiry Day")
    isVerifyShelfLife = fields.Boolean("Is Verify Shelf Life")

    # Flags
    enabled = fields.Boolean("Enabled")
    isAllowLessthencost = fields.Boolean("Allow Less Than Cost")
    isCombined = fields.Boolean("Is Combined")
    isInspection = fields.Boolean("Is Inspection")
    isOnPurchaseSale = fields.Boolean("Is On Purchase Sale")
    isStockSync2wms = fields.Boolean("Is Stock Sync 2 WMS")

    # Strings / labels / properties
    lableString = fields.Char("Label String")
    propertyNameString = fields.Char("Property Name String")
    propertyShortName = fields.Char("Property Short Name")
    propertyValueString = fields.Char("Property Value String")

    # Custom properties
    customProperty1 = fields.Char("Custom Property 1")
    customProperty2 = fields.Char("Custom Property 2")
    customProperty3 = fields.Char("Custom Property 3")
    customProperty4 = fields.Char("Custom Property 4")

    # Media / barcodes
    picture = fields.Char("Picture")
    picturesString = fields.Char("Pictures String")
    barCode = fields.Char("Bar Code")

    # Supplier
    supplierCode = fields.Char("Supplier Code")
    supplierName = fields.Char("Supplier Name")

    # Units
    unit = fields.Char("Unit")

    # Datetimes and users
    created = fields.Datetime("Created (epoch)")
    creator = fields.Integer("Creator", aggregator=None)
    jst_modified = fields.Datetime("Modified (epoch)")
    modifier = fields.Integer("Modifier", aggregator=None)

    # Arrays / complex
    bagCodes = fields.Text("Bag Codes (JSON)")
    auxiliaryCodes = fields.Text("Auxiliary Codes (JSON)")

    # Toàn bộ payload đơn (để lần vết đầy đủ)
    raw_payload = fields.Json(
        string="Raw Payload",
        help="Full JSON order object as returned by API"
    )

    def action_sync_jst_products(self, modified_begin, modified_end, enabled=True, pageIndex=1):
        """
        Đồng bộ sản phẩm theo thời gian
        """
        while True:
            body_data = {
                "requestModel": {
                  "modifiedBegin": int(modified_begin),
                  "modifiedEnd": int(modified_end),
                  "enabled": bool(enabled)
                },
                "dataPage": {
                  "pageSize": 500,
                  "pageIndex": pageIndex
                }
            }
            resp_data = self.env['res.config.settings']._call_api_jst("/api/Goods/GetItemSkus", body_data)

            # Call API không thành công
            if not resp_data.get('success'):
                _logger.error("Error (Get JST Product Template): %s", resp_data.get('message'))
                break
            
            data = resp_data.get('data') or []
            if data:
                # Create/Update product template
                self._update_product_template(data)

                # Check dataPage
                dp = resp_data.get('dataPage') or {}
                if dp.get('isLast', True):
                    break
                pageIndex = dp.get('pageIndex', pageIndex) + 1
                # Pending 1 second before calling API
                time.sleep(0.5)
            else:
                break

    def _update_product_template(self, data):
        synced_products = self.sudo().search([])
        synced_products_ids = synced_products.mapped('itemId')
        new_vals_list = []
        update_vals_list = []
        map_fields = self._map_fields()
        for line in data:
            new_line = {'raw_payload': line}
            for key, value in line.items():
                field_key = map_fields.get(key)
                if field_key:
                    if field_key in PRODUCT_TEAMPLATE_DATETIME_FIELDS:
                        value_dt = datetime.fromtimestamp(value, timezone.utc).replace(tzinfo=None) if value else False
                        new_line[field_key] = value_dt
                    elif field_key in PRODUCT_TEAMPLATE_LIST_OBJECT_FIELDS:
                        new_value = str(value) if value else ''
                        new_line[field_key] = new_value
                    else:
                        new_line[field_key] = value
            # Kiểm tra product đã đồng bộ về odoo chưa
            if new_line.get('itemId') in synced_products_ids:
                update_vals_list.append(new_line)
            else:
                new_vals_list.append(new_line)

        # Upsert theo trang trong savepoint để tránh rollback toàn bộ
        with self.env.cr.savepoint():
            # tạo product tempalte trên odoo
            if new_vals_list:
                self.sudo().create(new_vals_list)
            # update product tempalte đã có trên odoo, theo từng line
            if update_vals_list:
                for vals_line in update_vals_list:
                    product_template = synced_products.filtered(lambda r: r.itemId == vals_line.get('itemId'))
                    product_template.sudo().write(vals_line)

    def action_sync_products_by_ids(self, item_ids, enabled=True):
        """
        Tạo hoặc cập nhật product template theo item_ids được truyền vào
        item_ids: danh sách chuỗi itemIds: ["123", "124", ...]. Độ tài tối đa là 500
        """
        body_data = {
            "requestModel": {
                "enabled": bool(enabled),
                "itemIds": item_ids,
            },
            "dataPage": {
                "pageSize": 500,
                "pageIndex": 1
            }
        }
        resp_data = self.env['res.config.settings']._call_api_jst("/api/Goods/GetItemSkus", body_data)
        # Call API không thành công
        if not resp_data.get('success'):
            _logger.error("Error (Get JST Product Template): %s", resp_data.get('message'))
        else:
            data = resp_data.get('data') or []
            if data:
                # Create/Update product template
                self._update_product_template(data)

    def _map_fields(self):
        # key: JST API key, value: Odoo field name
        return {
            'companyId': 'companyId',
            'itemId': 'itemId',
            'itemName': 'itemName',
            'skuId': 'skuId',
            'name': 'name',
            'skuCode': 'skuCode',
            'fullName': 'fullName',
            'shortName': 'shortName',
            'brandName': 'brandName',
            'categoryName': 'categoryName',
            'vcName': 'vcName',
            'categoryPropertyContent': 'categoryPropertyContent',
            'averageCostPrice': 'averageCostPrice',
            'costPrice': 'costPrice',
            'lowestSalePrice': 'lowestSalePrice',
            'memberPrice': 'memberPrice',
            'nameplatePrice': 'nameplatePrice',
            'salePrice': 'salePrice',
            'wholesalePrice': 'wholesalePrice',
            'height': 'height',
            'length': 'length',
            'width': 'width',
            'cube': 'cube',
            'weight': 'weight',
            'weightUnit': 'weightUnit',
            'lowerLimitQty': 'lowerLimitQty',
            'upperLimitQty': 'upperLimitQty',
            'virtualQty': 'virtualQty',
            'safetyStockQty': 'safetyStockQty',
            'standardBoxQty': 'standardBoxQty',
            'expireWarningDay': 'expireWarningDay',
            'expiryDay': 'expiryDay',
            'isVerifyShelfLife': 'isVerifyShelfLife',
            'enabled': 'enabled',
            'isAllowLessthencost': 'isAllowLessthencost',
            'isCombined': 'isCombined',
            'isInspection': 'isInspection',
            'isOnPurchaseSale': 'isOnPurchaseSale',
            'isStockSync2wms': 'isStockSync2wms',
            'lableString': 'lableString',
            'propertyNameString': 'propertyNameString',
            'propertyShortName': 'propertyShortName',
            'propertyValueString': 'propertyValueString',
            'customProperty1': 'customProperty1',
            'customProperty2': 'customProperty2',
            'customProperty3': 'customProperty3',
            'customProperty4': 'customProperty4',
            'picture': 'picture',
            'picturesString': 'picturesString',
            'barCode': 'barCode',
            'supplierCode': 'supplierCode',
            'supplierName': 'supplierName',
            'unit': 'unit',
            'created': 'created',
            'creator': 'creator',
            'modified': 'jst_modified',
            'modifier': 'modifier',
            'bagCodes': 'bagCodes',
            'auxiliaryCodes': 'auxiliaryCodes',
        }

    def action_sync_this_product(self):
        self.action_sync_products_by_ids(self.mapped('itemId'))
        self.env['jst.product.template'].action_sync_products_by_ids(self.mapped('itemId'))

    def _action_sync_jst_products_daily(self):
        ts_end = int(fields.Datetime.now().timestamp())
        ts_start = ts_end - 25*3600
        self.env['jst.product.template'].sudo().action_sync_jst_products(ts_start, ts_end, True)
        time.sleep(1)
        self.env['jst.product.template'].sudo().action_sync_jst_products(ts_start, ts_end, False)
        time.sleep(1)
        self.env['jst.product.product'].sudo().action_sync_jst_products(ts_start, ts_end)
