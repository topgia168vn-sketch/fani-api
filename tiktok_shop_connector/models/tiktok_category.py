import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class TiktokCategory(models.Model):
    _name = "tiktok.category"
    _description = "TikTok Shop Product Categories"
    _order = "parent_id, local_name"

    # ===== Basic Information =====
    tiktok_id = fields.Char(string="TikTok Category ID", required=True, index=True)
    parent_id = fields.Many2one("tiktok.category", string="Parent Category", index=True)
    local_name = fields.Char(string="Category Name", required=True)
    is_leaf = fields.Boolean(string="Is Leaf Category", default=False)

    # ===== Permission & Status =====
    permission_statuses = fields.Json(string="Permission Statuses", help="JSON array of permission statuses")

    # ===== Raw Data =====
    raw_payload = fields.Json()

    _sql_constraints = [
        ('unique_tiktok_id', 'unique(tiktok_id)', 'TikTok Category ID must be unique globally!'),
    ]

    @api.depends("parent_id", "local_name")
    def _compute_display_name(self):
        for record in self:
            if record.parent_id:
                record.display_name = f"{record.parent_id.display_name} > {record.local_name}"
            else:
                record.display_name = record.local_name

    @api.model
    def _sync_categories(self, shop):
        """
        Sync product categories từ TikTok Shop API.
        """
        shop.ensure_one()

        # Gọi API Get Categories
        params = {
            'shop_cipher': shop.shop_cipher,
            'locale': shop._get_current_locale(),
            'category_version': 'v1' if shop.region == 'non-us' else 'v2',
        }

        data = shop._request("GET", "/product/202309/categories", params=params)
        categories = data.get("categories", [])

        if not categories:
            _logger.warning(f"No categories found for shop {shop.name}")
            return

        # Sync categories vào database
        synced_count = 0

        for cat_data in categories:
            # Tìm parent category nếu có
            parent_category = False
            if cat_data.get('parent_id'):
                parent_category = self.search([
                    ('tiktok_id', '=', cat_data.get('parent_id'))
                ], limit=1)

            # Prepare values
            values = {
                'tiktok_id': cat_data.get('id'),
                'local_name': cat_data.get('local_name'),
                'is_leaf': cat_data.get('is_leaf', False),
                'parent_id': parent_category.id if parent_category else False,
                'permission_statuses': cat_data.get('permission_statuses', []),
                'raw_payload': cat_data,
            }

            # Upsert category using helper method
            self.env['tiktok.shop']._upsert(
                'tiktok.category',
                [('tiktok_id', '=', cat_data.get('id'))],
                values
            )

            synced_count += 1

        _logger.info(f"Successfully synced {synced_count} categories for shop {shop.name}")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Synced %d categories successfully!') % synced_count,
                'type': 'success',
            }
        }


class TiktokShop(models.Model):
    _inherit = "tiktok.shop"

    def action_sync_categories(self):
        shop = self.sorted('access_token', reverse=True)[:1]
        return self.env["tiktok.category"]._sync_categories(shop)
