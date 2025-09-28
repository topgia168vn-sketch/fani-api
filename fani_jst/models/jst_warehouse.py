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

WAREHOUSE_DATETIME_FIELDS = ['created', 'jst_modified'] # -> DATETIME OBJECT


class JstWarehouse(models.Model):
    _name = 'jst.warehouse'
    _description = 'JST Warehouse'
    _rec_name = 'warehouseName'

    # Basic info from API
    companyId = fields.Integer("Merchant ID", aggregator=None)
    country = fields.Char("Nation")
    province = fields.Char("Province")
    city = fields.Char("City")
    district = fields.Char("District")
    address = fields.Char("Address")
    contactName = fields.Char("Contact")
    mobile = fields.Char("Contact Number")
    warehouseId = fields.Integer("Warehouse ID", aggregator=None)
    warehouseName = fields.Char("Warehouse Name")
    warehouseShortName = fields.Char("Warehouse Abbreviation Name")
    warehouseType = fields.Char("Warehouse Type")
    warehouseServerCode = fields.Char("Warehouse Service Number")
    
    # Timestamps
    jst_modified = fields.Datetime("Modification Time")
    created = fields.Datetime("Creation Time")

    # Toàn bộ payload đơn (để lần vết đầy đủ)
    raw_payload = fields.Json(
        string="Raw Payload",
        help="Full JSON order object as returned by API"
    )

    def action_sync_jst_warehouses(self, WarehouseId=False):
        """
        Đồng bộ warehouses theo thời gian
        """
        body_data = {}
        if WarehouseId:
            body_data["WarehouseId"] = WarehouseId
        resp_data = self.env['res.config.settings']._call_api_jst("/api/Warehouse/GetWarehouses", body_data)

        if resp_data.get('success'):
            data = resp_data.get('data') or []
            if data:
                self._update_jst_warehourse(data)
        else:
            error_msg = resp_data.get('message', 'Unknown error')
            _logger.error("Error (Get JST Warehouses): %s", error_msg)

    def _update_jst_warehourse(self, data):
        # Lấy danh sách warehouse từ data sync
        warehouse_ids_incoming = [line.get('warehouseId') for line in data if line.get('warehouseId')]
        # Tìm trong DB các order đã tồn tại (chỉ load id + orderId)
        existing_warehouses = self.sudo().search_read(
            domain=[('warehouseId', 'in', warehouse_ids_incoming)],
            fields=['id', 'warehouseId']
        )
        existing_warehouse_map = {w['warehouseId']: w['id'] for w in existing_warehouses}
        
        new_vals_list = []
        update_vals_list = []
        map_fields = self._map_fields()
        
        for line in data:
            new_line = {'raw_payload': line}
            for key, value in line.items():
                field_key = map_fields.get(key)
                if field_key:
                    if field_key in WAREHOUSE_DATETIME_FIELDS:
                        if isinstance(value, (int, float)) and value > 0:
                            value_dt = datetime.fromtimestamp(value, timezone.utc).replace(tzinfo=None) if value else False
                            new_line[field_key] = value_dt
                        else:
                            new_line[field_key] = False
                    else:
                        new_line[field_key] = value
            
            # Kiểm tra warehouse đã đồng bộ về odoo chưa
            warehouse_id = new_line.get('warehouseId')
            if warehouse_id in existing_warehouse_map:
                update_vals_list.append((existing_warehouse_map[warehouse_id], new_line))
            else:
                new_vals_list.append(new_line)
        
        with self.env.cr.savepoint():
            # tạo warehouse trên odoo
            if new_vals_list:
                self.env['jst.warehouse'].sudo().create(new_vals_list)
            # update warehouse đã có trên odoo, theo từng line
            for wh, vals in update_vals_list:
                jst_warehouse = self.browse(wh)
                jst_warehouse.sudo().write(vals)

    def action_sync_warehouses_by_ids(self):
        for r in self:
            r.action_sync_jst_warehouses(WarehouseId=r.WarehouseId)

    def _map_fields(self):
        # key: JST API key, value: Odoo field name
        return {
            'companyId': 'companyId',
            'country': 'country',
            'province': 'province',
            'city': 'city',
            'district': 'district',
            'address': 'address',
            'contactName': 'contactName',
            'mobile': 'mobile',
            'warehouseId': 'warehouseId',
            'warehouseName': 'warehouseName',
            'warehouseShortName': 'warehouseShortName',
            'warehouseType': 'warehouseType',
            'warehouseServerCode': 'warehouseServerCode',
            'modified': 'jst_modified',
            'created': 'created',
        }

    def _action_sync_jst_warehouses_weekly(self):
        """Daily sync for warehouses"""
        self.action_sync_jst_warehouses()
