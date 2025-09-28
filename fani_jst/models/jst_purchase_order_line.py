from odoo import models, fields


class JstPurchaseOrderLine(models.Model):
    _name = 'jst.purchase.order.line'
    _description = 'JST Purchase Order Line'
    _rec_name = 'skuName'
    _order = 'purchaseDetailId desc'

    # Many2one relationship back to Purchase Order
    jst_purchase_order_id = fields.Many2one(
        'jst.purchase.order',
        string='Purchase Order',
        required=True,
        ondelete='cascade',
        help="Related purchase order"
    )

    # ==== Purchase Order Line Fields ====
    boxCapacity = fields.Integer("Box Capacity", help="Standard packing quantity")
    boxQuantity = fields.Integer("Box Quantity", help="Box quantity")
    companyId = fields.Integer("Company ID", help="Company Number")
    created = fields.Datetime("Created", help="Creation time", index=True)
    creator = fields.Integer("Creator", help="Creator ID")
    currencyId = fields.Char("Currency", help="Currency code")
    goodsType = fields.Char("Goods Type", help="Purchased product type (e.g., Normal)")
    inoutQty = fields.Integer("Inout Quantity", help="Quantity in and out of warehouse")
    inoutWarehousedAmount = fields.Float("Inout Warehoused Amount", help="Amount in and out of warehouse")
    iqcExceptionQty = fields.Integer("IQC Exception Qty", help="Number of quality inspection abnormalities")
    itemId = fields.Char("Item ID", help="Style Code", index=True)
    itemName = fields.Char("Item Name", help="Style Name")
    lastPurchasePrice = fields.Float("Last Purchase Price", help="Last purchase price")
    jst_modified = fields.Datetime("Modified", help="Modification time", index=True)
    modifier = fields.Integer("Modifier", help="Modifier ID")
    planArriveDate = fields.Datetime("Plan Arrive Date", help="Estimated arrival time")
    planArriveQty = fields.Integer("Plan Arrive Qty", help="Estimated arrival quantity")
    planPurchaseQty = fields.Integer("Plan Purchase Qty", help="Recommended purchase quantity")
    purchaseAmount = fields.Float("Purchase Amount", help="Total purchase amount")
    purchaseDetailId = fields.Char("Purchase Detail ID", help="Purchase order detail number", index=True)
    purchaseId = fields.Char("Purchase ID", help="Purchase Order Number", index=True)
    purchasePrice = fields.Float("Purchase Price", help="Purchase price")
    purchaseQty = fields.Integer("Purchase Quantity", help="Purchase quantity")
    remark = fields.Text("Remark", help="Remark or note")
    skuId = fields.Char("SKU ID", help="Product Number", index=True)
    skuName = fields.Char("SKU Name", help="Product Name", index=True)
    skuPropertyName = fields.Char("SKU Property Name", help="Product attributes (specifications)")
    supplierCode = fields.Char("Supplier Code", help="Supplier Code", index=True)
    supplierItemId = fields.Char("Supplier Item ID", help="Supplier Part Number")
    supplierName = fields.Char("Supplier Name", help="Supplier Name")
    supplierSkuId = fields.Char("Supplier SKU ID", help="Supplier Product Number")
    weight = fields.Float("Weight", help="Product weight")

    def _map_fields(self):
        return {
            'boxCapacity': 'boxCapacity',
            'boxQuantity': 'boxQuantity',
            'companyId': 'companyId',
            'created': 'created',
            'creator': 'creator',
            'currencyId': 'currencyId',
            'goodsType': 'goodsType',
            'inoutQty': 'inoutQty',
            'inoutWarehousedAmount': 'inoutWarehousedAmount',
            'iqcExceptionQty': 'iqcExceptionQty',
            'itemId': 'itemId',
            'itemName': 'itemName',
            'lastPurchasePrice': 'lastPurchasePrice',
            'modified': 'jst_modified',
            'modifier': 'modifier',
            'planArriveDate': 'planArriveDate',
            'planArriveQty': 'planArriveQty',
            'planPurchaseQty': 'planPurchaseQty',
            'purchaseAmount': 'purchaseAmount',
            'purchaseDetailId': 'purchaseDetailId',
            'purchaseId': 'purchaseId',
            'purchasePrice': 'purchasePrice',
            'purchaseQty': 'purchaseQty',
            'remark': 'remark',
            'skuId': 'skuId',
            'skuName': 'skuName',
            'skuPropertyName': 'skuPropertyName',
            'supplierCode': 'supplierCode',
            'supplierItemId': 'supplierItemId',
            'supplierName': 'supplierName',
            'supplierSkuId': 'supplierSkuId',
            'weight': 'weight',
        }
