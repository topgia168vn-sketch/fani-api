import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Migration script để tạo TiktokSkuInventory records từ trường inventory_details JSON trong TiktokSku.
    """
    _logger.info("Starting migration: Create TiktokSkuInventory records from JSON data")

    env = api.Environment(cr, SUPERUSER_ID, {})

    skus = env['tiktok.sku'].search([('inventory_details', '!=', False)])

    if not skus:
        _logger.info("No skus with inventory_details data found")
        return

    _logger.info(f"Found {len(skus)} skus with inventory_details data")

    skus._compute_inventory_ids()
    created_count = len(skus.inventory_ids)

    _logger.info(f"Migration completed: Created {created_count} TiktokSkuInventory records")
