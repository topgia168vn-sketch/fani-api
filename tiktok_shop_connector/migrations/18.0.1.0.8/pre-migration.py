from odoo.tools.sql import rename_column


def migrate(cr, version):
    # Rename column in tiktok_sku_performance table
    rename_column(cr, 'tiktok_sku_performance', 'sku_id', 'tiktok_sku_id')
