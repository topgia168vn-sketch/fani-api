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

PRODUCT_INVENTORY_DATETIME_FIELDS = ['created', 'jst_modified'] # -> DATETIME OBJECT
ORDER_LIST_OBJECT_FIELDS = ['combineSkuIds'] # -> "[X, Y, X]"


class JstProductInventory(models.Model):
    _name = 'jst.product.inventory'
    _description = 'JST Product Inventory'
    _rec_name = 'skuId'

    # Core identifiers
    itemId = fields.Char("Style Code")
    skuId = fields.Char("Product Code")
    
    # Quantities
    qty = fields.Integer("Main Warehouse Qty")
    defectiveQty = fields.Integer("Number of Defective")
    inQty = fields.Integer("Qty of Incoming")
    orderLock = fields.Integer("Order Possession")
    purchaseQty = fields.Integer("Purchase qty in Transit")
    returnQty = fields.Integer("Sales and Return")
    virtualQty = fields.Integer("Virtual")
    
    # Related products
    combineSkuIds = fields.Text(string='Combine SKU IDs', help="Related Combination Pack Product Code")
    
    # Timestamps
    created = fields.Datetime("Creation Time")
    jst_modified = fields.Datetime("Update Time")

    raw_payload = fields.Json(
        string="Raw Payload",
        help="Full JSON order object as returned by API"
    )

    def action_sync_jst_product_inventory(self, modifiedBegin, modifiedEnd, pageIndex=1):
        """
        Đồng bộ product inventory theo:
            - itemIds: danh sách string
            - skuIds: danh sách string
        """
        while True:
            body_data = {
                "requestModel": {
                    "modifiedBegin": modifiedBegin,
                    "modifiedEnd": modifiedEnd
                },
                "dataPage": {
                  "pageSize": 500,
                  "pageIndex": pageIndex
                }
            }
            resp_data = self.env['res.config.settings']._call_api_jst("/api/Inventory/GetSkuinventorys", body_data)

            # Call API không thành công
            if not resp_data.get('success'):
                _logger.error("Error (Get JST Product Inventory): %s", resp_data.get('message'))
                break
            
            data = resp_data.get('data') or []
            if data:
                # Create/Update product inventory
                self._update_product_inventory(data)

                # Check dataPage
                dp = resp_data.get('dataPage') or {}
                if dp.get('isLast', True):
                    break
                pageIndex = dp.get('pageIndex', pageIndex) + 1
                # Pending 0.5 second before calling API
                time.sleep(0.5)
            else:
                break

    def _update_product_inventory(self, data):
        # Lấy danh sách tuple từ data sync
        itemId_list = []
        skuId_list = []
        
        for row in data:
            itemId_list.append(row.get('itemId'))
            skuId_list.append(row.get('skuId'))
        
        # Tìm trong DB các inventory đã tồn tại (chỉ load id + itemId + skuId)
        existing_inventories = self.sudo().search_read(
            domain=[('itemId', 'in', itemId_list), ('skuId', 'in', skuId_list)],
            fields=['id', 'itemId', 'skuId']
        )
        existing_inventory_map = {}
        for inv in existing_inventories:
            key = "%s_*^%s" % (inv['itemId'], inv['skuId'])
            existing_inventory_map[key] = inv['id']
        
        new_vals_list = []
        update_vals_list = []
        map_fields = self._map_fields()

        for line in data:
            new_line = {'raw_payload': line}
            for key, value in line.items():
                field_key = map_fields.get(key)
                if field_key:
                    if field_key in PRODUCT_INVENTORY_DATETIME_FIELDS:
                        value_dt = datetime.fromtimestamp(value, timezone.utc).replace(tzinfo=None) if value else False
                        new_line[field_key] = value_dt
                    elif field_key in ORDER_LIST_OBJECT_FIELDS:
                        new_value = str(value) if value else ''
                        new_line[field_key] = new_value
                    else:
                        new_line[field_key] = value
            
            # Kiểm tra product inventory đã đồng bộ về odoo chưa (dựa vào itemId và skuId)
            inv_key = f"{line.get('itemId')}_*^{line.get('skuId')}"
            if inv_key in existing_inventory_map:
                update_vals_list.append((existing_inventory_map[inv_key], new_line))
            else:
                new_vals_list.append(new_line)

        # Thực hiện DB transaction
        with self.env.cr.savepoint():
            if new_vals_list:
                self.sudo().create(new_vals_list)
            for inv_id, vals in update_vals_list:
                inventory = self.browse(inv_id)
                inventory.sudo().write(vals)

    def _map_fields(self):
        # key: JST API key, value: Odoo field name
        return {
            'itemId': 'itemId',
            'skuId': 'skuId',
            'qty': 'qty',
            'defectiveQty': 'defectiveQty',
            'inQty': 'inQty',
            'orderLock': 'orderLock',
            'purchaseQty': 'purchaseQty',
            'returnQty': 'returnQty',
            'virtualQty': 'virtualQty',
            'combineSkuIds': 'combineSkuIds',
            'created': 'created',
            'modified': 'jst_modified',
        }

    def _sync_jst_product_inventory(self):
        ts_dt_end = int(datetime.now().timestamp())
        ts_dt_start = ts_dt_end - 24*3600 - 60  # đồng bộ trong vòng 1 ngày vừa qua
        self.action_sync_jst_product_inventory(ts_dt_start, ts_dt_end)
