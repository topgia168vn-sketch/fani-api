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

AFTER_ORDER_DATETIME_FIELDS = ['created', 'jst_modified', 'orderPayTime', 'orderTime'] # -> DATETIME OBJECT
AFTER_ORDER_LIST_OBJECT_FIELDS = ['labels'] # -> "[X, Y, X]"

AFTER_ORDER_LINE_DATETIME_FIELDS = ['created', 'jst_modified', 'inoutTime'] # -> DATETIME OBJECT

class JstSaleOrderAfter(models.Model):
    _name = 'jst.sale.order.after'
    _description = 'JST After Sale Order'
    _rec_name = 'afterSaleOrderId_str'
    _order = 'afterSaleOrderId desc'

    jst_sale_order_after_line_ids = fields.One2many('jst.sale.order.after.line', 'jst_sale_order_after_id', string='JST After Order Lines')

    afterSaleOrderId = fields.Integer("After Sale Order ID", aggregator=None, index=True)
    afterSaleType = fields.Char("After Sale Type")
    afterSaleTypeDisplay = fields.Char("After Sale Type Display")
    areaType = fields.Char("Area Type")
    areaTypeDisplay = fields.Char("Area Type Display")
    created = fields.Datetime("Created")
    freight = fields.Float("Freight")
    logisticsCompanyId = fields.Char("Logistics Company ID")
    logisticsCompanyName = fields.Char("Logistics Company Name")
    logisticsId = fields.Char("Logistics ID")
    jst_modified = fields.Datetime("Modified")
    orderId = fields.Integer("Order ID", aggregator=None)
    orderPayTime = fields.Datetime("Order Pay Time")
    orderTime = fields.Datetime("Order Time")
    payment = fields.Float("Payment")
    platformAfterSaleId = fields.Char("Platform After Sale ID")
    platformBuyerId = fields.Char("Platform Buyer ID")
    platformGoodsStatus = fields.Char("Platform Goods Status")
    platformGoodsStatusDisplay = fields.Char("Platform Goods Status Display")
    platformOrderId = fields.Char("Platform Order ID")
    platformRefundStatus = fields.Char("Platform Refund Status")
    platformRefundStatusDisplay = fields.Char("Platform Refund Status Display")
    receiverFirstNameEn = fields.Char("Receiver First Name EN")
    receiverLastNameEn = fields.Char("Receiver Last Name EN")
    receiverMobileEn = fields.Char("Receiver Mobile EN")
    receiverPhoneEn = fields.Char("Receiver Phone EN")
    refundAmount = fields.Float("Refund Amount")
    remark = fields.Text("Remark")
    shopId = fields.Integer("Shop ID", aggregator=None)
    status = fields.Char("Status")
    statusDisplay = fields.Char("Status Display")
    warehouseId = fields.Integer("Warehouse ID", aggregator=None)
    drpCoIdFrom = fields.Integer("DRP Company ID From", aggregator=None)
    drpCoIdTo = fields.Integer("DRP Company ID To", aggregator=None)
    createType = fields.Char("Create Type")
    createTypeDisplay = fields.Char("Create Type Display")
    labels = fields.Text("Labels")

    # Khác
    afterSaleOrderId_str = fields.Char("After Sale Order ID ")
    orderId_str = fields.Char("Sale Order ID ")

    # Toàn bộ payload đơn (để lần vết đầy đủ)
    raw_payload = fields.Json(
        string="Raw Payload",
        help="Full JSON after order object as returned by API"
    )

    def action_sync_jst_after_orders(self, date_from, date_end, field='modify_time', pageIndex=1, only_create=False):
        """
        Đồng bộ After Order theo thời gian
        
        * Lưu ý: date_end phải > date_from
        """
        key_dt_start = 'modifiedBegin'
        key_dt_end = 'modifiedEnd'
        if field == 'order_time':
            key_dt_start = 'orderTimeBegin'
            key_dt_end = 'orderTimeEnd'
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
            # Get After Orders
            resp_data = self.env['res.config.settings']._call_api_jst("/api/AfterSaleOrder/GetAfterSaleOrders", body_data)

            # Call API không thành công
            if not resp_data.get('success'):
                _logger.error("Error (Get JST After Orders): %s", resp_data.get('message'))
                break

            data = resp_data.get('data') or []
            if data:
                # update after sale order
                after_order_ids_to_update_lines = self._update_jst_after_orders(data, only_create)
                # Update after sale order details
                while True:
                    if len(after_order_ids_to_update_lines) > 200:
                        self._update_jst_after_order_details(after_order_ids_to_update_lines[:200])
                        after_order_ids_to_update_lines = after_order_ids_to_update_lines[200:]  # Bỏ 200 phần tử đầu tiên
                    else:
                        self._update_jst_after_order_details(after_order_ids_to_update_lines)
                        break
                
                # Check dataPage
                dp = resp_data.get('dataPage') or {}
                if dp.get('isLast', True):
                    break
                pageIndex = dp.get('pageIndex', pageIndex) + 1
                # Pending 0.3s second before calling API
                time.sleep(0.3)
            else:
                break

    def _update_jst_after_orders(self, data, only_create=False):
        # Lấy danh sách afterSaleOrderId từ data sync
        after_order_ids_incoming = [line.get('afterSaleOrderId') for line in data if line.get('afterSaleOrderId')]
        # Tìm trong DB các after order đã tồn tại (chỉ load id + afterSaleOrderId)
        existing_after_orders = self.sudo().search_read(
            domain=[('afterSaleOrderId', 'in', after_order_ids_incoming)],
            fields=['id', 'afterSaleOrderId']
        )
        existing_after_orders_map = {o['afterSaleOrderId']: o['id'] for o in existing_after_orders}
        
        new_vals_list = []
        update_vals_list = []
        map_fields = self._map_fields()
        after_order_ids_to_update_lines = []
        # Duyệt qua data của từng After Order
        for line in data:
            after_order_id = line.get('afterSaleOrderId')
            if not after_order_id:
                continue
            
            # Nếu chỉ tạo mới và after order đã tồn tại thì bỏ qua
            if only_create and after_order_id in existing_after_orders_map:
                continue
            
            after_order_ids_to_update_lines.append(after_order_id)

            jst_after_order = {
                'raw_payload': line,
                'afterSaleOrderId_str': str(after_order_id),
                'jst_sale_order_after_line_ids': [(5, 0, 0)]  # clear lines to re-update
            }
            # Map field - value chính của model
            for key, value in line.items():
                field_key = map_fields.get(key)
                if field_key:
                    if field_key in AFTER_ORDER_DATETIME_FIELDS:
                        value_dt = datetime.fromtimestamp(value, timezone.utc).replace(tzinfo=None) if value else False
                        jst_after_order[field_key] = value_dt
                    elif field_key in AFTER_ORDER_LIST_OBJECT_FIELDS:
                        new_value = str(value) if value else ''
                        jst_after_order[field_key] = new_value
                    else:
                        jst_after_order[field_key] = value
                        if field_key == 'orderId':
                            jst_after_order['orderId_str'] = str(value)
            new_vals_list.append(jst_after_order)

        # Thực hiện DB transaction
        with self.env.cr.savepoint():
            if new_vals_list:
                self.sudo().create(new_vals_list)
            for after_order_id, vals in update_vals_list:
                after_order = self.browse(after_order_id)
                after_order.sudo().write(vals)
            self.flush_model()
        return after_order_ids_to_update_lines

    def _update_jst_after_order_details(self, afterOrderIds):
        body_data = {
            "AfterSaleOrderIds": afterOrderIds
        }
        # Get After Orders
        resp_data = self.env['res.config.settings']._call_api_jst("/api/AfterSaleOrder/GetAfterSaleOrderItems", body_data)
        # Call API không thành công
        if not resp_data.get('success'):
            _logger.error("Error (Get JST After Orders): %s", resp_data.get('message'))
            return
        
        data = resp_data.get('data') or []
        # Lấy danh sách afterSaleOrderId từ data sync
        after_order_ids_incoming = [line.get('afterSaleOrderId') for line in data if line.get('afterSaleOrderId')]
        # Tìm trong DB các after order đã tồn tại (chỉ load id + afterSaleOrderId)
        existing_after_orders = self.sudo().search_read(
            domain=[('afterSaleOrderId', 'in', after_order_ids_incoming)],
            fields=['id', 'afterSaleOrderId']
        )
        existing_after_orders_map = {o['afterSaleOrderId']: o['id'] for o in existing_after_orders}

        new_vals_list = []
        map_fields = self.env['jst.sale.order.after.line']._map_fields()
        # duyệt qua từng line của after orders
        for line in data:
            after_order_id = line.get('afterSaleOrderId')
            if not after_order_id:
                continue
            vals_line = {
                'raw_payload': line,
                'afterSaleOrderId_str': str(after_order_id),
                'jst_sale_order_after_id': existing_after_orders_map.get(after_order_id)
            }
            for key, value in line.items():
                field_key = map_fields.get(key)
                if field_key:
                    if field_key in AFTER_ORDER_LINE_DATETIME_FIELDS:
                        value_dt = datetime.fromtimestamp(value, timezone.utc).replace(tzinfo=None) if value else False
                        vals_line[field_key] = value_dt
                    else:
                        if field_key in ['afterSaleOrderItemId']:
                            vals_line['afterSaleOrderItemId_str'] = str(value)
                        vals_line[field_key] = value
            new_vals_list.append(vals_line)
        if new_vals_list:
            with self.env.cr.savepoint():
                self.env['jst.sale.order.after.line'].sudo().create(new_vals_list)

    def _map_fields(self):
        # key: JST API key, value: Odoo field name
        return {
            'afterSaleOrderId': 'afterSaleOrderId',
            'afterSaleType': 'afterSaleType',
            'afterSaleTypeDisplay': 'afterSaleTypeDisplay',
            'areaType': 'areaType',
            'areaTypeDisplay': 'areaTypeDisplay',
            'created': 'created',
            'freight': 'freight',
            'logisticsCompanyId': 'logisticsCompanyId',
            'logisticsCompanyName': 'logisticsCompanyName',
            'logisticsId': 'logisticsId',
            'modified': 'jst_modified',
            'orderId': 'orderId',
            'orderPayTime': 'orderPayTime',
            'orderTime': 'orderTime',
            'payment': 'payment',
            'platformAfterSaleId': 'platformAfterSaleId',
            'platformBuyerId': 'platformBuyerId',
            'platformGoodsStatus': 'platformGoodsStatus',
            'platformGoodsStatusDisplay': 'platformGoodsStatusDisplay',
            'platformOrderId': 'platformOrderId',
            'platformRefundStatus': 'platformRefundStatus',
            'platformRefundStatusDisplay': 'platformRefundStatusDisplay',
            'receiverFirstNameEn': 'receiverFirstNameEn',
            'receiverLastNameEn': 'receiverLastNameEn',
            'receiverMobileEn': 'receiverMobileEn',
            'receiverPhoneEn': 'receiverPhoneEn',
            'refundAmount': 'refundAmount',
            'remark': 'remark',
            'shopId': 'shopId',
            'status': 'status',
            'statusDisplay': 'statusDisplay',
            'warehouseId': 'warehouseId',
            'drpCoIdFrom': 'drpCoIdFrom',
            'drpCoIdTo': 'drpCoIdTo',
            'createType': 'createType',
            'createTypeDisplay': 'createTypeDisplay',
            'labels': 'labels',
        }

    def action_sync_this_after_orders(self):
        """
        Người dùng chọn đơn hàng và nhấn đồng bộ (tối đa 200 đơn 1 lúc)
        """
        self_todo = self.filtered(lambda r: r.afterSaleOrderId)
        if self_todo:
            while True:
                after_orders = self_todo[:200]
                afterSaleOrderId_list = after_orders.mapped('afterSaleOrderId')
                if afterSaleOrderId_list:
                    self._sync_jst_after_orders_detail(afterSaleOrderId_list)
                self_todo -= after_orders
                if not self_todo:
                    break

    def _cron_sync_jst_after_orders(self):
        """
        Đồng bộ đơn hàng sau bán trong vòng 1 ngày
        """
        ConfigParamater = self.env['ir.config_parameter'].sudo()
        ts_start = int(ConfigParamater.get_param('jst.next_ts_sync_after_order', '0'))
        if not ts_start:
            return
        dt_now = fields.Datetime.now()
        ts_now = int(dt_now.timestamp())
        if ts_now < ts_start:
            return
        ts_end = ts_start + 24*3600
        if ts_end > ts_now:
            ts_end = ts_now
        self.env['jst.sale.order.after'].action_sync_jst_after_orders(ts_start, ts_end, field='order_time')

        # Sau khi đồng bộ xong cần update thời gian lần tiếp theo gọi
        next_ts_sync_after_order = str(ts_end + 1)
        ConfigParamater.set_param('jst.next_ts_sync_after_order', next_ts_sync_after_order)
