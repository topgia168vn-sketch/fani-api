def migrate(cr, version):
    """
    Thêm cột kiểu Char để tiện theo dõi trên views
    """
    
    def add_column_if_not_exists(table_name, column_name, column_type="VARCHAR"):
        """Helper function to add column only if it doesn't exist"""
        cr.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s;
        """, (table_name, column_name))
        
        if not cr.fetchone():
            cr.execute(f'ALTER TABLE {table_name} ADD COLUMN "{column_name}" {column_type};')
            return True
        return False
    
    # 1 Table jst_sale_order: orderId_str
    add_column_if_not_exists('jst_sale_order', 'orderId_str')
    # Copy data from integer orderId to temporary char column
    cr.execute("""
        UPDATE jst_sale_order 
        SET "orderId_str" = CAST("orderId" AS VARCHAR)
        WHERE "orderId" IS NOT NULL;
    """)
    
    # 2 Table jst_sale_order_after: orderId_str, afterSaleOrderId_str
    add_column_if_not_exists('jst_sale_order_after', 'orderId_str')
    add_column_if_not_exists('jst_sale_order_after', 'afterSaleOrderId_str')
    # Copy data from integer orderId and afterSaleOrderId to temporary char columns
    cr.execute("""
        UPDATE jst_sale_order_after
        SET "orderId_str" = CAST("orderId" AS VARCHAR),
            "afterSaleOrderId_str" = CAST("afterSaleOrderId" AS VARCHAR)
        WHERE "orderId" IS NOT NULL OR "afterSaleOrderId" IS NOT NULL;
    """)
    
    # 3 Table jst_stock_inout: orderId_str
    add_column_if_not_exists('jst_stock_inout', 'orderId_str')
    # Copy data from integer orderId to temporary char column
    cr.execute("""
        UPDATE jst_stock_inout 
        SET "orderId_str" = CAST("orderId" AS VARCHAR)
        WHERE "orderId" IS NOT NULL;
    """)
