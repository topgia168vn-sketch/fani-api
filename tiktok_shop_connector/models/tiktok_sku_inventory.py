from odoo import models, fields


class TiktokSkuInventory(models.Model):
    _name = "tiktok.sku.inventory"
    _description = "TikTok SKU Inventory"

    sku_id = fields.Many2one("tiktok.sku", string="SKU", required=True, index=True, ondelete="cascade")
    warehouse_id = fields.Many2one("tiktok.warehouse", string="Warehouse", required=True, index=True, ondelete="cascade")
    quantity = fields.Integer(string="Quantity")

    _sql_constraints = [
        ('unique_sku_warehouse', 'unique(sku_id, warehouse_id)', 'SKU and Warehouse must be unique!'),
    ]
