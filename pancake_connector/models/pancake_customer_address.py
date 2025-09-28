from odoo import fields, models


class PancakeCustomerAddress(models.Model):
    _name = "pancake.customer.address"
    _description = "Pancake Customer Address"
    _rec_name = "full_address"
    _order = "id"

    # API 'id' trong mảng shop_customer_addresses
    pancake_id = fields.Char(
        string="Pancake Address ID",
        required=True,
        index=True,
        help="Field 'shop_customer_addresses[].id' from API"
    )
    customer_id = fields.Many2one(
        "pancake.customer",
        string="Customer",
        required=True,
        index=True,
        ondelete="cascade",
        help="Belongs to Pancake Customer"
    )

    # Thông tin người nhận
    full_name = fields.Char(string="Full Name", help="Field 'full_name' if present")
    phone_number = fields.Char(string="Phone Number", help="Field 'phone_number'")

    # Địa chỉ chi tiết
    address_line = fields.Char(string="Address Line", help="Field 'address'")
    full_address = fields.Char(string="Full Address", help="Field 'full_address'")

    # Mã quốc gia & M2O địa giới (yêu cầu của bạn)
    country_code = fields.Char(string="Country Code", help="Field 'country_code'")
    province_id = fields.Many2one(
        "pancake.geo.province",
        string="Province",
        index=True,
        ondelete="restrict",
        help="Map from 'province_id' in API"
    )
    district_id = fields.Many2one(
        "pancake.geo.district",
        string="District",
        index=True,
        ondelete="restrict",
        help="Map from 'district_id' in API"
    )
    commune_id = fields.Many2one(
        "pancake.geo.commune",
        string="Commune",
        index=True,
        ondelete="restrict",
        help="Map from 'commune_id' in API"
    )

    # Lưu nguyên payload địa chỉ nếu cần tra cứu
    raw_payload = fields.Json(
        string="Raw Payload",
        help="Full JSON of shop_customer_addresses[] element"
    )

    _sql_constraints = [
        ("pancake_customer_addr_uniq",
         "unique(customer_id, pancake_id)",
         "Customer Address must be unique by (Customer, Pancake Address ID)."),
    ]
