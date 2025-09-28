from odoo import fields, models, _, api
from odoo.exceptions import ValidationError


class PancakeFetchGeoWizard(models.TransientModel):
    _name = "pancake.fetch.geo.wizard"
    _description = "Pancake Fetch Geographic Data Wizard"

    shop_id = fields.Many2one(
        "pancake.shop",
        string="Shop",
        required=True,
        default=lambda self: self.env["pancake.shop"].search([], limit=1),
        help="Select shop to fetch geographic data"
    )

    country_code = fields.Char(
        string="Country Code",
        default="84",
        required=True,
        help="Country code (84 for Vietnam)"
    )

    fetch_type = fields.Selection([
        ("old", "Old Provinces Only"),
        ("new", "New Provinces Only"),
        ("all", "All Provinces (Old + New)")
    ], string="Fetch Type", default="old", required=True)

    include_districts = fields.Boolean(
        string="Include Districts",
        default=True,
        help="Also fetch districts for all provinces"
    )

    include_communes = fields.Boolean(
        string="Include Communes",
        default=True,
        help="Also fetch communes for all districts"
    )

    @api.constrains("include_districts", "include_communes")
    def _check_include_districts_and_communes(self):
        if self.include_communes and not self.include_districts:
            raise ValidationError(_("You must include districts if you want to include communes"))

    def action_fetch_geo_data(self):
        """Fetch geographic data based on wizard settings"""
        self.ensure_one()

        # Prepare parameters for API call
        is_new = None
        all_provinces = None

        if self.fetch_type == "new":
            is_new = True
        elif self.fetch_type == "old":
            is_new = False
        elif self.fetch_type == "all":
            all_provinces = True

        # Fetch provinces
        provinces = self.env["pancake.geo.province"]._fetch_from_pancake(
            self.shop_id,
            country_code=self.country_code,
            is_new=is_new,
            all=all_provinces
        )

        # Fetch districts if requested
        if self.include_districts:
            districts = self.env["pancake.geo.district"]._fetch_from_pancake(
                self.shop_id,
                province_records=provinces
            )

            # Fetch communes if requested
            if self.include_communes:
                self.env["pancake.geo.commune"]._fetch_from_pancake(
                    self.shop_id,
                    district_records=districts
                )

        return {'type': 'ir.actions.client', 'tag': 'soft_reload'}
