import logging
from datetime import datetime, timezone
import time
from odoo import models, fields

_logger = logging.getLogger(__name__)

# Timestamp fields to convert from Unix timestamp
JST_INOUT_DATETIME_FIELDS = ['created', 'jst_modified', 'sendTime', 'inoutTime', 'orderDate']
# Các field dạng datetime (timestamp) từ API của model inout item
JST_INOUT_ITEM_DATETIME_FIELDS = ['producedDate']

# Các field kiểu long cần chuyển thành kiểu Char trong odoo
JST_INOUT_TO_STRING_FIELDS = ['inoutId']
JST_INOUT_ITEM_TO_STRING_FIELDS = ['inoutId', 'inoutItemId']

# các key nằm trong api get inout, không nằm trong API inout detail -> Add chung vào raw_payload
JST_INOUT_FIELDS_ADD = ['factFreight', 'modifier', 'outType', 'totalQty', 'modified',
                        'receiverCountry', 'receiverCity', 'receiverDistrict', 'receiverAddress', 'receiverPhone', 'receiverMobile', 'modifierName']




class JstStockInout(models.Model):
    _name = 'jst.stock.inout'
    _description = 'JST Stock In/Out'
    _rec_name = 'inoutId'
    _order = 'inoutId desc'

    jst_stock_inout_item_ids = fields.One2many(
        'jst.stock.inout.item',
        'jst_stock_inout_id',
        string='JST Stock InOut Items',
        help="Product lines contained in the stock in/out order"
    )

    # ==== Fields from dict 2 (in order) ====
    inoutId = fields.Char("InOut ID", help="Unique ID of the stock in/out order", index=True)
    orderId = fields.Integer("Order ID", help="Linked order ID", index=True)
    status = fields.Char("Status", help="Status code of the stock in/out", index=True)
    statusDisplay = fields.Char("Status Display", help="Status description returned by API")
    linkCoId = fields.Integer("Linked Company ID", help="Linked company ID")
    linkCompanyName = fields.Char("Linked Company Name", help="Linked company name")
    warehouseId = fields.Integer("Warehouse ID", help="Warehouse ID", index=True)
    shopId = fields.Integer("Shop ID", help="Shop ID handling the order", index=True)
    warehouseName = fields.Char("Warehouse Name", help="Warehouse name", index=True)
    supplierCode = fields.Char("Supplier Code", help="Supplier code")
    supplierName = fields.Char("Supplier Name", help="Supplier name")
    inoutTime = fields.Datetime("InOut Time", help="Time of stock in/out operation", index=True)
    orderDate = fields.Datetime("Order Date", help="Order creation date", index=True)
    areaType = fields.Char("Area Type", help="Warehouse type")
    areaTypeDisplay = fields.Char("Area Type Display", help="Warehouse type description")
    companyId = fields.Integer("Company ID", help="Company ID owning the order")
    currency = fields.Char("Currency", help="Currency code, e.g., CNY")
    type = fields.Char("Type", help="Business type (e.g., SaleOut)")
    typeDisplay = fields.Char("Type Display", help="Business type description")
    logisticsCompany = fields.Char("Logistics Company", help="Logistics company name")
    logisticsCompanyCode = fields.Char("Logistics Company Code", help="Logistics company code")
    logisticsId = fields.Char("Logistics ID", help="Tracking number or logistics ID")
    realQty = fields.Float("Real Quantity", help="Actual quantity")
    realTotalCostAmount = fields.Float("Real Total Cost Amount", help="Actual total cost")
    freight = fields.Float("Freight", help="Estimated freight cost")
    platformOrderId = fields.Char("Platform Order ID", help="Order ID from e-commerce platform")
    sendTime = fields.Datetime("Send Time", help="Time when goods were sent", index=True)
    qty = fields.Float("Quantity", help="Planned quantity")
    totalCostAmount = fields.Float("Total Cost Amount", help="Estimated total cost")
    totalAmount = fields.Float("Total Amount", help="Total order amount")
    paidAmount = fields.Float("Paid Amount", help="Paid amount")
    skuQty = fields.Float("SKU Quantity", help="Number of SKUs")
    created = fields.Datetime("Created", help="Record creation time", index=True)
    creatorName = fields.Char("Creator Name", help="User name who created the record")
    creator = fields.Integer("Creator ID", help="User ID who created the record")
    receiverName = fields.Char("Receiver Name", help="Receiver name")
    remark = fields.Text("Remark", help="Remark or note")
    platformName = fields.Char("Platform Name", help="E-commerce platform name")

    # ==== Extra fields from Delivery Sale Order
    factFreight = fields.Float("Fact Freight", help="Actual freight cost")
    jst_modified = fields.Datetime("Modified", help="Record last modification time", index=True)
    modifier = fields.Integer("Modifier ID", help="User ID who last modified the record")
    outType = fields.Char("Out Type", help="Out type, e.g., Deliver")
    totalQty = fields.Float("Total Quantity (Planned)", help="Total planned quantity")
    
    # ==== Extra fields from Delivery Purchase Order
    receiverCountry = fields.Char("Nation")
    receiverProvince = fields.Char("Province")
    receiverCity = fields.Char("City")
    receiverDistrict = fields.Char("district")
    receiverAddress = fields.Char("Recipient address")
    receiverPhone = fields.Char("Recipient's phone number")
    receiverMobile = fields.Char("Recipient's mobile phone number")
    modifierName = fields.Char("Founder", help="Founder")

    # Phiếu giao khác: https://www.showdoc.com.cn/jsterp/7834151469503121
    is_other_delivery = fields.Boolean(string='Is Other Delivery', default=False, index=True)

    # Khác: trường str để hiển thị
    orderId_str = fields.Char("Order Id ", index=True)

    # Full JSON response
    raw_payload = fields.Json(
        string="Raw Payload",
        help="Raw JSON payload of the stock in/out object returned by API"
    )

    def _sync_jst_sale_inouts(self, requestModel, pageIndex=1, only_create=False):
        """
        Đồng bộ Sale InOut
        docs: https://www.showdoc.com.cn/jsterp/8467743641028963
        """
        if not requestModel:
            _logger.info("Sync JST InOut (Sale): Không truyền tham số requestModel")
            return
        _logger.info("Sync JST InOut (Sale): Bắt đầu đồng bộ Inout Orders ...")
        path = "/api/Order/GetInoutItems"
        while True:
            body_data = {
                "requestModel": requestModel,
                "dataPage": {
                    "pageSize": 500,
                    "pageIndex": pageIndex
                }
            }
            resp_data = self.env['res.config.settings']._call_api_jst("/api/SaleInout/GetSaleInouts", body_data)

            if not resp_data.get('success'):
                _logger.error("Sync JST InOut (Sale): Error (Get InOuts Orders): %s", resp_data.get('message'))
                break

            data = resp_data.get('data') or []
            if data:
                total_inouts = len(data)
                while data :
                    data_max_200 = data[:200]
                    data = data[200:]
                    inout_ids = [item.get("inoutId", 0) for item in data_max_200]
                    inout_data_more = {item.get("inoutId", 0): item for item in data_max_200}
                    self._sync_jst_inout_detail(path, inoutIds=inout_ids, InoutDataMore=inout_data_more, only_create=only_create, is_other_delivery=False)
                _logger.info("Sync JST InOut (Sale): Page %s -> Đã đồng bộ %s inouts.", pageIndex, total_inouts)

                dp = resp_data.get('dataPage') or {}
                if dp.get('isLast', True):
                    break
                pageIndex = dp.get('pageIndex', pageIndex) + 1
            else:
                break
        _logger.info("Sync JST InOut (Sale): Kết thúc đồng bộ.")

    def _sync_jst_purchase_inouts(self, requestModel, pageIndex=1, only_create=False):
        """
        Đồng bộ Purchase InOut
        docs: https://www.showdoc.com.cn/jsterp/8137905247277435
        """
        if not requestModel:
            _logger.info("Sync JST InOut (Purchase): Không truyền tham số requestModel")
            return
        _logger.info("Sync JST Sale InOut (Purchase): Bắt đầu đồng bộ Inout Orders ...")
        path = "/api/Purchase/GetPurchaseInItems"
        while True:
            body_data = {
                "requestModel": requestModel,
                "dataPage": {
                    "pageSize": 500,
                    "pageIndex": pageIndex
                }
            }
            resp_data = self.env['res.config.settings']._call_api_jst("/api/Purchase/GetPurchaseInInouts", body_data)

            if not resp_data.get('success'):
                _logger.error("Sync JST Sale InOut (Purchase): Error (Get InOuts Orders): %s", resp_data.get('message'))
                break

            data = resp_data.get('data') or []
            if data:
                total_inouts = len(data)
                while data :
                    data_max_200 = data[:200]
                    data = data[200:]
                    inout_ids = [item.get("inoutId", 0) for item in data_max_200]
                    inout_data_more = {item.get("inoutId", 0): item for item in data_max_200}
                    self._sync_jst_inout_detail(path, inoutIds=inout_ids, InoutDataMore=inout_data_more, only_create=only_create, is_other_delivery=False)
                _logger.info("Sync JST InOut (Purchase): Page %s -> Đã đồng bộ %s inouts.", pageIndex, total_inouts)

                dp = resp_data.get('dataPage') or {}
                if dp.get('isLast', True):
                    break
                pageIndex = dp.get('pageIndex', pageIndex) + 1
            else:
                break
        _logger.info("Sync JST InOut (Purchase): Kết thúc đồng bộ.")

    def _sync_jst_other_inouts(self, requestModel, pageIndex=1, only_create=False):
        """
        Đồng bộ Stock Other InOut theo thời gian modified
        docs: https://www.showdoc.com.cn/jsterp/7834151469503121
        """
        if not requestModel:
            _logger.info("Sync JST InOut (Other): Không truyền tham số requestModel")
            return
        _logger.info("Sync JST Other InOut: Bắt đầu đồng bộ ...")
        path = "/api/OtherInoutOrder/GetOtherOutInoutItems"
        while True:
            body_data = {
                "requestModel": requestModel,
                "dataPage": {
                    "pageSize": 500,
                    "pageIndex": pageIndex
                }
            }
            resp_data = self.env['res.config.settings']._call_api_jst("/api/OtherInoutOrder/GetOtherOutInouts", body_data)

            if not resp_data.get('success'):
                _logger.error("Sync JST InOut (Other): Error Call API Other Inout: %s", resp_data.get('message'))
                break

            data = resp_data.get('data') or []
            if data:
                total_inouts = len(data)
                while data :
                    data_max_200 = data[:200]
                    data = data[200:]
                    inout_ids = [item.get("inoutId", 0) for item in data_max_200]
                    inout_data_more = {item.get("inoutId", 0): item for item in data_max_200}
                    self._sync_jst_inout_detail(path, inoutIds=inout_ids, InoutDataMore=inout_data_more, only_create=only_create, is_other_delivery=True)
                _logger.info("Sync JST InOut (Other): Page %s -> Đã đồng bộ %s inouts.", pageIndex, total_inouts)

                dp = resp_data.get('dataPage') or {}
                if dp.get('isLast', True):
                    break
                pageIndex = dp.get('pageIndex', pageIndex) + 1
            else:
                break
        _logger.info("Sync JST InOut (Other): Kết thúc đồng bộ.")

    def _sync_jst_inout_detail(self, path, inoutIds=None, OrderIds=None, PurchaseIds=None, InoutDataMore=None, only_create=False, is_other_delivery=False):
        if not inoutIds and not OrderIds and not PurchaseIds:
            _logger.error("Sync JST InOut: %s, Cần truyền 1 trong 3 tham số inoutIds / OrderIds / PurchaseIds", path)
            return
        body_data = {}
        if inoutIds:
            body_data["inoutIds"] = inoutIds
        if OrderIds:
            body_data["OrderIds"] = OrderIds
        if PurchaseIds:
            body_data["PurchaseIds"] = PurchaseIds

        resp_data = self.env['res.config.settings']._call_api_jst(path, body_data)

        if not resp_data.get('success'):
            _logger.error("Sync JST InOut: Call API Inout Detail %s", resp_data.get('message'))
            return

        data = resp_data.get('data') or []
        if data:
            self._update_jst_inouts(data, InoutDataMore=InoutDataMore, only_create=only_create, is_other_delivery=is_other_delivery)

    def _update_jst_inouts(self, data, InoutDataMore=None, only_create=False, is_other_delivery=False):
        """
        data (list): Data chi tiết của phiếu Inout
        InoutDataMore (dict type): Data gốc khi lấy danh sách phiếu Inout, sẽ lấy thêm 1 vài thông tin ở đây
        only_create: True -> chỉ tạo mới phiếu Inout nếu trên hệ thống chưa có mã phiếu Inout này (inoutId)
        is_other_delivery: True if use API Other Inout https://www.showdoc.com.cn/jsterp/7834151469503121
                            False if use API Inout: https://www.showdoc.com.cn/jsterp/8467743641028963
        """
        InoutDataMore = InoutDataMore or {}
        inout_ids_incoming = [str(line.get('inoutId')) for line in data if line.get('inoutId')]

        existing = self.sudo().search_read(
            domain=[('inoutId', 'in', inout_ids_incoming)],
            fields=['id', 'inoutId']
        )
        existing_map = {o['inoutId']: o['id'] for o in existing}

        new_vals = []
        update_vals = []
        map_fields = self._map_fields()
        item_map_fields = self.env['jst.stock.inout.item']._map_fields()

        for line in data:
            inout_id = line.get('inoutId')
            if not inout_id:
                continue
            inout_id_str = str(inout_id)

            if only_create and inout_id_str in existing_map:
                continue

            # dict chứa các field cần bổ sung vào phiếu Inout (lấy từ api danh sách, bổ sung vào api danh sách chi tiết)
            raw_payload_0 = {}
            if InoutDataMore:
                for field_add in JST_INOUT_FIELDS_ADD:
                    raw_payload_0[field_add] = InoutDataMore.get(inout_id, {}).get(field_add)

            vals = {
                'is_other_delivery': is_other_delivery
            }
            # Odoo - Inout data
            for key, value in line.items():
                field_key = map_fields.get(key)
                if field_key:
                    if field_key in JST_INOUT_DATETIME_FIELDS:
                        vals[field_key] = datetime.fromtimestamp(value, timezone.utc).replace(tzinfo=None) if value else False
                    elif field_key in JST_INOUT_TO_STRING_FIELDS:
                        vals[field_key] = str(value)
                    else:
                        vals[field_key] = value
                        if field_key == 'orderId':
                            vals['orderId_str'] = str(value)
            # Lấy các field data bổ sung từ API danh sách phiếu inouts
            if raw_payload_0:
                for key, value in raw_payload_0.items():
                    field_key = map_fields.get(key)
                    if field_key in JST_INOUT_DATETIME_FIELDS:
                        vals[field_key] = datetime.fromtimestamp(value, timezone.utc).replace(tzinfo=None) if value else False
                    else:
                        vals[field_key] = value
            # Odoo - Inout items data
            item_vals = []
            for item in line.get('itemDetails', []):
                mapped_item = {}
                for key, value in item.items():
                    field_key = item_map_fields.get(key)
                    if field_key:
                        if field_key in JST_INOUT_ITEM_DATETIME_FIELDS:
                            mapped_item[field_key] = datetime.fromtimestamp(value, timezone.utc).replace(tzinfo=None) if value else False
                        elif field_key in JST_INOUT_ITEM_TO_STRING_FIELDS:
                            mapped_item[field_key] = str(value)
                        else:
                            mapped_item[field_key] = value
                if mapped_item:
                    mapped_item['inoutId'] = inout_id_str
                    item_vals.append(mapped_item)
            vals['jst_stock_inout_item_ids'] = [(0, 0, it) for it in item_vals]

            # add Raw Data to re-check
            raw_payload_0.update(line)
            vals['raw_payload'] = raw_payload_0

            if inout_id_str in existing_map:
                update_vals.append((existing_map[inout_id_str], vals))
            else:
                new_vals.append(vals)

        if update_vals:
            for rec_id, vals in update_vals:
                self.browse(rec_id).sudo().write(vals)
        if new_vals:
            self.sudo().create(new_vals)

    def _cron_sync_inouts(self, duration_minutes=10):
        """
        Đồng bộ phiếu giao dựa vào:
            1. ngày tạo phiếu giao
            2. ngày giao hàng phiếu giao
            3. Trạng thái cần đồng bộ trên đơn hàng bán
        """
        ConfigParamater = self.env['ir.config_parameter'].sudo()
        ts_start = int(ConfigParamater.get_param('jst.next_ts_sync_inout', '0'))
        if not ts_start:
            return
        dt_now = fields.Datetime.now()
        ts_now = int(dt_now.timestamp())
        if ts_now < ts_start:
            return
        ts_end = ts_start + duration_minutes*60
        if ts_end > ts_now:
            ts_end = ts_now
        
        # 1. ngày tạo phiếu giao
        requestModel_create = {
            "CreateBegin": ts_start,
            "CreateEnd": ts_end
        }
        _logger.info("Sync JST InOut: Đồng bộ phiếu giao hàng theo thời gian tạo ...")
        self._sync_jst_sale_inouts(requestModel_create)
        
        # 2. ngày giao hàng phiếu giao
        requestModel_sendtime = {
            "SendTimeBegin": ts_start,
            "SendTimeEnd": ts_end
        }
        _logger.info("Sync JST InOut: Đồng bộ phiếu giao hàng theo thời gian gửi hàng ...")
        self._sync_jst_sale_inouts(requestModel_sendtime)
        # Sau khi đồng bộ xong cần update thời gian lần tiếp theo gọi
        next_ts_sync_inout = str(ts_end + 1)
        ConfigParamater.set_param('jst.next_ts_sync_inout', next_ts_sync_inout)
        
        # 3. Trạng thái cần đồng bộ trên đơn hàng bán
        # lấy ra các đơn hàng bán cần đồng bộ
        sale_orders_list = self.env['jst.sale.order'].search_read(
            [('need_sync_delivery', '=', True)],
            fields=['id', 'orderId'],
            limit=2000,
            order='jst_modified'
        )
        orderIds = [o['orderId'] for o in sale_orders_list]
        
        # Lấy ra các phiếu giao liên quan đến đơn bán
        inout_orders_list = self.env['jst.stock.inout'].search_read(
            [('orderId', 'in', orderIds)],
            fields=['id', 'inoutId', 'orderId'],
            limit=2000
        )
        inOutIds = [int(o['inoutId']) for o in inout_orders_list]
        total_inouts = len(inOutIds)
        saleOrderIds = [o['orderId'] for o in inout_orders_list]  # set need_sync_delivery = False
        path = "/api/Order/GetInoutItems"
        _logger.info("Sync JST InOut: Đồng bộ phiếu giao hàng theo đơn hàng bán ...")
        while inOutIds :
            inOutIds_200 = inOutIds[:200]
            inOutIds = inOutIds[200:]
            self._sync_jst_inout_detail(path, inoutIds=inOutIds_200)
        _logger.info("Sync JST InOut: Đã đồng bộ %s inouts.", total_inouts)
        # Update sale order k cần sync delivery nữa
        sale_orders =  self.env['jst.sale.order'].search([('orderId', 'in', saleOrderIds)])
        sale_orders.write({'need_sync_delivery': False})

    def _cron_sync_inouts_past(self, duration_hours=2):
        """
        Đồng bộ phiếu giao dựa vào:
            1. ngày tạo phiếu giao
        """
        ConfigParamater = self.env['ir.config_parameter'].sudo()
        ts_start = int(ConfigParamater.get_param('jst.start_ts_sync_inout_period', '0'))
        ts_end = int(ConfigParamater.get_param('jst.end_ts_sync_inout_period', '0'))
        if not ts_start or not ts_end or ts_start > ts_end:
            return

        dt_now = fields.Datetime.now()
        ts_now = int(dt_now.timestamp())
        if ts_now < ts_start:
            return

        ts_end = ts_start + duration_hours*60*60
        if ts_end > ts_now:
            ts_end = ts_now
        
        # 1. ngày tạo phiếu giao
        requestModel_create = {
            "CreateBegin": ts_start,
            "CreateEnd": ts_end
        }
        _logger.info("Sync JST InOut: Đồng bộ phiếu giao hàng theo thời gian tạo ...")
        self._sync_jst_sale_inouts(requestModel_create, only_create=True)
        
        # Sau khi đồng bộ xong cần update thời gian lần tiếp theo gọi
        next_ts_sync_inout = str(ts_end + 1)
        ConfigParamater.set_param('jst.start_ts_sync_inout_period', next_ts_sync_inout)

    def _cron_sync_other_inouts(self, duration=24):
        """
        Đồng bộ đơn hàng khác: 1 lần 1 ngày?
        """
        ConfigParamater = self.env['ir.config_parameter'].sudo()
        ts_start = int(ConfigParamater.get_param('jst.next_ts_sync_other_inout', '0'))
        if not ts_start:
            return
        dt_now = fields.Datetime.now()
        ts_now = int(dt_now.timestamp())
        if ts_now < ts_start:
            return
        ts_end = ts_start + duration*3600 + 100
        if ts_end > ts_now:
            ts_end = ts_now
        requestModel = {
            "modifiedBegin": ts_start,
            "modifiedEnd": ts_end
        }
        self._sync_jst_other_inouts(requestModel)
        # Sau khi đồng bộ xong cần update thời gian lần tiếp theo gọi
        next_ts_sync_other_inout = str(ts_end + 1)
        ConfigParamater.set_param('jst.next_ts_sync_other_inout', next_ts_sync_other_inout)

    def _map_fields(self):
        return {
            'inoutId': 'inoutId',
            'orderId': 'orderId',
            'status': 'status',
            'statusDisplay': 'statusDisplay',
            'linkCoId': 'linkCoId',
            'linkCompanyName': 'linkCompanyName',
            'warehouseId': 'warehouseId',
            'shopId': 'shopId',
            'warehouseName': 'warehouseName',
            'supplierCode': 'supplierCode',
            'supplierName': 'supplierName',
            'inoutTime': 'inoutTime',
            'orderDate': 'orderDate',
            'areaType': 'areaType',
            'areaTypeDisplay': 'areaTypeDisplay',
            'companyId': 'companyId',
            'currency': 'currency',
            'type': 'type',
            'typeDisplay': 'typeDisplay',
            'logisticsCompany': 'logisticsCompany',
            'logisticsCompanyCode': 'logisticsCompanyCode',
            'logisticsId': 'logisticsId',
            'realQty': 'realQty',
            'realTotalCostAmount': 'realTotalCostAmount',
            'freight': 'freight',
            'platformOrderId': 'platformOrderId',
            'sendTime': 'sendTime',
            'qty': 'qty',
            'totalCostAmount': 'totalCostAmount',
            'totalAmount': 'totalAmount',
            'paidAmount': 'paidAmount',
            'skuQty': 'skuQty',
            'created': 'created',
            'creatorName': 'creatorName',
            'creator': 'creator',
            'receiverName': 'receiverName',
            'remark': 'remark',
            'platformName': 'platformName',

            # from dict 1
            'factFreight': 'factFreight',
            'modified': 'jst_modified',
            'modifier': 'modifier',
            'outType': 'outType',
            'totalQty': 'totalQty',
            'receiverCountry': 'receiverCountry',
            'receiverProvince': 'receiverProvince',
            'receiverCity': 'receiverCity',
            'receiverDistrict': 'receiverDistrict',
            'receiverAddress': 'receiverAddress',
            'receiverPhone': 'receiverPhone',
            'receiverMobile': 'receiverMobile',
            'modifierName': 'modifierName',
        }
