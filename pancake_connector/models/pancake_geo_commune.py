# -*- coding: utf-8 -*-
from odoo import fields, models


class PancakeGeoCommune(models.Model):
    _name = "pancake.geo.commune"
    _description = "Pancake Geo Commune"
    _rec_name = "name"
    _order = "name, id"

    pancake_id = fields.Char(
        string="Pancake Commune ID",
        required=True,
        index=True,
        help="Field 'id' from Pancake API /geo/communes"
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
        string="New Commune ID",
        help="Field 'new_id' from Pancake API (VN only)"
    )
    postcode = fields.Char(
        string="Postcode",
        help="Field 'postcode' from Pancake API"
    )

    # Many2one theo yêu cầu (API field 'district_id' & 'province_id')
    district_id = fields.Many2one(
        "pancake.geo.district",
        string="District",
        required=True,
        index=True,
        ondelete="cascade",
        help="Field 'district_id' from Pancake API"
    )
    province_id = fields.Many2one(
        "pancake.geo.province",
        string="Province",
        required=True,
        index=True,
        ondelete="cascade",
        help="Field 'province_id' from Pancake API"
    )

    raw_payload = fields.Json(string="Raw Payload")

    _sql_constraints = [
        ("pancake_geo_commune_uniq",
            "unique(pancake_id)",
            "Commune must be unique by Pancake Commune ID."),
    ]

    def _fetch_from_pancake(self, shop, district_records=None):
        """
        Private method: Tải danh mục phường/xã từ /geo/communes cho từng district truyền vào
        (hoặc toàn bộ districts đã có nếu không truyền).
        API yêu cầu cả province_id và district_id trong query.
        """
        if district_records is None:
            district_records = self.env["pancake.geo.district"].sudo().search([])

        communes = self.env["pancake.geo.commune"].browse()
        for dist in district_records:
            if not dist.province_id or not dist.province_id.pancake_id:
                # Bảo đảm có province liên kết và có mã pancake_id
                continue
            params = {
                "province_id": dist.province_id.pancake_id,
                "district_id": dist.pancake_id,
            }
            payload = shop._pancake_get(
                api_key=shop.api_key,
                path="/geo/communes",
                params=params,
            )
            items = (payload or {}).get("data") or []
            if not items:
                continue

            for it in items:
                vals = {
                    "pancake_id": str(it.get("id")) if it.get("id") is not None else False,
                    "name": it.get("name"),
                    "name_en": it.get("name_en"),
                    "new_id": it.get("new_id"),
                    "postcode": it.get("postcode"),
                    # link M2O tới district/province nội bộ (đã fetch ở bước trước)
                    "district_id": dist.id,
                    "province_id": dist.province_id.id,
                    "raw_payload": it,
                }
                dom = [("pancake_id", "=", vals["pancake_id"])]
                communes |= shop._upsert("pancake.geo.commune", dom, vals)
        return communes
