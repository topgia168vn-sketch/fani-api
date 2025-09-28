def migrate(cr, version):
    """
    Update sync_data_since cho tất cả các shop là 01/08/2025 00:00:00 (31/07/2025 17:00:00 UTC)
    """
    cr.execute("""
        UPDATE tiktok_shop
        SET sync_data_since = '2025-07-31 17:00:00'
    """)
