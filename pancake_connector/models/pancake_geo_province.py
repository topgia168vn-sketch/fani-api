from odoo import fields, models, _
from odoo.exceptions import UserError


class PancakeGeoProvince(models.Model):
    _name = "pancake.geo.province"
    _description = "Pancake Geo Province"
    _rec_name = "name"
    _order = "name, id"

    # API 'id' -> tránh đè id mặc định của Odoo
    pancake_id = fields.Char(
        string="Pancake Province ID",
        required=True,
        index=True,
        help="Field 'id' from Pancake API /geo/provinces"
    )
    name = fields.Char(
        string="Name",
        required=True,
        help="Field 'name' from Pancake API"
    )
    name_en = fields.Char(
        string="English Name",
        help="Field 'name_en' from Pancake API"
    )
    new_id = fields.Char(
        string="New Province ID",
        help="Field 'new_id' from Pancake API (VN only)"
    )
    # Tham số truy vấn của API có country_code (mặc định 84). Không bắt buộc, lưu nếu cần.
    country_code = fields.Char(
        string="Country Code",
        help="Query parameter 'country_code' used to fetch this record (e.g., '84')"
    )

    # Lưu nguyên payload để lần vết
    raw_payload = fields.Json(string="Raw Payload")

    # Quan hệ ngược
    district_ids = fields.One2many(
        "pancake.geo.district", "province_id", string="Districts"
    )
    commune_ids = fields.One2many(
        "pancake.geo.commune", "province_id", string="Communes"
    )

    _sql_constraints = [
        ("pancake_geo_province_uniq",
         "unique(pancake_id)",
         "Province must be unique by Pancake Province ID."),
    ]

    def _fetch_from_pancake(self, shop, country_code="84", is_new=False, all=False):
        """
        Private method: Tải danh mục tỉnh/thành từ /geo/provinces và upsert vào pancake.geo.province.
        """
        params = {"country_code": str(country_code)}
        # Chỉ set khi người dùng muốn — đúng theo API
        if is_new:
            params["is_new"] = "true"
        if all:
            params["all"] = "true"

        payload = shop._pancake_get(
            api_key=shop.api_key,
            path="/geo/provinces",
            params=params,
        )
        items = (payload or {}).get("data") or []
        if not items:
            # API trả rỗng thì báo rõ
            raise UserError(_("No provinces returned from Pancake"))

        provinces = self.env["pancake.geo.province"].browse()
        for it in items:
            vals = {
                "pancake_id": str(it.get("id")) if it.get("id") is not None else False,
                "name": it.get("name"),
                "name_en": it.get("name_en"),
                "new_id": it.get("new_id"),
                "country_code": str(country_code),
                "raw_payload": it,
            }
            dom = [("pancake_id", "=", vals["pancake_id"])]
            provinces |= shop._upsert("pancake.geo.province", dom, vals)
        return provinces
