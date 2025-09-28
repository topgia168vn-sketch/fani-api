import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)

# Các field dạng datetime (timestamp) từ API
JST_INOUT_ITEM_DATETIME_FIELDS = [
    'producedDate'
]


class JstStockInoutItem(models.Model):
    _name = 'jst.stock.inout.item'
    _description = 'JST Stock InOut Item'
    _rec_name = 'inoutItemId'
    _order = 'inoutItemId desc'

    jst_stock_inout_id = fields.Many2one(
        'jst.stock.inout',
        string='JST Stock InOut',
        help="Reference to the stock in/out order"
    )

    # ==== Fields from API dict (in order) ====
    companyId = fields.Integer("Company ID", help="Company ID")
    cost = fields.Float("Cost", help="Unit cost")
    costAmount = fields.Float("Cost Amount", help="Total cost amount")
    inoutId = fields.Char("InOut ID", help="Parent InOut ID from API")
    inoutItemId = fields.Char("InOut Item ID", help="Unique ID of the InOut item")
    invoicedQtyDel = fields.Float("Invoiced Quantity Delivered", help="Invoiced quantity already delivered")
    isGift = fields.Boolean("Is Gift", help="Whether this item is a gift")
    itemId = fields.Char("Item ID", help="Item ID")
    packId = fields.Char("Pack ID", help="Pack ID if bundled")
    payAmount = fields.Float("Pay Amount", help="Payment amount for this item")
    pic = fields.Char("Picture", help="Product image URL")
    isVerifyShelfLife = fields.Boolean("Verify Shelf Life", help="Whether shelf life needs to be verified")
    producedDate = fields.Datetime("Produced Date", help="Production date")
    shelfLife = fields.Integer("Shelf Life", help="Shelf life in days")
    producedDateDisplay = fields.Char("Produced Date Display", help="Production date string returned by API")
    propertiesValue = fields.Char("Properties Value", help="Product properties")
    qty = fields.Float("Quantity", help="Planned quantity")
    overloadLimitCnt = fields.Integer("Overload Limit Count", help="Overload limit count")
    rawPlatformOrderId = fields.Char("Raw Platform Order ID", help="Original platform order ID")
    realQty = fields.Float("Real Quantity", help="Actual quantity")
    remark = fields.Text("Remark", help="Remark or note")
    saleAmount = fields.Float("Sale Amount", help="Total sale amount")
    saleBasePrice = fields.Float("Sale Base Price", help="Base price per unit")
    salePrice = fields.Float("Sale Price", help="Sale price per unit")
    skuBatchId = fields.Char("SKU Batch ID", help="SKU batch ID")
    skuId = fields.Char("SKU ID", help="SKU ID")
    skuName = fields.Char("SKU Name", help="SKU name")
    subOrderId = fields.Integer("Sub Order ID", help="Sub-order ID linked to this item")
    areaType = fields.Char("Area Type", help="Warehouse type")
    areaTypeDisplay = fields.Char("Area Type Display", help="Warehouse type display name")
    bin = fields.Char("Bin", help="Storage bin")
    binType = fields.Char("Bin Type", help="Type of storage bin")
    binTypeDisplay = fields.Char("Bin Type Display", help="Storage bin type display")
    unit = fields.Char("Unit", help="Measurement unit")

    def _map_fields(self):
        return {
            'companyId': 'companyId',
            'cost': 'cost',
            'costAmount': 'costAmount',
            'inoutId': 'inoutId',
            'inoutItemId': 'inoutItemId',
            'invoicedQtyDel': 'invoicedQtyDel',
            'isGift': 'isGift',
            'itemId': 'itemId',
            'packId': 'packId',
            'payAmount': 'payAmount',
            'pic': 'pic',
            'isVerifyShelfLife': 'isVerifyShelfLife',
            'producedDate': 'producedDate',
            'shelfLife': 'shelfLife',
            'producedDateDisplay': 'producedDateDisplay',
            'propertiesValue': 'propertiesValue',
            'qty': 'qty',
            'overloadLimitCnt': 'overloadLimitCnt',
            'rawPlatformOrderId': 'rawPlatformOrderId',
            'realQty': 'realQty',
            'remark': 'remark',
            'saleAmount': 'saleAmount',
            'saleBasePrice': 'saleBasePrice',
            'salePrice': 'salePrice',
            'skuBatchId': 'skuBatchId',
            'skuId': 'skuId',
            'skuName': 'skuName',
            'subOrderId': 'subOrderId',
            'areaType': 'areaType',
            'areaTypeDisplay': 'areaTypeDisplay',
            'bin': 'bin',
            'binType': 'binType',
            'binTypeDisplay': 'binTypeDisplay',
            'unit': 'unit',
        }
