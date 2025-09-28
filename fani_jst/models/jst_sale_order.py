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

ORDER_DATETIME_FIELDS = ['orderTime', 'sendTime', 'created', 'jst_modified', 'payTime', 'finalPayTime', 'presendSendTime', 'signTime', 'endDeliveryTime', 'endPickupTime'] # -> DATETIME OBJECT
ORDER_LIST_OBJECT_FIELDS = ['labelStr'] # -> "[X, Y, X]"

ORDER_LINE_DATETIME_FIELDS = ['created', 'itemSendDate'] # -> DATETIME OBJECT

class JstSaleOrder(models.Model):
    _name = 'jst.sale.order'
    _description = 'JST Sale Order'
    _rec_name = 'orderId'
    _order = 'orderId desc'

    # lưu ý: orderId cần lấy theo order
    # cron 5p' 1 lần: Update các đơn hàng tìm thấy, nếu chưa có thì tạo mới
    jst_sale_order_line_ids = fields.One2many('jst.sale.order.line', 'jst_sale_order_id', string='JST Order Lines')

    orderId = fields.Integer("Order ID", aggregator=None, index=True)
    orderId_str = fields.Char("Order ID ", index=True)
    
    # orderNumber = fields.Char("Order Number")
    trackingNumber = fields.Char("Tracking Number")
    skus = fields.Char("SKUs")
    extendData = fields.Text("Extended Data")
    platformOrderId = fields.Char("Platform Order ID")
    platformBuyerId = fields.Char("Platform Buyer ID")
    platformBuyerNickName = fields.Char("Platform Buyer Nickname")
    status = fields.Char("Status", index=True)
    statusDisplay = fields.Char("Status Display")
    receiverAddress = fields.Text("Receiver Address")
    receiverZip = fields.Char("Receiver Zip")
    questionDesc = fields.Text("Question Description")
    questionType = fields.Char("Question Type")
    isQuestion = fields.Boolean("Is Question", index=True)
    isQuestionText = fields.Char("Is Question Text")
    orderTime = fields.Datetime("Order Time", index=True)
    orderType = fields.Char("Order Type")
    orderTypeDisplay = fields.Char("Order Type Display")
    payTime = fields.Datetime("Pay Time", index=True)
    afterSaleId = fields.Integer("After Sale ID", aggregator=None)
    amount = fields.Float("Amount")
    amountDisPlay = fields.Char("Amount Display")
    buyerId = fields.Integer("Buyer ID", aggregator=None)
    buyerMessage = fields.Text("Buyer Message")
    calcWeight = fields.Float("Calculated Weight")
    cancelDesc = fields.Char("Cancel Description")
    cancelType = fields.Char("Cancel Type")
    cardInfo = fields.Char("Card Info")
    companyId = fields.Integer("Company ID", aggregator=None)
    created = fields.Datetime("Created", index=True)
    creator = fields.Integer("Creator", aggregator=None)
    currency = fields.Char("Currency")
    prefix = fields.Char("Currency Prefix")
    deliveryWay = fields.Char("Delivery Way")
    discountRate = fields.Float("Discount Rate")
    drpAmount = fields.Float("DRP Amount")
    drpCoIdFrom = fields.Integer("DRP Company ID From", aggregator=None)
    drpCoIdTo = fields.Integer("DRP Company ID To", aggregator=None)
    drpType = fields.Char("DRP Type")
    finalPayTime = fields.Datetime("Final Pay Time", index=True)
    freightFee = fields.Float("Freight Fee")
    freightIncomeDisPlay = fields.Char("Freight Income Display")
    freightIncome = fields.Float("Freight Income")
    invoiceData = fields.Text("Invoice Data")
    invoiceTaxNo = fields.Char("Invoice Tax No")
    invoiceTitle = fields.Char("Invoice Title")
    invoiceType = fields.Char("Invoice Type")
    isBuyerRate = fields.Boolean("Is Buyer Rate")
    isCod = fields.Boolean("Is COD", index=True)
    isInvoice = fields.Boolean("Is Invoice")
    isMerge = fields.Boolean("Is Merge", index=True)
    isPaid = fields.Boolean("Is Paid", index=True)
    isPresend = fields.Boolean("Is Presend")
    isPrintExpress = fields.Boolean("Is Print Express")
    isPrintShip = fields.Boolean("Is Print Ship")
    isSellerRate = fields.Boolean("Is Seller Rate")
    isSplit = fields.Boolean("Is Split")
    salesman = fields.Char("Salesman")
    receiverLastName = fields.Char("Receiver Last Name")
    receiverFirstName = fields.Char("Receiver First Name")
    logisticsBillType = fields.Char("Logistics Bill Type")
    logisticsCompanyName = fields.Char("Logistics Company Name")
    logisticsId = fields.Char("Logistics ID")
    mergePlatformOrderId = fields.Char("Merge Platform Order ID")
    jst_modified = fields.Datetime("Modified", index=True)
    modifier = fields.Integer("Modifier", aggregator=None)
    offlineNote = fields.Text("Offline Note")
    orderFrom = fields.Char("Order From")
    logisticsCompanyCode = fields.Char("Logistics Company Code")
    paidAmount = fields.Float("Paid Amount")
    paidAmountDisPlay = fields.Char("Paid Amount Display")
    payAmount = fields.Float("Pay Amount")
    payAmountDisPlay = fields.Char("Pay Amount Display")
    ortherAmount = fields.Float("Other Amount")
    ortherAmountDisPlay = fields.Char("Other Amount Display")
    platformFreeAmount = fields.Float("Platform Free Amount")
    platformFreeAmountDisPlay = fields.Char("Platform Free Amount Display")
    platformId = fields.Char("Platform ID")
    presendSendTime = fields.Datetime("Presend Send Time", index=True)
    receiverCity = fields.Char("Receiver City")
    receiverCountry = fields.Char("Receiver Country")
    receiverDistrict = fields.Char("Receiver District")
    receiverFirstNameEn = fields.Char("Receiver First Name EN")
    receiverIdCardType = fields.Char("Receiver ID Card Type")
    receiverLastNameEn = fields.Char("Receiver Last Name EN")
    receiverMobileEn = fields.Char("Receiver Mobile EN")
    receiverPhoneEn = fields.Char("Receiver Phone EN")
    receiverProvince = fields.Char("Receiver Province")
    receiverIdCard = fields.Char("Receiver ID Card")
    receiverTown = fields.Char("Receiver Town")
    sellerRemark = fields.Text("Seller Remark")
    saveHashCode = fields.Integer("Save Hash Code", aggregator=None)
    sendTime = fields.Datetime("Send Time", index=True)
    shopFreeAmount = fields.Float("Shop Free Amount")
    shopFreeAmountDisPlay = fields.Char("Shop Free Amount Display")
    shopId = fields.Integer("Shop ID", aggregator=None, index=True)
    shopName = fields.Char("Shop Name", index=True)
    signTime = fields.Datetime("Sign Time")
    endDeliveryTime = fields.Datetime("End Delivery Time", index=True)
    endPickupTime = fields.Datetime("End Pickup Time", index=True)
    skuIdStr = fields.Char("SKU ID String")
    splitBeforeOrderId = fields.Integer("Split Before Order ID", aggregator=None)
    warehouseId = fields.Integer("Warehouse ID", aggregator=None)
    weight = fields.Float("Weight")
    wmsCoId = fields.Integer("WMS Company ID", aggregator=None)
    isRejectOrder = fields.Boolean("Is Reject Order")
    ossId = fields.Char("OSS ID")
    payment = fields.Char("Payment")
    countryId = fields.Char("Country ID")
    settlementMethod = fields.Char("Settlement Method")
    platformStatus = fields.Char("Platform Status")
    pdfFileUrl = fields.Char("PDF File URL")
    labelStr = fields.Text("Label String")

    # Lịch sử thay đổi thông tin order: tạo mới, update
    jst_order_tracking_ids = fields.One2many(
        'jst.sale.order.tracking',
        'jst_order_id',
        string='Tracking JST Order Fields'
    )

    # Thông tin đồng bộ phiếu giao
    need_sync_delivery = fields.Boolean(string='Need sync Delivery Order', default=False)

    # Toàn bộ payload đơn (để lần vết đầy đủ)
    raw_payload = fields.Json(
        string="Raw Payload",
        help="Full JSON order object as returned by API"
    )

    def _fields_tracking(self):
        """
        Danh sách các trường cần tracking của JST Order, theo thời gian của JST
        """
        return ['status']

    def _fields_check_to_sync_delivery(self):
        """
        Danh sách các trường cần tracking của JST Order, theo thời gian của JST
        """
        return ['status']

    def action_sync_jst_orders(self, date_from, date_end, field='modify_time', pageIndex=1, only_create=False):
        """
        Đồng bộ Order theo thời gian
        
        * Lưu ý: date_end phải > date_from
        """
        key_dt_start = 'modifiedBegin'
        key_dt_end = 'modifiedEnd'
        if field == 'order_time':
            key_dt_start = 'orderTimeBegin'
            key_dt_end = 'orderTimeEnd'
        if field == 'send_time':
            key_dt_start = 'sendTimeBegin'
            key_dt_end = 'sendTimeEnd'
        start_dt = datetime.now()
        _logger.info("Sync JST Order: Bắt đầu đồng bộ đơn hàng JST ...")
        all_orderId = [] # Gom tất cả ourder cần update
        while True:
            body_data = {
                "requestModel": {
                  key_dt_start: int(date_from),
                  key_dt_end: int(date_end),
                },
                "dataPage": {
                  "pageSize": 500,
                  "pageIndex": pageIndex
                }
            }
            # Get Orders
            resp_data = self.env['res.config.settings']._call_api_jst("/api/Order/GetOrders", body_data)

            # Call API không thành công
            if not resp_data.get('success'):
                _logger.error("Sync JST Order: Error (Get Orders): %s", resp_data.get('message'))
                break

            data = resp_data.get('data') or []
            if data:
                # Lấy danh sách orders
                orderId_list = [item.get("orderId", 0) for item in data]
                all_orderId += orderId_list

                # Check dataPage
                dp = resp_data.get('dataPage') or {}
                if dp.get('isLast', True):
                    break
                pageIndex = dp.get('pageIndex', pageIndex) + 1
            else:
                break
        
        total_orders = len(all_orderId)
        _logger.info("Sync JST Order: Cần đồng bộ %s orders ...", total_orders)
        
        # Đồng bộ chi tiết 200 đơn 1 lần đến khi kết thúc
        if all_orderId:
            while all_orderId:
                check_dt_start = datetime.now()
                self._sync_jst_orders_detail(all_orderId[:200], only_create)
                check_dt_end = datetime.now()
                _logger.info("Sync JST Order: Đã đồng bộ %s orders -> %s (s)", len(all_orderId[:200]), (check_dt_end-check_dt_start).total_seconds())
                all_orderId = all_orderId[200:] # Bỏ 200 phần tử đầu tiên

        end_dt = datetime.now()
        _logger.info("Sync JST Order: Kết thúc đồng bộ đơn hàng JST -> %s orders-> %s (s)", total_orders, (end_dt - start_dt).total_seconds())

    def _sync_jst_orders_detail(self, orderId_list, only_create=False):
        # Tối đa 200 đơn hàng
        body_data = {
            'orderIds': orderId_list
        }
        resp_data = self.env['res.config.settings']._call_api_jst("/api/Order/GetOrderDetailByIds", body_data)
        
        # Call API không thành công
        if not resp_data.get('success'):
            _logger.error("Error (Get JST Order Detail): %s", resp_data.get('message'))
            return
        
        data = resp_data.get('data') or []
        if data:
            self._update_jst_orders(data, only_create)

    def _update_jst_orders(self, data, only_create=False):
        # Lấy danh sách orderId từ data sync
        order_ids_incoming = [line.get('orderId') for line in data if line.get('orderId')]

        # Tìm trong DB các order đã tồn tại (chỉ load id + orderId)
        existing_orders = self.sudo().search_read(
            domain=[('orderId', 'in', order_ids_incoming)],
            fields=['id', 'orderId']
        )
        existing_orders_map = {o['orderId']: o['id'] for o in existing_orders}

        # Tìm trong DB các order đã tồn tại, lấy các trường cần tracking
        existing_orders_tracking = self.sudo().search_read(
            domain=[('orderId', 'in', order_ids_incoming)],
            fields=['id', 'orderId'] + self._fields_tracking()
        )
        existing_orders_tracking_map = {o['orderId']: o for o in existing_orders_tracking}

        new_vals_list = []
        update_vals_list = []
        map_fields = self._map_fields()
        sol_map_fields = self.env['jst.sale.order.line']._map_fields()

        # Duyệt qua data của từng JST Order
        for line in data:
            order_id = line.get('orderId')
            if not order_id:
                continue

            # Nếu chỉ tạo mới và order đã tồn tại thì bỏ qua    
            if only_create and order_id in existing_orders_map:
                continue

            jst_order = {
                'raw_payload': line,
                'orderId_str': str(order_id)
            }
            # Map field - value chính của model
            for key, value in line.items():
                field_key = map_fields.get(key)
                if field_key:
                    if field_key in ORDER_DATETIME_FIELDS:
                        value_dt = datetime.fromtimestamp(value, timezone.utc).replace(tzinfo=None) if value else False
                        jst_order[field_key] = value_dt
                    elif field_key in ORDER_LIST_OBJECT_FIELDS:
                        new_value = str(value) if value else ''
                        jst_order[field_key] = new_value
                    else:
                        jst_order[field_key] = value

            # chuẩn hóa key-data của JST order lines
            order_lines_data = []
            for item_data in line.get('orderItems', []):
                # Map field - value
                jst_order_line = {}
                for key, value in item_data.items():
                    field_key = sol_map_fields.get(key)
                    if field_key:
                        if field_key in ORDER_LINE_DATETIME_FIELDS:
                            value_dt = datetime.fromtimestamp(value, timezone.utc).replace(tzinfo=None) if value else False
                            jst_order_line[field_key] = value_dt
                        else:
                            jst_order_line[field_key] = value
                if jst_order_line:
                    jst_order_line['orderId'] = line.get('orderId')
                    order_lines_data.append(jst_order_line)


            # Update order đã tồn tại
            if order_id in existing_orders_map:
                # order lines (các order lines cũ đã bị xóa)
                jst_order['jst_sale_order_line_ids'] = [(0, 0, ol) for ol in order_lines_data]

                # Tracking khi có thay đổi vào trường cần check
                jst_order_tracking_data = []
                for field_check in  self._fields_tracking():
                    vals = self._prepare_tracking_vals(line, field_check, existing_data=existing_orders_tracking_map.get(order_id, []))
                    if vals:
                        jst_order_tracking_data.append((0, 0, vals))
                        # Có value tạo tracking cho status thì add sync delivery
                        if field_check in self._fields_check_to_sync_delivery():
                            jst_order['need_sync_delivery'] = True
                jst_order['jst_order_tracking_ids'] = jst_order_tracking_data

                update_vals_list.append((existing_orders_map[order_id], jst_order))

            # Chưa đồng bộ: tạo mới
            else:
                # tạo order lines
                jst_order['jst_sale_order_line_ids'] = [(0, 0, ol) for ol in order_lines_data]
                # tạo tracking theo từng field làm giá trị ban đầu
                jst_order['jst_order_tracking_ids'] = [(0, 0, self._prepare_tracking_vals(line, field_check)) for field_check in self._fields_tracking()]

                new_vals_list.append(jst_order)

        # search tất cả order lines và cho chim cook thay vì dùng lệnh (5, 0, 0), giúp giảm update 200 orders từ 50s xuống còn khoảng dưới 5s
        jst_order_lines_remove = self.env['jst.sale.order.line'].search([('orderId', 'in', order_ids_incoming)])
        if jst_order_lines_remove:
            jst_order_lines_remove.unlink()

        with self.env.cr.savepoint():
            # Create new orders
            if new_vals_list:
                self.sudo().create(new_vals_list)
            # Update orders
            for order_id, vals in update_vals_list:
                order = self.browse(order_id)
                order.sudo().write(vals)

    def _prepare_tracking_vals(self, data, field_check, existing_data=False):
        if existing_data:
            field_value_old = str(existing_data.get(field_check))
            field_value = str(data.get(field_check))
            if field_value == field_value_old:
                return {}
        dt = data.get('modified')
        value_dt = datetime.fromtimestamp(dt, timezone.utc).replace(tzinfo=None) if dt else False
        return {
            'orderId': data.get('orderId'),
            'jst_modified': value_dt,
            'field_check': field_check,
            'field_value': str(data.get(field_check)),
            'raw_payload': data
        }

    def _map_fields(self):
        # key: JST API key, value: Odoo field name
        return {
            'orderId': 'orderId',
            'trackingNumber': 'trackingNumber',
            'skus': 'skus',
            'extendData': 'extendData',
            'platformOrderId': 'platformOrderId',
            'platformBuyerId': 'platformBuyerId',
            'platformBuyerNickName': 'platformBuyerNickName',
            'status': 'status',
            'statusDisplay': 'statusDisplay',
            'receiverAddress': 'receiverAddress',
            'receiverZip': 'receiverZip',
            'questionDesc': 'questionDesc',
            'questionType': 'questionType',
            'isQuestion': 'isQuestion',
            'isQuestionText': 'isQuestionText',
            'orderTime': 'orderTime',
            'orderType': 'orderType',
            'orderTypeDisplay': 'orderTypeDisplay',
            'payTime': 'payTime',
            'afterSaleId': 'afterSaleId',
            'amount': 'amount',
            'amountDisPlay': 'amountDisPlay',
            'buyerId': 'buyerId',
            'buyerMessage': 'buyerMessage',
            'calcWeight': 'calcWeight',
            'cancelDesc': 'cancelDesc',
            'cancelType': 'cancelType',
            'cardInfo': 'cardInfo',
            'companyId': 'companyId',
            'created': 'created',
            'creator': 'creator',
            'currency': 'currency',
            'prefix': 'prefix',
            'deliveryWay': 'deliveryWay',
            'discountRate': 'discountRate',
            'drpAmount': 'drpAmount',
            'drpCoIdFrom': 'drpCoIdFrom',
            'drpCoIdTo': 'drpCoIdTo',
            'drpType': 'drpType',
            'finalPayTime': 'finalPayTime',
            'freightFee': 'freightFee',
            'freightIncomeDisPlay': 'freightIncomeDisPlay',
            'freightIncome': 'freightIncome',
            'invoiceData': 'invoiceData',
            'invoiceTaxNo': 'invoiceTaxNo',
            'invoiceTitle': 'invoiceTitle',
            'invoiceType': 'invoiceType',
            'isBuyerRate': 'isBuyerRate',
            'isCod': 'isCod',
            'isInvoice': 'isInvoice',
            'isMerge': 'isMerge',
            'isPaid': 'isPaid',
            'isPresend': 'isPresend',
            'isPrintExpress': 'isPrintExpress',
            'isPrintShip': 'isPrintShip',
            'isSellerRate': 'isSellerRate',
            'isSplit': 'isSplit',
            'salesman': 'salesman',
            'receiverLastName': 'receiverLastName',
            'receiverFirstName': 'receiverFirstName',
            'logisticsBillType': 'logisticsBillType',
            'logisticsCompanyName': 'logisticsCompanyName',
            'logisticsId': 'logisticsId',
            'mergePlatformOrderId': 'mergePlatformOrderId',
            'modified': 'jst_modified',
            'modifier': 'modifier',
            'offlineNote': 'offlineNote',
            'orderFrom': 'orderFrom',
            'logisticsCompanyCode': 'logisticsCompanyCode',
            'paidAmount': 'paidAmount',
            'paidAmountDisPlay': 'paidAmountDisPlay',
            'payAmount': 'payAmount',
            'payAmountDisPlay': 'payAmountDisPlay',
            'ortherAmount': 'ortherAmount',
            'ortherAmountDisPlay': 'ortherAmountDisPlay',
            'platformFreeAmount': 'platformFreeAmount',
            'platformFreeAmountDisPlay': 'platformFreeAmountDisPlay',
            'platformId': 'platformId',
            'presendSendTime': 'presendSendTime',
            'receiverCity': 'receiverCity',
            'receiverCountry': 'receiverCountry',
            'receiverDistrict': 'receiverDistrict',
            'receiverFirstNameEn': 'receiverFirstNameEn',
            'receiverIdCardType': 'receiverIdCardType',
            'receiverLastNameEn': 'receiverLastNameEn',
            'receiverMobileEn': 'receiverMobileEn',
            'receiverPhoneEn': 'receiverPhoneEn',
            'receiverProvince': 'receiverProvince',
            'receiverIdCard': 'receiverIdCard',
            'receiverTown': 'receiverTown',
            'sellerRemark': 'sellerRemark',
            'saveHashCode': 'saveHashCode',
            'sendTime': 'sendTime',
            'shopFreeAmount': 'shopFreeAmount',
            'shopFreeAmountDisPlay': 'shopFreeAmountDisPlay',
            'shopId': 'shopId',
            'shopName': 'shopName',
            'signTime': 'signTime',
            'endDeliveryTime': 'endDeliveryTime',
            'endPickupTime': 'endPickupTime',
            'skuIdStr': 'skuIdStr',
            'splitBeforeOrderId': 'splitBeforeOrderId',
            'warehouseId': 'warehouseId',
            'weight': 'weight',
            'wmsCoId': 'wmsCoId',
            'isRejectOrder': 'isRejectOrder',
            'ossId': 'ossId',
            'payment': 'payment',
            'countryId': 'countryId',
            'settlementMethod': 'settlementMethod',
            'platformStatus': 'platformStatus',
            'pdfFileUrl': 'pdfFileUrl',
            'labelStr': 'labelStr',
        }

    def action_sync_this_orders(self):
        """
        Người dùng chọn đơn hàng và nhấn đồng bộ (tối đa 500 đơn 1 lúc)
        """
        self_todo = self.filtered(lambda r: r.orderId)
        if self_todo:
            while True:
                orders = self_todo[:500]
                orderId_list = orders.mapped('orderId')
                if orderId_list:
                    self._sync_jst_orders_detail(orderId_list)
                self_todo -= orders
                if not self_todo:
                    break

    def _cron_sync_jst_orders(self, duration_minutes=6):
        """
        Đồng bộ đơn hàng cách nhau 10p
        """
        _logger.info("Sync JST Order: Running Cron job ...")
        ConfigParamater = self.env['ir.config_parameter'].sudo()
        ts_start = int(ConfigParamater.get_param('jst.next_ts_sync_order', '0'))
        if not ts_start:
            return
        dt_now = fields.Datetime.now()
        ts_now = int(dt_now.timestamp())
        if ts_now < ts_start:
            return
        ts_end = ts_start + duration_minutes*60
        if ts_end > ts_now:
            ts_end = ts_now
        print(ts_start, ts_end)
        self.env['jst.sale.order'].action_sync_jst_orders(ts_start, ts_end)
        # Sau khi đồng bộ xong cần update thời gian lần tiếp theo gọi
        next_ts_sync_order = str(ts_end + 1)
        ConfigParamater.set_param('jst.next_ts_sync_order', next_ts_sync_order)

    def _cron_sync_jst_orders_past(self, duration=1):
        """
        Đồng bộ các đơn hàng trong quá khứ:
            - duration: khoảng thời gian cho mỗi lần đồng bộ
        """
        ConfigParamater = self.env['ir.config_parameter'].sudo()
        ts_start = int(ConfigParamater.get_param('jst.start_ts_sync_order_past', '0'))
        ts_end = int(ConfigParamater.get_param('jst.end_ts_sync_order_past', '0'))
        if not ts_end or not ts_start or ts_end <= ts_start:
            # Tắt cron khi đã đồng bộ xong khoảng thời gian
            # self.env.ref('fani_jst.ir_cron_sync_jst_orders_past').sudo().write({'active': False})
            return
        new_ts_start = ts_end - duration*3600
        if new_ts_start < ts_start:
            new_ts_start = ts_start
        self.env['jst.sale.order'].action_sync_jst_orders(new_ts_start, ts_end, field='order_time', only_create=True)
        
        # Sau khi đồng bộ xong cần update thời gian ts_end cho lần gọi tiếp theo
        new_ts_end = str(new_ts_start - 1)
        ConfigParamater.set_param('jst.end_ts_sync_order_past', new_ts_end)
