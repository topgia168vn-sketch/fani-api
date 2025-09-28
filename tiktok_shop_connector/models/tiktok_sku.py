import logging
from odoo import api, models, fields, Command

_logger = logging.getLogger(__name__)


class TiktokSku(models.Model):
    _name = "tiktok.sku"
    _description = "TikTok Product SKUs"
    _order = "create_date desc"

    # ===== Basic Information =====
    tiktok_id = fields.Char(string="TikTok SKU ID", required=True, index=True)
    seller_sku = fields.Char(string="Seller SKU", help="Internal SKU code from seller")
    product_id = fields.Many2one("tiktok.product", string="Product", required=True, ondelete="cascade")
    shop_id = fields.Many2one("tiktok.shop", string="Shop", related="product_id.shop_id", store=True)

    # ===== Pricing Information =====
    currency = fields.Char(string="Currency")
    sale_price = fields.Float(string="Sale Price", digits="Product Price")
    tax_exclusive_price = fields.Float(string="Tax Exclusive Price", digits="Product Price")

    # ===== Inventory Information =====
    total_quantity = fields.Integer(string="Total Quantity", compute="_compute_total_quantity", store=True)
    inventory_details = fields.Json(string="Inventory Details", help="Warehouse-wise inventory")
    inventory_ids = fields.One2many("tiktok.sku.inventory", "sku_id", string="Inventory", compute="_compute_inventory_ids", store=True)

    # ===== Variant Attributes =====
    sales_attributes = fields.Json(string="Sales Attributes", help="Size, color, material, etc.")
    variant_display = fields.Char(string="Variant Display", compute="_compute_variant_display", store=True)

    # ===== Status Information =====
    status = fields.Char(string="Status", help="NORMAL, DISABLED, etc.")
    status_info = fields.Json(string="Status Info")

    # ===== Listing Policy =====
    inventory_type = fields.Selection([
        ("EXCLUSIVE", "Exclusive"),
        ("SHARED", "Shared")
    ], string="Inventory Type")
    price_sync = fields.Boolean(string="Price Sync")
    global_listing_policy = fields.Json(string="Global Listing Policy")

    # ===== Media =====
    sku_images = fields.Json(string="SKU Images", help="Variant-specific images")

    # ===== Constraints =====
    _sql_constraints = [
        ('tiktok_id_unique', 'unique(tiktok_id)', 'TikTok SKU ID must be unique!'),
    ]

    @api.depends('inventory_details')
    def _compute_inventory_ids(self):
        """Compute inventory IDs from inventory details."""
        warehouses = self.env['tiktok.warehouse'].search([])
        for sku in self:
            to_delete_inventories = sku.inventory_ids
            inventory_values = []
            for inventory in (sku.inventory_details or []):
                if inventory.get('warehouse_id') and inventory.get('quantity'):
                    warehouse = warehouses.filtered(
                        lambda w: w.tiktok_id == inventory['warehouse_id'] and w.shop_id == sku.shop_id
                    )
                    if warehouse:
                        org_inventory = sku.inventory_ids.filtered(
                            lambda i: i.warehouse_id == warehouse
                        )
                        if org_inventory:
                            to_delete_inventories -= org_inventory
                            if org_inventory.quantity != inventory['quantity']:
                                inventory_values.append(Command.update(org_inventory.id, {
                                    'quantity': inventory['quantity'],
                                }))
                        else:
                            inventory_values.append(Command.create({
                                'warehouse_id': warehouse.id,
                                'quantity': inventory['quantity'],
                            }))
            if to_delete_inventories:
                inventory_values.extend([Command.unlink(i.id) for i in to_delete_inventories])
            sku.inventory_ids = inventory_values

    @api.depends('inventory_ids', 'inventory_ids.quantity')
    def _compute_total_quantity(self):
        """Calculate total quantity across all warehouses."""
        groups = self.env['tiktok.sku.inventory']._read_group([('sku_id', 'in', self.ids)], ['sku_id'], ['quantity:sum'])
        inventory_mapping = {sku.id: quantity for sku, quantity in groups}
        for sku in self:
            sku.total_quantity = inventory_mapping.get(sku.id, 0)

    @api.depends('sales_attributes')
    def _compute_variant_display(self):
        """Create human-readable variant display from sales_attributes."""
        for sku in self:
            if not sku.sales_attributes or not isinstance(sku.sales_attributes, list):
                sku.variant_display = "Default"
                continue

            attributes = []
            for attr in sku.sales_attributes:
                if isinstance(attr, dict) and 'name' in attr and 'value_name' in attr:
                    attributes.append(f"{attr['name']}: {attr['value_name']}")

            sku.variant_display = " | ".join(attributes) if attributes else "Default"

    @api.depends('product_id.title', 'variant_display', 'seller_sku')
    def _compute_display_name(self):
        """Create display name for the SKU."""
        for sku in self:
            if sku.product_id:
                base_name = sku.product_id.title or "Unknown Product"
                variant = sku.variant_display or "Default"
                seller_sku = sku.seller_sku or ""

                if seller_sku:
                    sku.display_name = f"{base_name} - {variant} ({seller_sku})"
                else:
                    sku.display_name = f"{base_name} - {variant}"
            else:
                sku.display_name = f"SKU {sku.tiktok_id}"

    # ===== Helper Methods =====
    def _parse_sku_data(self, sku_data, product_id):
        """Parse SKU data from TikTok API response."""
        if not isinstance(sku_data, dict):
            return {}

        Shop = self.env['tiktok.shop']

        # Extract pricing information
        price_info = sku_data.get('price', {})

        # Extract inventory information
        inventory_info = sku_data.get('inventory', [])

        # Extract sales attributes
        sales_attrs = sku_data.get('sales_attributes', [])

        # Extract status information
        status_info = sku_data.get('status_info', {})

        # Extract listing policy
        listing_policy = sku_data.get('global_listing_policy', {})

        # Extract SKU images from sales attributes
        sku_images = []
        for attr in sales_attrs:
            if isinstance(attr, dict) and 'sku_img' in attr:
                sku_images.append(attr['sku_img'])

        return {
            'tiktok_id': sku_data.get('id'),
            'seller_sku': sku_data.get('seller_sku'),
            'product_id': product_id,
            'currency': price_info.get('currency', 'VND'),
            'sale_price': Shop._parse_number(price_info.get('sale_price', 0)),
            'tax_exclusive_price': Shop._parse_number(price_info.get('tax_exclusive_price', 0)),
            'inventory_details': inventory_info,
            'sales_attributes': sales_attrs,
            'status': status_info.get('status'),
            'status_info': status_info,
            'inventory_type': listing_policy.get('inventory_type'),
            'price_sync': listing_policy.get('price_sync', False),
            'global_listing_policy': listing_policy,
            'sku_images': sku_images,
        }

    @api.model
    def _upsert_sku(self, sku_data, product_id):
        """Create or update SKU from TikTok API data."""
        if not sku_data or not product_id:
            return False

        parsed_data = self._parse_sku_data(sku_data, product_id)
        if not parsed_data.get('tiktok_id'):
            _logger.warning("SKU data missing tiktok_id: %s", sku_data)
            return False

        # Find existing SKU
        # Upsert SKU using helper method
        sku = self.env['tiktok.shop']._upsert(
            'tiktok.sku',
            [('tiktok_id', '=', parsed_data['tiktok_id'])],
            parsed_data
        )
        return sku
