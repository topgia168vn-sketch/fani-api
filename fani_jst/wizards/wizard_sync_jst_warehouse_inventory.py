from datetime import timedelta
from odoo import models, fields


class JstWarehouseInventory(models.TransientModel):
    _name = 'wizard.sync.jst.warehouse.inventory'
    _description = 'Wizard Sync JST Warehouse Inventory'

    def _default_date_from(self):
        return fields.Datetime.now() - timedelta(days=1)
    def _default_date_to(self):
        return fields.Datetime.now()

    # Basic info from API
    date_from = fields.Datetime("Ngày Bắt đầu", default=_default_date_from, required=True)
    date_to = fields.Datetime("Ngày kết thúc", default=_default_date_to, required=True)
    warehouseId = fields.Integer(string='Warehouse Id')
    itemIds = fields.Text(string='Item Ids')
    skuIds = fields.Text(string='Sku Ids')

    def action_sync(self):
        modifiedBegin = int(self.date_from.timestamp())
        modifiedEnd = int(self.date_to.timestamp())
        warehouseId = self.warehouseId or False
        itemIds = False
        skuIds = False
        if self.itemIds:
            itemIds = [int(x.strip()) for x in self.itemIds.split(",")]
        if self.skuIds:
            skuIds = [int(x.strip()) for x in self.skuIds.split(",")]
        self.env['jst.warehouse.inventory'].action_sync_jst_warehouse_inventory(modifiedBegin, modifiedEnd, warehouseId=warehouseId, itemIds=itemIds, skuIds=skuIds)
