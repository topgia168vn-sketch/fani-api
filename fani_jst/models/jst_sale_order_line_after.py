from datetime import timedelta, datetime, date
import time
import hashlib
import requests
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class JstSaleOrderAfterLine(models.Model):
    _name = 'jst.sale.order.after.line'
    _description = 'JST After Sale Order Line'
    _rec_name = 'afterSaleOrderItemId'

    # lưu ý: afterSaleOrderId cần lấy theo after order
    jst_sale_order_after_id = fields.Many2one('jst.sale.order.after', string='JST After Sale Order')

    afterSaleOrderId = fields.Integer("After Sale Order ID", aggregator=None)
    afterSaleOrderItemId = fields.Integer("After Sale Order Item ID", aggregator=None)
    amount = fields.Char("Amount")
    combineSkuId = fields.Char("Combine SKU ID")
    costPrice = fields.Char("Cost Price")
    created = fields.Datetime("Created")
    inoutTime = fields.Datetime("Inout Time")
    isCombine = fields.Boolean("Is Combine")
    itemId = fields.Char("Item ID")
    jst_modified = fields.Datetime("Modified")
    orderItemId = fields.Char("Order Item ID")
    pic = fields.Char("Product Picture")
    platformOrderItemId = fields.Char("Platform Order Item ID")
    platformSkuId = fields.Char("Platform SKU ID")
    price = fields.Char("Price")
    propertiesValue = fields.Char("Product Properties")
    qty = fields.Integer("Quantity")
    remark = fields.Char("Remark")
    returnQty = fields.Integer("Return Quantity")
    salePrice = fields.Char("Sale Price")
    skuId = fields.Char("SKU ID")
    skuName = fields.Char("SKU Name")
    type = fields.Char("Type")
    typeDisplay = fields.Char("Type Display")
    unit = fields.Char("Unit")

    # Khác
    afterSaleOrderId_str = fields.Char("After Sale Order ID ")
    afterSaleOrderItemId_str = fields.Char("After Sale Order Item ID ")

    # Toàn bộ payload đơn (để lần vết đầy đủ)
    raw_payload = fields.Json(
        string="Raw Payload",
        help="Full JSON after order object as returned by API"
    )

    def _map_fields(self):
        # key: JST API key, value: Odoo field name
        return {
            'afterSaleOrderId': 'afterSaleOrderId',
            'afterSaleOrderItemId': 'afterSaleOrderItemId',
            'amount': 'amount',
            'combineSkuId': 'combineSkuId',
            'costPrice': 'costPrice',
            'created': 'created',
            'inoutTime': 'inoutTime',
            'isCombine': 'isCombine',
            'itemId': 'itemId',
            'modified': 'jst_modified',
            'orderItemId': 'orderItemId',
            'pic': 'pic',
            'platformOrderItemId': 'platformOrderItemId',
            'platformSkuId': 'platformSkuId',
            'price': 'price',
            'propertiesValue': 'propertiesValue',
            'qty': 'qty',
            'remark': 'remark',
            'returnQty': 'returnQty',
            'salePrice': 'salePrice',
            'skuId': 'skuId',
            'skuName': 'skuName',
            'type': 'type',
            'typeDisplay': 'typeDisplay',
            'unit': 'unit',
        }
