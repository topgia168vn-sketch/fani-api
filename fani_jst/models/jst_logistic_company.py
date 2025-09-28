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

LOGISTIC_COMPANY_DATETIME_FIELDS = ['created', 'jst_modified']

class JstLogisticCompany(models.Model):
    _name = 'jst.logistic.company'
    _description = 'JST Logistic Company'
    _rec_name = 'logisticsCompanyName'

    # Basic info from API
    autoId = fields.Integer("Auto ID", aggregator=None)
    companyId = fields.Integer("Company ID", aggregator=None)
    countryId = fields.Char("Country ID")
    logisticsCompanyId = fields.Integer("Logistics Company ID", aggregator=None)
    logisticsCompanyCode = fields.Char("Logistics Company Code")
    logisticsCompanyName = fields.Char("Logistics Company Name")
    enabled = fields.Boolean("Enabled")
    created = fields.Datetime("Creation Time")
    creator = fields.Integer("Creator", aggregator=None)
    jst_modified = fields.Datetime("Modification Time")
    modifier = fields.Integer("Modifier", aggregator=None)
    remark = fields.Text("Remark")
    connectionMode = fields.Char("Connection Mode")
    connectionModeDisplay = fields.Char("Connection Mode Display")
    createType = fields.Char("Create Type")
    waybillConfig = fields.Text("Electronic Waybill Configuration")
    isOfflineDocking = fields.Boolean("Is Offline Logistics Connected")
    isOpenAdvancePrint = fields.Boolean("Is Advanced Print Enabled")
    isAdvancePrintByDefault = fields.Boolean("Is Advanced Print By Default")
    platformApiExtendConfig = fields.Text("Platform API Extended Configuration")
    waterMark = fields.Char("Water Mark")

    # Toàn bộ payload đơn (để lần vết đầy đủ)
    raw_payload = fields.Json(
        string="Raw Payload",
        help="Full JSON logistic company object as returned by API"
    )

    def action_sync_jst_logistic_companies(self):
        """
        Đồng bộ logistic companies từ JST API
        """
        body_data = {
            "requestModel": {},
            "dataPage": {
              "pageSize": 500,
              "pageIndex": 1
            }
        }
        
        resp_data = self.env['res.config.settings']._call_api_jst("/api/LogisticsCompany/GetLogisticsCompanys", body_data)
        
        if resp_data.get('success'):
            if resp_data.get('data'):
                synced_companies = self.env['jst.logistic.company'].search([])
                synced_company_ids = synced_companies.mapped('logisticsCompanyId')
                new_vals_list = []
                update_vals_list = []
                map_fields = self._map_fields()
                
                for line in resp_data['data']:
                    new_line = {'raw_payload': line}
                    for key, value in line.items():
                        field_key = map_fields.get(key)
                        if field_key:
                            if field_key in LOGISTIC_COMPANY_DATETIME_FIELDS:
                                # Xử lý datetime string từ API
                                if isinstance(value, str) and value:
                                    try:
                                        # Parse ISO format datetime string
                                        # '2025-06-20T09:03:41.4+08:00'
                                        new_value = value.split('.')[0]
                                        new_value = new_value.split('+')[0]
                                        value_dt = datetime.fromisoformat(new_value)
                                        new_line[field_key] = value_dt
                                    except:
                                        new_line[field_key] = False
                                else:
                                    new_line[field_key] = False
                            else:
                                new_line[field_key] = value
                    
                    # Kiểm tra logistic company đã đồng bộ về odoo chưa
                    if new_line.get('logisticsCompanyId', 0) in synced_company_ids:
                        update_vals_list.append(new_line)
                    else:
                        new_vals_list.append(new_line)
                
                # Tạo logistic company trên odoo
                if new_vals_list:
                    self.env['jst.logistic.company'].sudo().create(new_vals_list)
                
                # Update logistic company đã có trên odoo, theo từng line
                if update_vals_list:
                    for vals_line in update_vals_list:
                        company = synced_companies.filtered(lambda r: r.logisticsCompanyId == vals_line.get('logisticsCompanyId', 0))
                        company.sudo().write(vals_line)
        else:
            error_msg = resp_data.get('message', 'Unknown error')
            _logger.error("Error (Get JST Logistic Companies): %s", error_msg)

    def _map_fields(self):
        # key: JST API key, value: Odoo field name
        return {
            'autoId': 'autoId',
            'companyId': 'companyId',
            'countryId': 'countryId',
            'logisticsCompanyId': 'logisticsCompanyId',
            'logisticsCompanyCode': 'logisticsCompanyCode',
            'logisticsCompanyName': 'logisticsCompanyName',
            'enabled': 'enabled',
            'created': 'created',
            'creator': 'creator',
            'modified': 'jst_modified',
            'modifier': 'modifier',
            'remark': 'remark',
            'connectionMode': 'connectionMode',
            'connectionModeDisplay': 'connectionModeDisplay',
            'createType': 'createType',
            'waybillConfig': 'waybillConfig',
            'isOfflineDocking': 'isOfflineDocking',
            'isOpenAdvancePrint': 'isOpenAdvancePrint',
            'isAdvancePrintByDefault': 'isAdvancePrintByDefault',
            'platformApiExtendConfig': 'platformApiExtendConfig',
            'waterMark': 'waterMark',
        }
