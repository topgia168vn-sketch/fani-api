# -*- coding: utf-8 -*-
from odoo import fields, models


class PancakeGeoDistrict(models.Model):
    _name = "pancake.geo.district"
    _description = "Pancake Geo District"
    _rec_name = "name"
    _order = "name, id"

    pancake_id = fields.Char(
        string="Pancake District ID",
        required=True,
        index=True,
        help="Field 'id' from Pancake API /geo/districts"
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

    # Many2one theo yêu cầu (API field 'province_id')
    province_id = fields.Many2one(
        "pancake.geo.province",
        string="Province",
        required=True,
        index=True,
        ondelete="cascade",
        help="Field 'province_id' from Pancake API"
    )

    raw_payload = fields.Json(string="Raw Payload")

    # Quan hệ ngược
    commune_ids = fields.One2many(
        "pancake.geo.commune", "district_id", string="Communes"
    )

    _sql_constraints = [
        ("pancake_geo_district_uniq",
         "unique(pancake_id)",
         "District must be unique by Pancake District ID."),
    ]

    def _fetch_from_pancake(self, shop, province_records=None):
        """
        Private method: Tải danh mục quận/huyện từ /geo/districts cho từng province truyền vào
        (hoặc toàn bộ provinces đã có trong DB nếu không truyền).
        """
        if province_records is None:
            province_records = self.env["pancake.geo.province"].sudo().search([])

        districts = self.env["pancake.geo.district"].browse()
        for prov in province_records:
            params = {"province_id": prov.pancake_id}
            payload = shop._pancake_get(
                api_key=shop.api_key,
                path="/geo/districts",
                params=params,
            )
            items = (payload or {}).get("data") or []
            if not items:
                # Bỏ qua tỉnh này nếu không có dữ liệu, không raise toàn bộ flow
                continue

            for it in items:
                vals = {
                    "pancake_id": str(it.get("id")) if it.get("id") is not None else False,
                    "name": it.get("name"),
                    "name_en": it.get("name_en"),
                    "province_id": prov.id,  # M2O tới bản ghi tỉnh nội bộ
                    "raw_payload": it,
                }
                dom = [("pancake_id", "=", vals["pancake_id"])]
                districts |= shop._upsert("pancake.geo.district", dom, vals)
        return districts
