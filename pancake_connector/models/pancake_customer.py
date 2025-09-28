import logging
from datetime import datetime
from odoo import fields, models

_logger = logging.getLogger(__name__)


class PancakeCustomer(models.Model):
    _name = "pancake.customer"
    _description = "Pancake Customer"
    _rec_name = "name"
    _order = "name, id"

    # API 'id' -> tránh đè id Odoo
    pancake_id = fields.Char(
        string="Pancake Customer ID",
        required=True,
        index=True,
        help="Field 'id' from Pancake API /shops/<SHOP_ID>/customers"
    )
    shop_id = fields.Many2one(
        "pancake.shop",
        string="Shop",
        required=True,
        index=True,
        ondelete="cascade",
        help="Belongs to Pancake Shop"
    )

    # Thông tin cơ bản
    name = fields.Char(string="Name", help="Field 'name' from API")
    gender = fields.Char(string="Gender", help="Field 'gender' from API")
    date_of_birth = fields.Date(string="Date of Birth", help="Field 'date_of_birth'")

    # Danh sách email / SĐT giữ nguyên JSON
    emails = fields.Json(
        string="Emails (JSON)",
        help="Array 'emails' from API"
    )
    phone_numbers = fields.Json(
        string="Phone Numbers (JSON)",
        help="Array 'phone_numbers' from API"
    )

    # Các thống kê & nhận diện khác
    order_count = fields.Integer(string="Order Count", help="Field 'order_count'")
    succeed_order_count = fields.Integer(string="Succeed Order Count", help="Field 'succeed_order_count'")
    purchased_amount = fields.Integer(
        string="Purchased Amount (VND)",
        help="Field 'purchased_amount' (đơn vị đồng, lưu số nguyên)"
    )
    last_order_at = fields.Datetime(string="Last Order At", help="Field 'last_order_at'")

    fb_id = fields.Char(string="Facebook ID", help="Field 'fb_id'")
    referral_code = fields.Char(string="Referral Code", help="Field 'referral_code'")
    # reward_point có thể xuất hiện trong API → lưu nếu có
    reward_point = fields.Float(string="Reward Point", help="Field 'reward_point' (if present)")

    # Dấu vết thời gian từ API — tiện incremental sync
    inserted_at = fields.Datetime(string="Inserted At")
    updated_at = fields.Datetime(string="Updated At")

    # JSON full để lần vết (gồm: tags, shop_customer_addresses, v.v…)
    raw_payload = fields.Json(
        string="Raw Payload",
        help="Full JSON customer object from API"
    )

    # Quan hệ
    address_ids = fields.One2many(
        "pancake.customer.address",
        "customer_id",
        string="Addresses"
    )

    _sql_constraints = [
        ("pancake_customer_shop_pancake_id_uniq",
         "unique(shop_id, pancake_id)",
         "Customer must be unique by (Shop, Pancake ID)."),
    ]

    def _fetch_from_pancake(self, shop, updated_since=None, page_size=30, max_pages=None):
        """
        Private method: Đồng bộ danh sách Customers từ Pancake.
        - Nếu updated_since được truyền (datetime), chỉ lấy các bản ghi cập nhật sau thời điểm này.
        - page_size: số record mỗi lần gọi API (mặc định 30, tối đa 100).
        - max_pages: giới hạn số trang để tránh loop quá lớn (None = lấy hết).
        """
        page_number = 1
        total_imported = 0
        customers = self.env["pancake.customer"].browse()
        while True:
            params = {"page_number": page_number, "page_size": page_size}
            if updated_since:
                if isinstance(updated_since, datetime):
                    # Convert to Unix timestamp (seconds)
                    updated_timestamp = int(updated_since.timestamp())
                else:
                    # Assume it's already a timestamp
                    updated_timestamp = int(updated_since)
                params["start_time_updated_at"] = updated_timestamp

            payload = shop._pancake_get(shop.api_key, f"/shops/{shop.pancake_id}/customers", params=params)
            items = (payload or {}).get("data") or []
            if not items:
                break

            for it in items:
                cust_vals = {
                    "pancake_id": str(it.get("id")),
                    "shop_id": shop.id,
                    "name": it.get("name"),
                    "emails": it.get("emails"),
                    "phone_numbers": it.get("phone_numbers"),
                    "gender": it.get("gender"),
                    "date_of_birth": shop._parse_date(it.get("date_of_birth")) or False,
                    "order_count": it.get("order_count"),
                    "succeed_order_count": it.get("succeed_order_count"),
                    "purchased_amount": it.get("purchased_amount"),
                    "last_order_at": shop._parse_dt(it.get("last_order_at")) or False,
                    "fb_id": it.get("fb_id"),
                    "referral_code": it.get("referral_code"),
                    "reward_point": it.get("reward_point"),
                    "inserted_at": shop._parse_dt(it.get("inserted_at")) or False,
                    "updated_at": shop._parse_dt(it.get("updated_at")) or False,
                    "raw_payload": it,
                }
                domain = [("shop_id", "=", shop.id), ("pancake_id", "=", cust_vals["pancake_id"])]
                customer = shop._upsert("pancake.customer", domain, cust_vals)
                customers |= customer

                # Sync addresses
                for addr in (it.get("shop_customer_addresses") or []):
                    addr_vals = {
                        "pancake_id": str(addr.get("id")),
                        "customer_id": customer.id,
                        "full_name": addr.get("full_name"),
                        "phone_number": addr.get("phone_number"),
                        "address_line": addr.get("address"),
                        "full_address": addr.get("full_address"),
                        "country_code": addr.get("country_code"),
                        "province_id": self.env["pancake.geo.province"]
                            .search([("pancake_id", "=", str(addr.get("province_id")))], limit=1).id,
                        "district_id": self.env["pancake.geo.district"]
                            .search([("pancake_id", "=", str(addr.get("district_id")))], limit=1).id,
                        "commune_id": self.env["pancake.geo.commune"]
                            .search([("pancake_id", "=", str(addr.get("commune_id")))], limit=1).id,
                        "raw_payload": addr,
                    }
                    dom_addr = [("customer_id", "=", customer.id), ("pancake_id", "=", addr_vals["pancake_id"])]
                    shop._upsert("pancake.customer.address", dom_addr, addr_vals)

            total_imported += len(items)
            meta = (payload or {}).get("meta") or {}
            total = meta.get("total")
            page_size_actual = meta.get("page_size") or page_size
            if total and page_number * page_size_actual >= total:
                break
            page_number += 1
            if max_pages and page_number > max_pages:
                break

        _logger.info("Fetched %s customers for shop %s", total_imported, shop.name)
        return customers
