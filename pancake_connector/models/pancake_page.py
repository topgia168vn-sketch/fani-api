# -*- coding: utf-8 -*-
from odoo import fields, models


class PancakePage(models.Model):
    _name = "pancake.page"
    _description = "Pancake Page"
    _rec_name = "name"
    _order = "name, id"

    # Trường từ API pages[].*
    pancake_id = fields.Char(
        string="Pancake Page ID",
        required=True,
        index=True,
        help="Field 'pages[].id' from Pancake API"
    )
    shop_id = fields.Many2one(
        "pancake.shop",
        string="Shop",
        required=True,
        index=True,
        ondelete="cascade",
        help="Field 'pages[].shop_id' from Pancake API (or parent shop)"
    )
    name = fields.Char(
        string="Name",
        required=True,
        help="Field 'pages[].name' from Pancake API"
    )
    platform = fields.Char(
        string="Platform",
        help="Field 'pages[].platform' from Pancake API (e.g. facebook/instagram/...)"
    )
    # 'settings' là object -> lưu JSON
    settings = fields.Json(
        string="Settings (JSON)",
        help="Field 'pages[].settings' from Pancake API"
    )

    # Lưu nguyên object page nếu cần
    raw_payload = fields.Json(
        string="Raw Payload",
        help="Full JSON of the page object as returned by Pancake"
    )

    _sql_constraints = [
        ("pancake_page_shop_pancake_id_uniq",
         "unique(shop_id, pancake_id)",
         "Pancake page must be unique by (Shop, Pancake Page ID)."),
    ]
