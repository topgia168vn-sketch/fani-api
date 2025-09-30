from datetime import timedelta, datetime, date
import time
import hashlib
import requests
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class JstSaleOrderLine(models.Model):
    _name = 'jst.sale.order.line'
    _description = 'JST Sale Order Line'
    _rec_name = 'orderItemId'

    # lưu ý: orderId cần lấy theo order
    jst_sale_order_id = fields.Many2one('jst.sale.order', string='JST Sale Order', ondelete='cascade')

    pic = fields.Char("Product Picture")
    name = fields.Char("Product Name")
    qty = fields.Integer("Quantity")
    price = fields.Float("Unit Price")
    priceDisplay = fields.Char("Unit Price Display")
    basePrice = fields.Float("Base Price")
    basePriceDisplay = fields.Char("Base Price Display")
    amount = fields.Float("Total Amount")
    amountDisPlay = fields.Char("Total Amount Display")
    binId = fields.Integer("Bin ID", aggregator=None)
    companyId = fields.Integer("Company ID")
    created = fields.Datetime("Created")
    creator = fields.Integer("Creator")
    drpCoIdTo = fields.Integer("DRP Company ID To", aggregator=None)
    isBuyerRate = fields.Boolean("Is Buyer Rate")
    isGift = fields.Boolean("Is Gift")
    isPresale = fields.Boolean("Is Presale")
    isSellerRate = fields.Boolean("Is Seller Rate")
    itemId = fields.Char("Item ID")
    itemLockId = fields.Integer("Item Lock ID", aggregator=None)
    itemLogisticsCompany = fields.Char("Item Logistics Company")
    itemLogisticsCompanyId = fields.Char("Item Logistics Company ID")
    itemSendDate = fields.Datetime("Item Send Date")
    itemStatus = fields.Char("Item Status")
    modifierName = fields.Char("Modifier Name")
    modifier = fields.Integer("Modifier", aggregator=None)
    orderId = fields.Char("Order ID")
    orderItemId = fields.Char("Order Item ID")
    paidAmount = fields.Float("Paid Amount")
    platformFreeAmount = fields.Float("Platform Free Amount")
    platformOrderItemId = fields.Char("Platform Order Item ID")
    platformSkuId = fields.Char("Platform SKU ID")
    propertiesValue = fields.Char("Product Properties")
    refundId = fields.Char("Refund ID")
    refundQty = fields.Integer("Refund Quantity")
    refundStatus = fields.Char("Refund Status")
    remark = fields.Char("Remark")
    shopFreeAmount = fields.Float("Shop Free Amount")
    skuId = fields.Char("SKU ID")
    skuType = fields.Char("SKU Type")
    totalWeight = fields.Float("Total Weight")
    weight = fields.Float("Weight")
    isDeleted = fields.Boolean("Is Deleted")
    isNotNeedDelivery = fields.Boolean("Is Not Need Delivery")
    isPlatformDelivery = fields.Boolean("Is Platform Delivery")
    isCombined = fields.Boolean("Is Combined")

    def _map_fields(self):
        # key: JST API key, value: Odoo field name
        return {
            'pic': 'pic',
            'name': 'name',
            'qty': 'qty',
            'price': 'price',
            'priceDisplay': 'priceDisplay',
            'basePrice': 'basePrice',
            'basePriceDisplay': 'basePriceDisplay',
            'amount': 'amount',
            'amountDisPlay': 'amountDisPlay',
            'binId': 'binId',
            'companyId': 'companyId',
            'created': 'created',
            'creator': 'creator',
            'drpCoIdTo': 'drpCoIdTo',
            'isBuyerRate': 'isBuyerRate',
            'isGift': 'isGift',
            'isPresale': 'isPresale',
            'isSellerRate': 'isSellerRate',
            'itemId': 'itemId',
            'itemLockId': 'itemLockId',
            'itemLogisticsCompany': 'itemLogisticsCompany',
            'itemLogisticsCompanyId': 'itemLogisticsCompanyId',
            'itemSendDate': 'itemSendDate',
            'itemStatus': 'itemStatus',
            'modifierName': 'modifierName',
            'modifier': 'modifier',
            'orderId': 'orderId',
            'orderItemId': 'orderItemId',
            'paidAmount': 'paidAmount',
            'platformFreeAmount': 'platformFreeAmount',
            'platformOrderItemId': 'platformOrderItemId',
            'platformSkuId': 'platformSkuId',
            'propertiesValue': 'propertiesValue',
            'refundId': 'refundId',
            'refundQty': 'refundQty',
            'refundStatus': 'refundStatus',
            'remark': 'remark',
            'shopFreeAmount': 'shopFreeAmount',
            'skuId': 'skuId',
            'skuType': 'skuType',
            'totalWeight': 'totalWeight',
            'weight': 'weight',
            'isDeleted': 'isDeleted',
            'isNotNeedDelivery': 'isNotNeedDelivery',
            'isPlatformDelivery': 'isPlatformDelivery',
            'isCombined': 'isCombined',
        }
