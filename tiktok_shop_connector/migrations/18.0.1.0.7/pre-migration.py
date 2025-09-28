from odoo.tools.sql import rename_column


def migrate(cr, version):
    """Rename columns in tiktok_order table to match API response keys."""
    column_renames = {
        'order_status': 'states',
        'buyer_uid': 'user_id',
        'order_remark': 'seller_note',
        'commerce_platform': 'ecommerce_platform',
    }
    for old_name, new_name in column_renames.items():
        rename_column(cr, 'tiktok_order', old_name, new_name)
