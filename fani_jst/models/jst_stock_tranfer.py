import logging
from datetime import datetime, timezone
import time
from odoo import models, fields

_logger = logging.getLogger(__name__)

JST_STOCK_TRANFER_DATETIME_FIELDS = ['created', 'jst_modified', 'revieweDate']
JST_STOCK_TRANFER_CONVERT_TO_STRING = ['allocationId']

JST_STOCK_TRANFER_DETAIL_DATETIME_FIELDS = ['created', 'jst_modified']
JST_STOCK_TRANFER_DETAIL_STRING_TO_DATETIME_FIELDS = ['producedDate']
JST_STOCK_TRANFER_DETAIL_CONVERT_TO_STRING = ['allocationItemId', 'allocationId']


class JstStockTranfer(models.Model):
    # docs: https://www.showdoc.com.cn/jsterp/7258080998815838
    _name = 'jst.stock.tranfer'
    _description = 'JST Stock Transfer'

    jst_stock_tranfer_detail_ids = fields.One2many('jst.stock.tranfer.detail', 'jst_stock_tranfer_id', string='JST Stock Transfer Details')
    raw_payload = fields.Json(string='Raw Payload')

    # ==== Fields from API ====
    allocationId = fields.Char(string='Transfer ID', help='Transfer order number', index=True)
    allocationStatus = fields.Char(string='Transfer Status', help='Transfer order status', index=True)
    allocationTotalQty = fields.Integer(string='Transfer Total Quantity', help='Total quantity allocated')
    auditer = fields.Integer(string='Auditer', help='Reviewer')
    companyId = fields.Integer(string='Company ID', help='Company Number')
    comment = fields.Text(string='Comment', help='Remark')
    createType = fields.Char(string='Create Type', help='Create Type', index=True)
    created = fields.Datetime(string='Created Date', help='Creation time')
    creator = fields.Integer(string='Creator', help='Creator Number', aggregator=None)
    enabled = fields.Boolean(string='Enabled', default=True, help='Is it enabled?')
    freightCost = fields.Float(string='Freight Cost', help='Freight')
    inLinkWarehouseId = fields.Integer(string='In Link Warehouse ID', help='Associated warehouse id_in')
    inQty = fields.Integer(string='In Quantity', help='Quantity received')
    inStatus = fields.Char(string='In Status', help='Warehouse status', index=True)
    inWarehouseId = fields.Integer(string='In Warehouse ID', help='Transfer warehouse ID', index=True)
    inWarehouseName = fields.Char(string='In Warehouse Name', help='Transfer-in warehouse name', index=True)
    linkCoId = fields.Integer(string='Link Company ID', help='Associated merchant id')
    logisticsCompanyCode = fields.Char(string='Logistics Company Code', help='Courier company code')
    logisticsCompanyName = fields.Char(string='Logistics Company Name', help='Courier Company Name')
    logisticsNo = fields.Char(string='Logistics Number', help='Logistics order number')
    jst_modified = fields.Datetime(string='Modified Date', help='Modification time')
    modifier = fields.Integer(string='Modifier', help='Modifier Number')
    orderType = fields.Char(string='Order Type', help='Document Type', index=True)
    outLinkWarehouseId = fields.Integer(string='Out Link Warehouse ID', help='Associated warehouse id_out')
    outQty = fields.Integer(string='Out Quantity', help='Quantity shipped')
    outStatus = fields.Char(string='Out Status', help='Outbound status', index=True)
    outType = fields.Char(string='Out Type', help='Outbound type', index=True)
    outWarehouseId = fields.Integer(string='Out Warehouse ID', help='Retrieve warehouse ID', index=True)
    outWarehouseName = fields.Char(string='Out Warehouse Name', help='Retrieve warehouse name', index=True)
    printCount = fields.Integer(string='Print Count', help='Number of prints')
    revieweDate = fields.Datetime(string='Review Date', help='Review time', index=True)
    warehouseArea = fields.Char(string='Warehouse Area', help='Default receiving warehouse area')

    def _sync_jst_stock_tranfers(self, requestModel, pageIndex=1):
        """
        Sync JST Stock Transfers
        """
        start_dt = datetime.now()
        _logger.info("Sync JST Stock Transfer: Bắt đầu đồng bộ phiếu chuyển JST ...")
        all_allocationIds = 0
        while True:
            body_data = {
                "requestModel": requestModel,
                "dataPage": {
                    "pageSize": 500,
                    "pageIndex": pageIndex
                }
            }
            # Get Stock Transfers
            resp_data = self.env['res.config.settings']._call_api_jst("/api/Allocation/GetAllocations", body_data)
            
            # Call API không thành công
            if not resp_data.get('success'):
                _logger.error("Sync JST Stock Transfer: Error (Get Stock Transfers): %s", resp_data.get('message'))
                break
            
            data = resp_data.get('data') or []
            if data:
                sync_max500_start = datetime.now()
                # Lấy danh sách allocationId đã được update
                allocationId_list = self._update_jst_stock_tranfers(data)
                total_allocationIds = len(allocationId_list)
                all_allocationIds += total_allocationIds

                # Đảm bảo max 200 ids 1 lần update
                # Update chi tiết phiếu chuyển theo allocationId_list đã update  trước đó
                while allocationId_list:
                    self._update_jst_stock_tranfer_details(allocationId_list[:200])
                    allocationId_list = allocationId_list[200:] # Bỏ 200 phần tử đầu tiên
                
                sync_max500_end = datetime.now()
                _logger.info("Sync JST Stock Transfer: Đã đồng bộ %s phiếu chuyển -> %s (s)", total_allocationIds, (sync_max500_end - sync_max500_start).total_seconds())

                # Check dataPage
                dp = resp_data.get('dataPage') or {}
                if dp.get('isLast', True):
                    break
                pageIndex = dp.get('pageIndex', pageIndex) + 1
            else:
                break
        
        end_dt = datetime.now()
        _logger.info("Sync JST Stock Transfer: Kết thúc đồng bộ phiếu chuyển -> %s phiếu chuyển-> %s (s)", all_allocationIds, (end_dt - start_dt).total_seconds())

    def _update_jst_stock_tranfers(self, data):
        """
        Update JST Stock Transfers
        """
        # Lấy danh sách allocationId từ data sync
        allocationId_list = [str(item["allocationId"]) for item in data if item.get("allocationId", False)]
        # Tìm trong DB các allocationId đã tồn tại (chỉ load id + allocationId)
        existing_allocations = self.sudo().search_read(
            domain=[('allocationId', 'in', allocationId_list)],
            fields=['id', 'allocationId']
        )
        existing_allocation_map = {o['allocationId']: o['id'] for o in existing_allocations}
        
        new_vals_list = []
        update_vals_list = []
        map_fields = self._map_fields()
        allocationId_to_update_lines = []

        # Duyệt qua data của từng Allocation
        for line in data:
            allocationId = line.get("allocationId")
            if not allocationId:
                continue
            allocationId_str = str(allocationId)

            # Add id vào danh sách cần update detail
            allocationId_to_update_lines.append(allocationId)

            jst_allocation = {
                'raw_payload': line
            }
            # Map field - value chính của model
            for key, value in line.items():
                field_key = map_fields.get(key)
                if field_key:
                    if field_key in JST_STOCK_TRANFER_DATETIME_FIELDS:
                        value_dt = datetime.fromtimestamp(value, timezone.utc).replace(tzinfo=None) if value else False
                        jst_allocation[field_key] = value_dt
                    elif field_key in JST_STOCK_TRANFER_CONVERT_TO_STRING:
                        jst_allocation[field_key] = str(value)
                    else:
                        jst_allocation[field_key] = value

            if allocationId_str in existing_allocation_map:
                update_vals_list.append((existing_allocation_map[allocationId_str], jst_allocation))
            else:
                new_vals_list.append(jst_allocation)
        
        with self.env.cr.savepoint():
            if new_vals_list:
                self.sudo().create(new_vals_list)
            for allocation_id, vals in update_vals_list:
                allocation = self.browse(allocation_id)
                allocation.sudo().write(vals)
            self.flush_model()
        return allocationId_to_update_lines

    def _update_jst_stock_tranfer_details(self, allocationId_list):
        """
        Sync JST Stock Transfer Details: max 200 allocationIds 1 lần
        """
        body_data = {
            "AllocationIds": allocationId_list
        }
        # Get Allocation Items
        resp_data = self.env['res.config.settings']._call_api_jst("/api/Allocation/GetAllocationDetail", body_data)
        
        # Call API không thành công
        if not resp_data.get('success'):
            _logger.error("Sync JST Stock Transfer: Error (Get JST Stock Transfer Details): %s", resp_data.get('message'))
            return
        
        data = resp_data.get('data') or []
        if data:
            # Lấy danh sách allocationId từ data sync
            allocationId_list_incoming = [str(line['allocationId']) for line in data if line.get('allocationId')]
            # Tìm trong DB các allocationId đã tồn tại (chỉ load id + allocationId)
            existing_allocations = self.sudo().search_read(
                domain=[('allocationId', 'in', allocationId_list_incoming)],
                fields=['id', 'allocationId']
            )
            existing_allocation_map = {o['allocationId']: o['id'] for o in existing_allocations}

            new_vals_list = []
            map_fields = self.env['jst.stock.tranfer.detail']._map_fields()
            # Duyệt qua data của từng Allocation details
            for line in data:
                allocationId = line.get('allocationId')
                if not allocationId:
                    continue
                allocationId_str = str(allocationId)

                vals_line = {
                    'raw_payload': line,
                    'jst_stock_tranfer_id': existing_allocation_map.get(allocationId_str, False)
                }
                for key, value in line.items():
                    field_key = map_fields.get(key)
                    if field_key:
                        if field_key in JST_STOCK_TRANFER_DETAIL_DATETIME_FIELDS:
                            value_dt = datetime.fromtimestamp(value, timezone.utc).replace(tzinfo=None) if value else False
                            vals_line[field_key] = value_dt
                        elif field_key in JST_STOCK_TRANFER_DETAIL_STRING_TO_DATETIME_FIELDS:
                            # valuse = '2025-01-01T08:05:00+08:05' -> convert to datetime
                            value_dt = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S%z') if value else False
                            # value_dt = datetime.datetime(2025, 1, 1, 8, 5, tzinfo=datetime.timezone(datetime.timedelta(seconds=29100)))
                            value_dt = value_dt.replace(tzinfo=None)
                            if value_dt.year > 2010:
                                vals_line[field_key] = False
                            vals_line[field_key] = value_dt
                        elif field_key in JST_STOCK_TRANFER_DETAIL_CONVERT_TO_STRING:
                            vals_line[field_key] = str(value)
                        else:
                            vals_line[field_key] = value
                new_vals_list.append(vals_line)
            
            # Xóa các tranfer detail đã được update để tạo lại
            jst_stock_tranfer_detail_remove = self.env['jst.stock.tranfer.detail'].search([('allocationId', 'in', allocationId_list_incoming)])
            if jst_stock_tranfer_detail_remove:
                jst_stock_tranfer_detail_remove.unlink()

            # Tạo/Tạo lại các tranfer detail
            if new_vals_list:
                with self.env.cr.savepoint():
                    self.env['jst.stock.tranfer.detail'].sudo().create(new_vals_list)

    def _map_fields(self):
        # key: JST API key, value: Odoo field name
        return {
            'allocationId': 'allocationId',
            'allocationStatus': 'allocationStatus',
            'allocationTotalQty': 'allocationTotalQty',
            'auditer': 'auditer',
            'companyId': 'companyId',
            'comment': 'comment',
            'createType': 'createType',
            'created': 'created',
            'creator': 'creator',
            'enabled': 'enabled',
            'freightCost': 'freightCost',
            'inLinkWarehouseId': 'inLinkWarehouseId',
            'inQty': 'inQty',
            'inStatus': 'inStatus',
            'inWarehouseId': 'inWarehouseId',
            'inWarehouseName': 'inWarehouseName',
            'linkCoId': 'linkCoId',
            'logisticsCompanyCode': 'logisticsCompanyCode',
            'logisticsCompanyName': 'logisticsCompanyName',
            'logisticsNo': 'logisticsNo',
            'modified': 'jst_modified',
            'modifier': 'modifier',
            'orderType': 'orderType',
            'outLinkWarehouseId': 'outLinkWarehouseId',
            'outQty': 'outQty',
            'outStatus': 'outStatus',
            'outType': 'outType',
            'outWarehouseId': 'outWarehouseId',
            'outWarehouseName': 'outWarehouseName',
            'printCount': 'printCount',
            'revieweDate': 'revieweDate',
            'warehouseArea': 'warehouseArea',
        }

    def _cron_sync_jst_stock_tranfers(self, duration_hours=24):
        """
        Đồng bộ phiếu chuyển trong vòng 1 ngày
        - theo thời gian cập nhật trên JST
        """
        ConfigParamater = self.env['ir.config_parameter'].sudo()
        ts_start = int(ConfigParamater.get_param('jst.next_ts_sync_stock_tranfer', '0'))
        if not ts_start:
            return
        dt_now = fields.Datetime.now()
        ts_now = int(dt_now.timestamp())
        if ts_now < ts_start:
            return
        ts_end = ts_start + duration_hours*3600
        if ts_end > ts_now:
            ts_end = ts_now
        
        requestModel = {
            "ModifiedBegin": ts_start,
            "modifiedEnd": ts_end
        }
        # Đồng bộ phiếu chuyển JST
        _logger.info("Sync JST Stock Transfer: Cron Job -> Đồng bộ phiếu chuyển JST ...")
        self.env['jst.stock.tranfer']._sync_jst_stock_tranfers(requestModel)

        # Đồng bộ phiếu chuyển JST Out InOut
        _logger.info("Sync JST Stock Transfer: Cron Job -> Đồng bộ phiếu chuyển JST Out InOut ...")
        self.env['jst.stock.inout']._sync_jst_transfer_out_inouts(requestModel)

        # Đồng bộ phiếu chuyển JST In InOut
        _logger.info("Sync JST Stock Transfer: Cron Job -> Đồng bộ phiếu chuyển JST In InOut ...")
        self.env['jst.stock.inout']._sync_jst_transfer_in_inouts(requestModel)


