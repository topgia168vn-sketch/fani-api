def migrate(cr, version):
    """
    Update product_id và sku_id trong tiktok.order.line từ tiktok_sku_id   
    """
    cr.execute("""
        UPDATE tiktok_order_line tol
        SET product_id = tsk.product_id,
            sku_id = tsk.id
        FROM tiktok_sku tsk
        WHERE tol.tiktok_sku_id IS NOT NULL AND tol.tiktok_sku_id = tsk.tiktok_id
    """)
