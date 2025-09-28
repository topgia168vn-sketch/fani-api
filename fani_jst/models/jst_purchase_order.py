import logging
from datetime import datetime, timezone
import time
from odoo import models, fields

_logger = logging.getLogger(__name__)

# Timestamp fields to convert from Unix timestamp for Purchase Order
JST_PURCHASE_ORDER_DATETIME_FIELDS = ['created', 'jst_modified', 'planArriveDate', 'purchaseFinishedDate', 'reviewDate', 'supplierConfirmDate']
JST_PURCHASE_ORDER_LINE_DATETIME_FIELDS = ['created', 'jst_modified', 'planArriveDate']
JST_PURCHASE_PROCESS_DATETIME_FIELDS = ['bussinessTime']

JST_PURCHASE_ORDER_ADD_FIELDS = ["thirdOrderNo"]

JST_PURCHASE_ORDER_CONVERT_TO_STRING = ['purchaseId', 'originalPurchaseId']


class JstPurchaseOrder(models.Model):
    _name = 'jst.purchase.order'
    _description = 'JST Purchase Order'
    _rec_name = 'purchaseId'
    _order = 'created desc,purchaseId desc'

    # One2many relationships
    jst_purchase_order_line_ids = fields.One2many(
        'jst.purchase.order.line',
        'jst_purchase_order_id',
        string='Purchase Order Lines',
        help="Product lines contained in the purchase order"
    )
    
    jst_purchase_process_ids = fields.One2many(
        'jst.purchase.order.process',
        'jst_purchase_order_id',
        string='Purchase Process',
        help="Process records for the purchase order"
    )

    # ==== Main Purchase Order Fields ====
    auditer = fields.Integer("Auditer", help="Reviewer ID")
    createType = fields.Char("Create Type", help="Purchase Order Creation Type (e.g., manual)")
    created = fields.Datetime("Created", help="Creation time", index=True)
    creator = fields.Integer("Creator", help="Creator ID")
    currencyId = fields.Char("Currency", help="Currency code (e.g., VND)")
    freightCost = fields.Float("Freight Cost", help="Freight cost")
    freightType = fields.Char("Freight Type", help="Mode of transportation")
    isPushToSupplier = fields.Boolean("Push To Supplier", help="Whether to push to suppliers")
    logisticsCompanyCode = fields.Char("Logistics Company Code", help="Courier company code")
    logisticsId = fields.Char("Logistics ID", help="Logistics order number")
    jst_modified = fields.Datetime("Modified", help="Modification time", index=True)
    modifier = fields.Integer("Modifier", help="Modifier ID")
    originalPurchaseId = fields.Char("Original Purchase ID", help="Related document number")
    planArriveDate = fields.Datetime("Plan Arrive Date", help="Planned delivery time")
    purchaseFinishedDate = fields.Datetime("Purchase Finished Date", help="Last delivery time")
    purchaseGoodsAmount = fields.Float("Purchase Goods Amount", help="Total amount of purchased goods")
    purchaseGoodsCount = fields.Integer("Purchase Goods Count", help="Total quantity of purchased goods")
    purchaseId = fields.Char("Purchase ID", help="Purchase order number", index=True)
    purchaseInoutQty = fields.Integer("Purchase Inout Qty", help="Actual quantity")
    purchaseOrderType = fields.Char("Purchase Order Type", help="Purchase order type (e.g., in)")
    purchaseOverloadRate = fields.Float("Purchase Overload Rate", help="Overfill ratio")
    purchaseStatus = fields.Char("Purchase Status", help="Purchase Order Status (e.g., completed)", index=True)
    purchaseTaxRate = fields.Float("Purchase Tax Rate", help="Purchase tax rate")
    purchaserName = fields.Char("Purchaser Name", help="Purchaser's name")
    receiptStatus = fields.Char("Receipt Status", help="Warehouse status (e.g., allstocked)", index=True)
    receiverAddress = fields.Text("Receiver Address", help="Delivery address")
    receiverCity = fields.Char("Receiver City", help="Delivery Address-City")
    receiverCountry = fields.Char("Receiver Country", help="Shipping Address-Country")
    receiverDistrict = fields.Char("Receiver District", help="Delivery Address-District")
    receiverMobile = fields.Char("Receiver Mobile", help="Consignee's phone number")
    receiverName = fields.Char("Receiver Name", help="Consignee's name")
    receiverPostcode = fields.Char("Receiver Postcode", help="Delivery address-zip code")
    receiverProvince = fields.Char("Receiver Province", help="Delivery Address-Province")
    receiverTown = fields.Char("Receiver Town", help="Delivery Address-Town")
    remark = fields.Text("Remark", help="Remark or note")
    reviewDate = fields.Datetime("Review Date", help="Review time")
    supplierCode = fields.Char("Supplier Code", help="Supplier Code", index=True)
    supplierConfirmDate = fields.Datetime("Supplier Confirm Date", help="Supplier confirmation time")
    supplierConfirmStatus = fields.Char("Supplier Confirm Status", help="Supplier confirmation status")
    supplierName = fields.Char("Supplier Name", help="Supplier Name", index=True)
    warehouseArea = fields.Char("Warehouse Area", help="Default receiving warehouse area")
    warehouseId = fields.Integer("Warehouse ID", help="Default receiving warehouse code", index=True)

    # Khác: nằm trong api danh sách lấy PO
    thirdOrderNo = fields.Char("External order number", help="External order number", index=True)

    # Full JSON response
    raw_payload = fields.Json(
        string="Raw Payload",
        help="Raw JSON payload of the purchase order returned by API"
    )

    def _sync_jst_purchase_orders(self, requestModel, pageIndex=1):
        """
        Lấy danh sách Purchase Orders cần đồng bộ
        """
        start_dt = datetime.now()
        _logger.info("Sync JST Purchase Order: Bắt đầu đồng bộ đơn mua ...")
        all_purchaseIds = [] # Gom tất cả ourder cần update
        all_data_by_purchaseId = {}
        while True:
            body_data = {
                "requestModel": requestModel,
                "dataPage": {
                  "pageSize": 500,
                  "pageIndex": pageIndex
                }
            }
            # Get Purchase Orders
            resp_data = self.env['res.config.settings']._call_api_jst("/api/Purchase/GetPurchaseOrders", body_data)

            # Call API không thành công
            if not resp_data.get('success'):
                _logger.error("Sync JST Purchase Order: Error (Get Orders): %s", resp_data.get('message'))
                break

            data = resp_data.get('data') or []
            if data:
                for item in data:
                    purchaseId = item.get("purchaseId", 0)
                    # Add purchaseId vào list
                    all_purchaseIds.append(purchaseId)
                    # Add more data vào dict
                    more_data = {}
                    for add_field in JST_PURCHASE_ORDER_ADD_FIELDS:
                        more_data[add_field] = item.get(add_field, False)
                    all_data_by_purchaseId[purchaseId] = more_data

                # Check dataPage
                dp = resp_data.get('dataPage') or {}
                if dp.get('isLast', True):
                    break
                pageIndex = dp.get('pageIndex', pageIndex) + 1
            else:
                break
        
        total_orders = len(all_purchaseIds)
        _logger.info("Sync JST Purchase Order: Cần đồng bộ %s purchase orders ...", total_orders)
        
        # Đồng bộ chi tiết 200 đơn 1 lần đến khi kết thúc
        if all_purchaseIds:
            while all_purchaseIds:
                check_dt_start = datetime.now()
                self._sync_jst_purchase_orders_detail(all_purchaseIds[:200], add_more_data=all_data_by_purchaseId)
                check_dt_end = datetime.now()
                _logger.info("Sync JST Purchase Order: Đã đồng bộ %s purchase orders -> %s (s)", len(all_purchaseIds[:200]), (check_dt_end-check_dt_start).total_seconds())
                all_purchaseIds = all_purchaseIds[200:] # Bỏ 200 phần tử đầu tiên

        end_dt = datetime.now()
        _logger.info("Sync JST Purchase Order: Kết thúc đồng bộ đơn mua -> %s orders-> %s (s)", total_orders, (end_dt - start_dt).total_seconds())

    def _sync_jst_purchase_orders_detail(self, purchaseId_list, add_more_data=None):
        # Tối đa 200 đơn hàng
        body_data = {
            'purchaseIds': purchaseId_list,
            'IsGetProcess': True
        }
        resp_data = self.env['res.config.settings']._call_api_jst("/api/Purchase/GetPurchaseOrderById", body_data)
        
        # Call API không thành công
        if not resp_data.get('success'):
            _logger.error("Sync JST Purchase Order: Error Get Order Detail: %s", resp_data.get('message'))
            return
        
        data = resp_data.get('data') or []
        if data:
            self._update_jst_purchase_orders(data, add_more_data=add_more_data)

    def _update_jst_purchase_orders(self, data, add_more_data=None):
        # Lấy danh sách purchaseId từ data sync
        purchase_ids_incoming = [str(line.get('purchaseId')) for line in data if line.get('purchaseId')]

        # Tìm trong DB các order đã tồn tại (chỉ load id + orderId)
        existing_orders = self.sudo().search_read(
            domain=[('purchaseId', 'in', purchase_ids_incoming)],
            fields=['id', 'purchaseId']
        )
        existing_orders_map = {o['purchaseId']: o['id'] for o in existing_orders}

        new_vals_list = []
        update_vals_list = []
        map_fields = self._map_fields()
        pol_map_fields = self.env['jst.purchase.order.line']._map_fields()
        pop_map_fields = self.env['jst.purchase.order.process']._map_fields()

        # Duyệt qua data của từng Purchase Order
        for line in data:
            purchase_order_id = line.get('purchaseId')
            purchase_order_id_str = str(purchase_order_id)
            if not purchase_order_id:
                continue

            jst_purchase_order = {'raw_payload': line}
            # Map field - value chính của model
            for key, value in line.items():
                field_key = map_fields.get(key)
                if field_key:
                    if field_key in JST_PURCHASE_ORDER_DATETIME_FIELDS:
                        value_dt = datetime.fromtimestamp(value, timezone.utc).replace(tzinfo=None) if value else False
                        jst_purchase_order[field_key] = value_dt
                    elif field_key in JST_PURCHASE_ORDER_CONVERT_TO_STRING:
                        jst_purchase_order[field_key] = str(value)
                    else:
                        jst_purchase_order[field_key] = value
            # Add thêm data vào PO (thường nằm ở API lấy danh sách PO)
            if add_more_data:
                add_field_vals = add_more_data.get(purchase_order_id, {})
                if add_field_vals:
                    jst_purchase_order.update(add_field_vals)

            # chuẩn hóa key-data của JST PO lines
            order_lines_data = []
            for item_data in line.get('purchaseOrderItemDetails', []):
                # Map field - value
                jst_purchase_order_line = {}
                for key, value in item_data.items():
                    field_key = pol_map_fields.get(key)
                    if field_key:
                        if field_key in JST_PURCHASE_ORDER_LINE_DATETIME_FIELDS:
                            value_dt = datetime.fromtimestamp(value, timezone.utc).replace(tzinfo=None) if value else False
                            jst_purchase_order_line[field_key] = value_dt
                        else:
                            if field_key == 'purchaseDetailId':
                                jst_purchase_order_line[field_key] = str(value)
                            else:
                                jst_purchase_order_line[field_key] = value
                if jst_purchase_order_line:
                    jst_purchase_order_line['purchaseId'] = purchase_order_id_str
                    order_lines_data.append(jst_purchase_order_line)

            # chuẩn hóa key-data của JST PO process
            process_lines_data = []
            for item_data in line.get('purchaseProcess', []):
                # Map field - value
                jst_purchase_order_process = {}
                for key, value in item_data.items():
                    field_key = pop_map_fields.get(key)
                    if field_key:
                        if field_key in JST_PURCHASE_ORDER_LINE_DATETIME_FIELDS:
                            value_dt = datetime.fromtimestamp(value, timezone.utc).replace(tzinfo=None) if value else False
                            jst_purchase_order_process[field_key] = value_dt
                        else:
                            jst_purchase_order_process[field_key] = value
                if jst_purchase_order_process:
                    jst_purchase_order_process['purchaseId'] = purchase_order_id_str
                    process_lines_data.append(jst_purchase_order_process)

            if order_lines_data:
                # order lines (các order lines cũ đã bị xóa)
                jst_purchase_order['jst_purchase_order_line_ids'] = [(0, 0, pol) for pol in order_lines_data]
            if process_lines_data:
                # process lines (các process lines cũ đã bị xóa)
                jst_purchase_order['jst_purchase_process_ids'] = [(0, 0, pop) for pop in process_lines_data]

            # Update order đã tồn tại
            if purchase_order_id_str in existing_orders_map:
                # Add tuple to list
                update_vals_list.append((existing_orders_map[purchase_order_id_str], jst_purchase_order))
            # Chưa đồng bộ: tạo mới
            else:
                # Add dict to list
                new_vals_list.append(jst_purchase_order)

        # search tất cả order lines, process lines và cho chim cook thay vì dùng lệnh (5, 0, 0), giúp giảm update 200 orders từ 50s xuống còn khoảng dưới 5s
        jst_PO_lines_remove = self.env['jst.purchase.order.line'].search([('purchaseId', 'in', purchase_ids_incoming)])
        if jst_PO_lines_remove:
            jst_PO_lines_remove.unlink()
        jst_PO_process_remove = self.env['jst.purchase.order.process'].search([('purchaseId', 'in', purchase_ids_incoming)])
        if jst_PO_process_remove:
            jst_PO_process_remove.unlink()

        with self.env.cr.savepoint():
            # Create new orders
            if new_vals_list:
                self.sudo().create(new_vals_list)
            # Update orders
            for order_id, vals in update_vals_list:
                order = self.browse(order_id)
                order.sudo().write(vals)

    def _map_fields(self):
        # key: JST API key, value: Odoo field name
        return {
            'auditer': 'auditer',
            'createType': 'createType',
            'created': 'created',
            'creator': 'creator',
            'currencyId': 'currencyId',
            'freightCost': 'freightCost',
            'freightType': 'freightType',
            'isPushToSupplier': 'isPushToSupplier',
            'logisticsCompanyCode': 'logisticsCompanyCode',
            'logisticsId': 'logisticsId',
            'modified': 'jst_modified',
            'modifier': 'modifier',
            'originalPurchaseId': 'originalPurchaseId',
            'planArriveDate': 'planArriveDate',
            'purchaseFinishedDate': 'purchaseFinishedDate',
            'purchaseGoodsAmount': 'purchaseGoodsAmount',
            'purchaseGoodsCount': 'purchaseGoodsCount',
            'purchaseId': 'purchaseId',
            'purchaseInoutQty': 'purchaseInoutQty',
            'purchaseOrderType': 'purchaseOrderType',
            'purchaseOverloadRate': 'purchaseOverloadRate',
            'purchaseStatus': 'purchaseStatus',
            'purchaseTaxRate': 'purchaseTaxRate',
            'purchaserName': 'purchaserName',
            'receiptStatus': 'receiptStatus',
            'receiverAddress': 'receiverAddress',
            'receiverCity': 'receiverCity',
            'receiverCountry': 'receiverCountry',
            'receiverDistrict': 'receiverDistrict',
            'receiverMobile': 'receiverMobile',
            'receiverName': 'receiverName',
            'receiverPostcode': 'receiverPostcode',
            'receiverProvince': 'receiverProvince',
            'receiverTown': 'receiverTown',
            'remark': 'remark',
            'reviewDate': 'reviewDate',
            'supplierCode': 'supplierCode',
            'supplierConfirmDate': 'supplierConfirmDate',
            'supplierConfirmStatus': 'supplierConfirmStatus',
            'supplierName': 'supplierName',
            'warehouseArea': 'warehouseArea',
            'warehouseId': 'warehouseId',
        }

    def action_sync_purchase_inouts(self):
        self_todo = self.filtered(lambda r: r.purchaseId)
        purchaseId_list = self_todo.mapped('purchaseId')
        purchaseId_total = len(purchaseId_list)
        _logger.info("Sync JST InOut (Purchase): Đồng bộ Phiếu nhận của %s đơn mua.", purchaseId_total)
        start_dt = datetime.now()
        if purchaseId_list:
            path = "/api/Purchase/GetPurchaseInItems"
            while purchaseId_list :
                purchaseId_to_sync = purchaseId_list[:200]
                purchaseId_list = purchaseId_list[200:]
                self.env['jst.stock.inout']._sync_jst_inout_detail(path, PurchaseIds=purchaseId_to_sync)
        end_dt = datetime.now()
        _logger.info("Sync JST InOut (Purchase): Đã đồng bộ xong Phiếu nhận của %s đơn mua -> %s (s)", purchaseId_total, (end_dt-start_dt).total_seconds())