class JstStockTranferDetail(models.Model):
    # docs: https://www.showdoc.com.cn/jsterp/7258085271720274
    _name = 'jst.stock.tranfer.detail'
    _description = 'JST Stock Transfer Detail'

    jst_stock_tranfer_id = fields.Many2one('jst.stock.tranfer', string='JST Stock Transfer', ondelete='cascade', index=True)

    raw_payload = fields.Json(string='Raw Payload')

    # ==== Fields from API ====
    allocationId = fields.Char(string='Transfer ID', help='Transfer order number', index=True)
    allocationItemId = fields.Char(string='Transfer Item ID', help='Transfer order table ID', index=True)
    allocationQty = fields.Integer(string='Transfer Quantity', help='Transfer quantity')
    boxCapacity = fields.Integer(string='Box Capacity', help='Standard packing quantity')
    boxQuantity = fields.Integer(string='Box Quantity', help='Box quantity')
    companyId = fields.Integer(string='Company ID', help='Company Number')
    costPrice = fields.Float(string='Cost Price', help='Cost price')
    created = fields.Datetime(string='Created Date', help='Creation time')
    creator = fields.Integer(string='Creator', help='Creator Number')
    enabled = fields.Boolean(string='Enabled', default=True, help='Is it enabled?')
    inQty = fields.Integer(string='In Quantity', help='Quantity received')
    itemId = fields.Char(string='Item ID', help='Style Code', index=True)
    itemName = fields.Char(string='Item Name', help='Style Name', index=True)
    itemShortname = fields.Char(string='Item Short Name', help='Style Abbreviation')
    jst_modified = fields.Datetime(string='Modified Date', help='Modification time')
    modifier = fields.Integer(string='Modifier', help='Modifier Number')
    outQty = fields.Integer(string='Out Quantity', help='Quantity shipped')
    producedDate = fields.Datetime(string='Produced Date', help='Production Date 2', index=True)
    salePrice = fields.Float(string='Sale Price', help='Basic selling price', index=True)
    skuBatchId = fields.Char(string='SKU Batch ID', help='Product batch ID')
    skuId = fields.Char(string='SKU ID', help='Product Number', index=True)
    skuName = fields.Char(string='SKU Name', help='Product Name', index=True)
    skuPic = fields.Char(string='SKU Picture', help='Product images')
    skuPropertyName = fields.Char(string='SKU Property Name', help='Product attribute name')

    def _map_fields(self):
        # key: JST API key, value: Odoo field name
        return {
            'allocationId': 'allocationId',
            'allocationItemId': 'allocationItemId',
            'allocationQty': 'allocationQty',
            'boxCapacity': 'boxCapacity',
            'boxQuantity': 'boxQuantity',
            'companyId': 'companyId',
            'costPrice': 'costPrice',
            'created': 'created',
            'creator': 'creator',
            'enabled': 'enabled',
            'inQty': 'inQty',
            'itemId': 'itemId',
            'itemName': 'itemName',
            'itemShortname': 'itemShortname',
            'modified': 'jst_modified',
            'modifier': 'modifier',
            'outQty': 'outQty',
            'producedDate': 'producedDate',
            'salePrice': 'salePrice',
            'skuBatchId': 'skuBatchId',
            'skuId': 'skuId',
            'skuName': 'skuName',
            'skuPic': 'skuPic',
            'skuPropertyName': 'skuPropertyName',
        }