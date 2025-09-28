from odoo import api, SUPERUSER_ID

def migrate(cr, version):
    # Xóa hết dữ liệu 2 bảng
    cr.execute("TRUNCATE TABLE jst_sale_order_line RESTART IDENTITY CASCADE;")
    cr.execute("TRUNCATE TABLE jst_sale_order RESTART IDENTITY CASCADE;")
