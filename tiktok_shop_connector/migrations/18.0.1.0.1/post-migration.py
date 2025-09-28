import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Migration script để tạo TiktokSku records từ trường skus JSON trong TiktokProduct.
    """
    _logger.info("Starting migration: Create TiktokSku records from JSON data")

    env = api.Environment(cr, SUPERUSER_ID, {})

    # Lấy tất cả products có skus data
    products = env['tiktok.product'].search([('skus', '!=', False)])

    if not products:
        _logger.info("No products with SKU data found")
        return

    _logger.info(f"Found {len(products)} products with SKU data")

    sku_model = env['tiktok.sku']
    created_count = 0

    for product in products:
        skus_data = product.skus
        if not isinstance(skus_data, list):
            continue

        for sku_data in skus_data:
            if not isinstance(sku_data, dict):
                continue

            tiktok_sku_id = sku_data.get('id')
            if not tiktok_sku_id:
                continue

            # Check if SKU already exists
            existing_sku = sku_model.search([('tiktok_id', '=', tiktok_sku_id)], limit=1)
            if existing_sku:
                continue

            # Parse và tạo SKU
            try:
                price_info = sku_data.get('price', {})
                status_info = sku_data.get('status_info', {})
                listing_policy = sku_data.get('global_listing_policy', {})

                sku_model.create({
                    'tiktok_id': tiktok_sku_id,
                    'seller_sku': sku_data.get('seller_sku'),
                    'product_id': product.id,
                    'currency': price_info.get('currency', 'VND'),
                    'sale_price': float(price_info.get('sale_price', 0)) if price_info.get('sale_price') else 0,
                    'tax_exclusive_price': float(price_info.get('tax_exclusive_price', 0)) if price_info.get('tax_exclusive_price') else 0,
                    'inventory_details': sku_data.get('inventory', []),
                    'sales_attributes': sku_data.get('sales_attributes', []),
                    'status': status_info.get('status'),
                    'status_info': status_info,
                    'inventory_type': listing_policy.get('inventory_type'),
                    'price_sync': listing_policy.get('price_sync', False),
                    'global_listing_policy': listing_policy,
                })
                created_count += 1

            except Exception as e:
                _logger.error(f"Failed to create SKU {tiktok_sku_id}: {str(e)}")

    _logger.info(f"Migration completed: Created {created_count} SKUs")
