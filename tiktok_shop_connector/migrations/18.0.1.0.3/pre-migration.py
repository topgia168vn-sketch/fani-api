from odoo.tools.sql import rename_column, create_column


def _set_no_translate_for_local_name(cr):
    """
    Đổi trường local_name từ Json (translated=True) sang Char (translated=False)
    """
    rename_column(cr, 'tiktok_category', 'local_name', 'local_name_old')
    create_column(cr, 'tiktok_category', 'local_name', 'varchar')
    cr.execute("UPDATE tiktok_category SET local_name = COALESCE(local_name_old ->> 'vi_VN', local_name_old ->> 'en_US')")
    cr.execute("ALTER TABLE tiktok_category DROP COLUMN local_name_old")


def migrate(cr, version):
    _set_no_translate_for_local_name(cr)
