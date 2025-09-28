import logging
from datetime import datetime
from odoo import api, models, fields, _
from .tiktok_shop import MAX_CONCURRENT_THREADS

_logger = logging.getLogger(__name__)


class TiktokWarehouse(models.Model):
    _name = "tiktok.warehouse"
    _description = "TikTok Shop Warehouses"
    _order = "create_date desc"
    _rec_name = "name"

    # ===== Basic Information =====
    tiktok_id = fields.Char(string="TikTok Warehouse ID", required=True, index=True)
    entity_id = fields.Char(string="Entity ID", help="Used to associate physical information of a warehouse")
    name = fields.Char(string="Warehouse Name", required=True)

    # ===== Status Information =====
    effect_status = fields.Selection([
        ("ENABLED", "Enabled"),
        ("DISABLED", "Disabled"),
        ("RESTRICTED", "Restricted")
    ], string="Effect Status", help="ENABLED, DISABLED, or RESTRICTED (holiday mode or order limit mode)")

    # ===== Type Information =====
    type = fields.Selection([
        ("SALES_WAREHOUSE", "Sales Warehouse"),
        ("RETURN_WAREHOUSE", "Return Warehouse")
    ], string="Warehouse Type", help="SALES_WAREHOUSE (shipping products) or RETURN_WAREHOUSE (receiving returned products)")

    sub_type = fields.Selection([
        ("DOMESTIC_WAREHOUSE", "Domestic Warehouse"),
        ("CR_OVERSEA_WAREHOUSE", "Cross-border Overseas Warehouse"),
        ("CR_DIRECT_SHIPPING_WAREHOUSE", "Cross-border Direct Shipping Warehouse")
    ], string="Sub Type")

    is_default = fields.Boolean(string="Is Default Warehouse", default=False)

    # ===== Address Information =====
    region = fields.Char(string="Region")
    state = fields.Char(string="State/Province")
    city = fields.Char(string="City")
    district = fields.Char(string="District")
    town = fields.Char(string="Town")
    contact_person = fields.Char(string="Contact Person")

    # ===== Japanese Market Specific Fields =====
    first_name = fields.Char(string="First Name (Kanji)", help="Kanji first name (JP market only)")
    last_name = fields.Char(string="Last Name (Kanji)", help="Kanji last name (JP market only)")
    first_name_local_script = fields.Char(string="First Name (Local Script)", help="Hiragana or Katakana first name (JP market only)")
    last_name_local_script = fields.Char(string="Last Name (Local Script)", help="Hiragana or Katakana last name (JP market only)")

    # ===== Address Details =====
    postal_code = fields.Char(string="Postal Code")
    full_address = fields.Text(string="Full Address", help="Combined warehouse address")
    region_code = fields.Char(string="Region Code")
    phone_number = fields.Char(string="Phone Number")
    address_line1 = fields.Char(string="Address Line 1", help="Street name/number, neighborhood/district")
    address_line2 = fields.Char(string="Address Line 2", help="Flat, apartment, or suit")
    address_line3 = fields.Char(string="Address Line 3", help="Street number (Brazilian market only)")
    address_line4 = fields.Char(string="Address Line 4", help="Supplement information (flat, apartment, or suit, optional)")

    # ===== Geolocation =====
    latitude = fields.Char(string="Latitude")
    longitude = fields.Char(string="Longitude")

    # ===== Shop Reference =====
    shop_id = fields.Many2one("tiktok.shop", string="TikTok Shop", required=True, ondelete="cascade")

    # ===== Raw Data =====
    raw_payload = fields.Json(string="Raw Payload", help="Complete warehouse data from API")

    # ===== Computed Fields =====
    display_address = fields.Char(string="Display Address", compute="_compute_display_address")

    _sql_constraints = [
        ('unique_tiktok_id_per_shop', 'unique(tiktok_id, shop_id)', 'TikTok Warehouse ID must be unique per shop!'),
    ]

    @api.depends('full_address', 'city', 'state', 'region')
    def _compute_display_address(self):
        """Create a display-friendly address."""
        for warehouse in self:
            if warehouse.full_address:
                warehouse.display_address = warehouse.full_address
            else:
                # Build address from components
                address_parts = []
                if warehouse.city:
                    address_parts.append(warehouse.city)
                if warehouse.state:
                    address_parts.append(warehouse.state)
                if warehouse.region:
                    address_parts.append(warehouse.region)
                warehouse.display_address = ", ".join(address_parts) if address_parts else ""

    @api.model
    def _sync_warehouses(self, shop):
        """
        Sync warehouses từ TikTok Shop API.
        """
        shop.ensure_one()
        sync_from_cron = self.env.context.get('sync_from_cron', False)

        _logger.info(f"Shop {shop.name}: Starting warehouse sync")

        # Gọi API Get Warehouse List
        params = {
            'shop_cipher': shop.shop_cipher,
        }

        data = shop._request("GET", "/logistics/202309/warehouses", params=params)
        warehouses = data.get("warehouses", [])

        if not warehouses:
            _logger.warning(f"Shop {shop.name}: No warehouses found")
            if sync_from_cron:
                return {
                    'total_synced': 0,
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Warning'),
                        'message': _('No warehouses found!'),
                        'type': 'warning',
                    }
                }

        _logger.info(f"Shop {shop.name}: Processing {len(warehouses)} warehouses")

        # Process từng warehouse
        total_synced = 0
        for warehouse_data in warehouses:
            warehouse_id = warehouse_data.get('id')
            if not warehouse_id:
                continue

            # Extract address information
            address_info = warehouse_data.get('address', {})
            geolocation_info = warehouse_data.get('geolocation', {})

            # Prepare values
            values = {
                'tiktok_id': warehouse_id,
                'entity_id': warehouse_data.get('entity_id'),
                'name': warehouse_data.get('name'),
                'effect_status': warehouse_data.get('effect_status'),
                'type': warehouse_data.get('type'),
                'sub_type': warehouse_data.get('sub_type'),
                'is_default': warehouse_data.get('is_default', False),

                # Address fields
                'region': address_info.get('region'),
                'state': address_info.get('state'),
                'city': address_info.get('city'),
                'district': address_info.get('district'),
                'town': address_info.get('town'),
                'contact_person': address_info.get('contact_person'),

                # Japanese market fields
                'first_name': address_info.get('first_name'),
                'last_name': address_info.get('last_name'),
                'first_name_local_script': address_info.get('first_name_local_script'),
                'last_name_local_script': address_info.get('last_name_local_script'),

                # Address details
                'postal_code': address_info.get('postal_code'),
                'full_address': address_info.get('full_address'),
                'region_code': address_info.get('region_code'),
                'phone_number': address_info.get('phone_number'),
                'address_line1': address_info.get('address_line1'),
                'address_line2': address_info.get('address_line2'),
                'address_line3': address_info.get('address_line3'),
                'address_line4': address_info.get('address_line4'),

                # Geolocation
                'latitude': geolocation_info.get('latitude'),
                'longitude': geolocation_info.get('longitude'),

                # Shop reference
                'shop_id': shop.id,

                # Raw data
                'raw_payload': warehouse_data,
            }

            # Upsert warehouse using helper method
            self.env['tiktok.shop']._upsert(
                'tiktok.warehouse',
                [('tiktok_id', '=', warehouse_id), ('shop_id', '=', shop.id)],
                values
            )

            total_synced += 1

        _logger.info(f"Shop {shop.name}: Successfully synced {total_synced} warehouses")

        if sync_from_cron:
            return {
                'total_synced': total_synced,
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Synced %d warehouses successfully!') % total_synced,
                    'type': 'success',
                }
            }


class TiktokShop(models.Model):
    _inherit = "tiktok.shop"

    def action_sync_warehouses(self):
        """
        Đồng bộ Warehouses từ TikTok Shop API.
        - Single shop: chạy trực tiếp
        - Multiple shops: chạy đa luồng
        """
        if len(self) == 1:
            # Single shop - chạy trực tiếp
            return self.env["tiktok.warehouse"]._sync_warehouses(self)
        else:
            # Multiple shops - chạy đa luồng
            return self._run_multi_thread_tasks(
                self,
                "Sync Warehouses",
                self.env["tiktok.warehouse"]._sync_warehouses,
                max_workers=min(len(self), MAX_CONCURRENT_THREADS)
            )
