import logging
from datetime import datetime
from odoo import api, models, fields, _
from .tiktok_shop import MAX_CONCURRENT_THREADS

_logger = logging.getLogger(__name__)


class TiktokProduct(models.Model):
    _name = "tiktok.product"
    _description = "TikTok Shop Products"
    _order = "create_time desc"
    _rec_name = "title"

    # ===== Basic Information =====
    tiktok_id = fields.Char(string="TikTok Product ID", required=True, index=True)
    title = fields.Char(string="Product Title", required=True)
    status = fields.Char(string="Product Status")
    product_status = fields.Char(string="Product Status (Detailed)")
    product_types = fields.Json(string="Product Types")

    # ===== Classification =====
    category_chains = fields.Json(string="Category Chains")
    category_id = fields.Many2one("tiktok.category", string="Category", compute="_compute_category_id", store=True)
    brand = fields.Json(string="Brand Information")

    # ===== Media =====
    main_images = fields.Json(string="Main Images")
    video = fields.Json(string="Product Video")

    # ===== Content =====
    description = fields.Html(string="Description")

    # ===== Physical Properties =====
    package_dimensions = fields.Json(string="Package Dimensions")
    package_weight = fields.Json(string="Package Weight")

    # ===== SKUs =====
    skus = fields.Json(string="SKUs (Raw Data)")
    sku_ids = fields.One2many("tiktok.sku", "product_id", string="SKUs")

    # ===== Certifications =====
    certifications = fields.Json(string="Certifications")

    # ===== Size Chart =====
    size_chart = fields.Json(string="Size Chart")

    # ===== Product Attributes =====
    product_attributes = fields.Json(string="Product Attributes")

    # ===== Audit & Quality =====
    audit_failed_reasons = fields.Json(string="Audit Failed Reasons")
    listing_quality_tier = fields.Char(string="Listing Quality Tier")
    audit = fields.Json(string="Audit Information")

    # ===== Delivery & Shipping =====
    delivery_options = fields.Json(string="Delivery Options")
    is_cod_allowed = fields.Boolean(string="COD Allowed")
    shipping_insurance_requirement = fields.Char(string="Shipping Insurance Requirement")

    # ===== External References =====
    external_product_id = fields.Char(string="External Product ID")
    manufacturer_ids = fields.Json(string="Manufacturer IDs")
    responsible_person_ids = fields.Json(string="Responsible Person IDs")

    # ===== Product Features =====
    is_not_for_sale = fields.Boolean(string="Not For Sale")
    is_pre_owned = fields.Boolean(string="Pre Owned")
    minimum_order_quantity = fields.Integer(string="Minimum Order Quantity")

    # ===== Global Product =====
    global_product_association = fields.Json(string="Global Product Association")
    is_replicated = fields.Boolean(string="Is Replicated")

    # ===== Subscription =====
    subscribe_info = fields.Json(string="Subscribe Information")

    # ===== Product Families =====
    product_families = fields.Json(string="Product Families")
    primary_combined_product_id = fields.Char(string="Primary Combined Product ID")

    # ===== Platform Integration =====
    integrated_platform_statuses = fields.Json(string="Integrated Platform Statuses")

    # ===== Recommendations =====
    recommended_categories = fields.Json(string="Recommended Categories")

    # ===== Prescription =====
    prescription_requirement = fields.Json(string="Prescription Requirement")

    # ===== Draft Status =====
    has_draft = fields.Boolean(string="Has Draft")

    # ===== Timestamps =====
    create_time = fields.Datetime(string="Create Time")
    update_time = fields.Datetime(string="Update Time")

    # ===== Shop Reference =====
    shop_id = fields.Many2one("tiktok.shop", string="TikTok Shop", required=True, index=True, ondelete="cascade")

    # ===== Raw Data =====
    raw_payload = fields.Json()

    _sql_constraints = [
        ('unique_tiktok_id_per_shop', 'unique(tiktok_id, shop_id)', 'TikTok Product ID must be unique per shop!'),
    ]

    @api.depends('category_chains')
    def _compute_category_id(self):
        """
        Compute category_id từ category_chains.
        Lấy category cuối cùng (leaf category) trong chain và tìm record tương ứng.
        """
        for record in self:
            if record.category_chains and isinstance(record.category_chains, list):
                # Tìm category cuối cùng (leaf category)
                target_category_id = None
                for category in reversed(record.category_chains):
                    if category.get('is_leaf', False):
                        target_category_id = category.get('id')
                        break
                else:
                    # Nếu không có leaf category, lấy category cuối cùng
                    if record.category_chains:
                        target_category_id = record.category_chains[-1].get('id')

                # Tìm record trong tiktok.category
                if target_category_id:
                    category_record = self.env['tiktok.category'].search([
                        ('tiktok_id', '=', target_category_id)
                    ], limit=1)
                    record.category_id = category_record.id if category_record else False
                else:
                    record.category_id = False
            else:
                record.category_id = False

    @api.model
    def _get_smart_updated_since(self, shop):
        """
        Lấy updated_since thông minh cho shop.
        """
        shop.ensure_one()

        # Tìm max update_time của products trong shop này
        updated_since = self.env['tiktok.product'].search([
            ('shop_id', '=', shop.id)
        ], order='update_time desc', limit=1).update_time

        if updated_since:
            last_cron_start = self.env['tiktok.shop']._get_last_cron_start('tiktok_shop_connector.ir_cron_sync_tiktok_all_data')
            if last_cron_start:
                updated_since = min(updated_since, last_cron_start)

            _logger.info(f"Shop {shop.name}: Incremental product sync since {updated_since.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            _logger.info(f"Shop {shop.name}: Full product sync (no previous products)")
            updated_since = None

        return updated_since

    @api.model
    def _sync_products(self, shop, updated_since=None, page_size=100, max_page=None):
        """
        Sync products từ TikTok Shop API.
        Process từng page để tiết kiệm memory.
        """
        shop.ensure_one()
        sync_from_cron = self.env.context.get('sync_from_cron', False)

        _logger.info(f"Shop {shop.name}: Starting product sync")

        page_token = None
        page_number = 1
        total_synced = 0

        json_body = None
        if not updated_since:
            updated_since = self._get_smart_updated_since(shop)
        if updated_since:
            if isinstance(updated_since, datetime):
                updated_timestamp = int(updated_since.timestamp())
            else:
                updated_timestamp = int(updated_since)
            json_body = {
                'update_time_ge': updated_timestamp
            }

        while not max_page or page_number <= max_page:
            # Gọi API Search Products
            params = {
                'shop_cipher': shop.shop_cipher,
                'page_size': page_size,
            }
            if page_token:
                params['page_token'] = page_token

            data = shop._request("POST", "/product/202309/products/search", params=params, json_body=json_body)
            products = data.get("products", [])

            if not products:
                page_token = None
                break

            _logger.info(f"Shop {shop.name}: Processing page {page_number}, got {len(products)} products")

            # Process từng product trong page này
            page_synced = 0
            for product_data in products:
                product_id = product_data.get('id')
                if not product_id:
                    continue

                # Gọi API Get Product để lấy chi tiết đầy đủ
                detail_params = {
                    'shop_cipher': shop.shop_cipher,
                }

                product_detail = shop._request("GET", f"/product/202309/products/{product_id}", params=detail_params)

                # Prepare values từ Get Product response (complete data)
                values = {
                    'tiktok_id': product_detail.get('id'),
                    'title': product_detail.get('title'),
                    'status': product_detail.get('status'),
                    'product_status': product_detail.get('product_status'),
                    'product_types': product_detail.get('product_types', []),
                    'category_chains': product_detail.get('category_chains', []),
                    'brand': product_detail.get('brand', {}),
                    'main_images': product_detail.get('main_images', []),
                    'video': product_detail.get('video', {}),
                    'description': product_detail.get('description'),
                    'package_dimensions': product_detail.get('package_dimensions', {}),
                    'package_weight': product_detail.get('package_weight', {}),
                    'skus': product_detail.get('skus', []),
                    'certifications': product_detail.get('certifications', []),
                    'size_chart': product_detail.get('size_chart', {}),
                    'product_attributes': product_detail.get('product_attributes', []),
                    'audit_failed_reasons': product_detail.get('audit_failed_reasons', []),
                    'listing_quality_tier': product_detail.get('listing_quality_tier'),
                    'audit': product_detail.get('audit', {}),
                    'delivery_options': product_detail.get('delivery_options', []),
                    'is_cod_allowed': product_detail.get('is_cod_allowed', False),
                    'shipping_insurance_requirement': product_detail.get('shipping_insurance_requirement'),
                    'external_product_id': product_detail.get('external_product_id'),
                    'manufacturer_ids': product_detail.get('manufacturer_ids', []),
                    'responsible_person_ids': product_detail.get('responsible_person_ids', []),
                    'is_not_for_sale': product_detail.get('is_not_for_sale', False),
                    'is_pre_owned': product_detail.get('is_pre_owned', False),
                    'minimum_order_quantity': product_detail.get('minimum_order_quantity'),
                    'global_product_association': product_detail.get('global_product_association', {}),
                    'is_replicated': product_detail.get('is_replicated', False),
                    'subscribe_info': product_detail.get('subscribe_info', {}),
                    'product_families': product_detail.get('product_families', []),
                    'primary_combined_product_id': product_detail.get('primary_combined_product_id'),
                    'integrated_platform_statuses': product_detail.get('integrated_platform_statuses', []),
                    'recommended_categories': product_detail.get('recommended_categories', []),
                    'prescription_requirement': product_detail.get('prescription_requirement', {}),
                    'has_draft': product_detail.get('has_draft', False),
                    'create_time': shop._convert_unix_to_datetime(product_detail.get('create_time')),
                    'update_time': shop._convert_unix_to_datetime(product_detail.get('update_time')),
                    'shop_id': shop.id,
                    'raw_payload': product_detail,  # Store complete detail data
                }

                # Upsert product using helper method
                product = self.env['tiktok.shop']._upsert(
                    'tiktok.product',
                    [('tiktok_id', '=', product_id), ('shop_id', '=', shop.id)],
                    values
                )

                # Sync SKUs for this product
                skus_data = product_detail.get('skus', [])
                if skus_data:
                    sku_model = self.env['tiktok.sku']
                    for sku_data in skus_data:
                        sku_model._upsert_sku(sku_data, product.id)

                page_synced += 1
                total_synced += 1

            # Check pagination
            page_token = data.get("next_page_token")
            if not page_token:
                break

            page_number += 1

        if total_synced == 0:
            _logger.warning(f"Shop {shop.name}: No products found")
            if sync_from_cron:
                return {
                    'total_synced': total_synced,
                    'has_next_page': bool(page_token),
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Warning'),
                        'message': _('No products found!'),
                        'type': 'warning',
                    }
                }

        if sync_from_cron:
            return {
                'total_synced': total_synced,
                'has_next_page': bool(page_token),
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Synced %d products successfully!') % total_synced,
                    'type': 'success',
                }
            }


class TiktokShop(models.Model):
    _inherit = "tiktok.shop"

    def action_sync_products(self):
        """
        Đồng bộ Products từ TikTok Shop API.
        - Single shop: chạy trực tiếp
        - Multiple shops: chạy đa luồng
        """
        if len(self) == 1:
            # Single shop - chạy trực tiếp
            return self.env["tiktok.product"]._sync_products(self)
        else:
            # Multiple shops - chạy đa luồng
            return self._run_multi_thread_tasks(
                self,
                "Sync Products",
                self.env["tiktok.product"]._sync_products,
                max_workers=min(len(self), MAX_CONCURRENT_THREADS)
            )
