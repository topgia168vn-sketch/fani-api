import logging
from datetime import datetime
from odoo import api, models, fields, _
from .tiktok_shop import MAX_CONCURRENT_THREADS

_logger = logging.getLogger(__name__)


class TiktokCancel(models.Model):
    _name = "tiktok.cancel"
    _description = "TikTok Shop Cancellations"
    _order = "create_time desc"
    _rec_name = "cancel_id"

    # ===== Basic Information =====
    cancel_id = fields.Char(string="Cancel ID", required=True, index=True)
    order_id = fields.Many2one("tiktok.order", string="Original Order", ondelete="set null")
    tiktok_order_id = fields.Char(string="TikTok Order ID", help="Original order ID from TikTok")

    # ===== Cancel Type & Status =====
    cancel_type = fields.Selection([
        ("CANCEL", "Cancel by Seller/System"),
        ("BUYER_CANCEL", "Cancel by Buyer")
    ], string="Cancel Type")

    cancel_status = fields.Selection([
        ("CANCELLATION_REQUEST_PENDING", "Request Pending"),
        ("CANCELLATION_REQUEST_SUCCESS", "Request Success"),
        ("CANCELLATION_REQUEST_CANCEL", "Request Cancelled"),
        ("CANCELLATION_REQUEST_COMPLETE", "Request Complete")
    ], string="Cancel Status")

    # ===== Cancel Details =====
    role = fields.Selection([
        ("BUYER", "Buyer"),
        ("SELLER", "Seller"),
        ("OPERATOR", "Operator"),
        ("SYSTEM", "System")
    ], string="Initiator Role")

    cancel_reason_id = fields.Many2one("tiktok.cancel.reason", string="Cancel Reason", ondelete="set null")

    # ===== Timeline =====
    create_time = fields.Datetime(string="Create Time", index=True)
    update_time = fields.Datetime(string="Update Time", index=True)

    # ===== Seller Actions =====
    seller_next_action = fields.Char(string="Seller Next Action")
    seller_action_deadline = fields.Datetime(string="Seller Action Deadline")

    # ===== Financial Information =====
    refund_currency = fields.Char(string="Refund Currency")
    refund_total = fields.Float(string="Refund Total", digits="Product Price")
    refund_subtotal = fields.Float(string="Refund Subtotal", digits="Product Price")
    refund_shipping_fee = fields.Float(string="Refund Shipping Fee", digits="Product Price")
    refund_tax = fields.Float(string="Refund Tax", digits="Product Price")
    retail_delivery_fee = fields.Float(string="Retail Delivery Fee", digits="Product Price")
    buyer_service_fee = fields.Float(string="Buyer Service Fee", digits="Product Price")

    # ===== Relationships =====
    line_ids = fields.One2many("tiktok.cancel.line", "cancel_id", string="Cancel Lines")
    shop_id = fields.Many2one("tiktok.shop", string="TikTok Shop", required=True, index=True, ondelete="cascade")

    # ===== Raw Data =====
    raw_payload = fields.Json(string="Raw Payload")

    _sql_constraints = [
        ('unique_cancel_id_per_shop', 'unique(cancel_id, shop_id)', 'Cancel ID must be unique per shop!'),
    ]

    @api.model
    def _get_smart_updated_since(self, shop):
        """
        Lấy updated_since thông minh cho shop (updated_since hoặc sync_data_since).
        """
        shop.ensure_one()
        sync_data_since = shop.sync_data_since

        # Tìm max update_time của cancels trong shop này
        updated_since = self.env['tiktok.cancel'].search([
            ('shop_id', '=', shop.id)
        ], order='update_time desc', limit=1).update_time

        if updated_since:
            last_cron_start = self.env['tiktok.shop']._get_last_cron_start('tiktok_shop_connector.ir_cron_sync_tiktok_all_data')
            if last_cron_start:
                updated_since = min(updated_since, last_cron_start)
            if sync_data_since:
                updated_since = max(updated_since, sync_data_since)
            _logger.info(f"Shop {shop.name}: Incremental cancellation sync since {updated_since.strftime('%Y-%m-%d %H:%M:%S')}")

        else:
            if sync_data_since:
                updated_since = sync_data_since
                _logger.info(f"Shop {shop.name}: Full cancellation sync since {updated_since.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                updated_since = None
                _logger.info(f"Shop {shop.name}: Full cancellation sync")

        return updated_since

    @api.model
    def _sync_cancellations(self, shop, updated_since=None, page_size=50, max_page=None):
        """
        Sync cancellations từ TikTok Shop API.
        """
        shop.ensure_one()
        sync_from_cron = self.env.context.get('sync_from_cron', False)

        _logger.info(f"Shop {shop.name}: Starting cancellation sync")

        page_token = None
        page_number = 1
        total_synced = 0

        json_body = {'locale': shop._get_current_locale()}
        if not updated_since:
            updated_since = self._get_smart_updated_since(shop)
        if updated_since:
            if isinstance(updated_since, datetime):
                updated_timestamp = int(updated_since.timestamp())
            else:
                updated_timestamp = int(updated_since)
            json_body['update_time_ge'] = updated_timestamp

        while not max_page or page_number <= max_page:
            # Gọi API Search Cancellations
            params = {
                'shop_cipher': shop.shop_cipher,
                'page_size': page_size,
                'sort_field': 'update_time',
                'sort_order': 'ASC',
            }
            if page_token:
                params['page_token'] = page_token

            data = shop._request("POST", "/return_refund/202309/cancellations/search", params=params, json_body=json_body)
            cancellations = data.get("cancellations", [])

            if not cancellations:
                page_token = None
                break

            _logger.info(f"Shop {shop.name}: Processing page {page_number}, got {len(cancellations)} cancellations")

            # Process từng cancellation
            for cancel_data in cancellations:
                cancel_id = cancel_data.get('cancel_id')
                if not cancel_id:
                    continue

                # Extract seller next action
                seller_actions = cancel_data.get('seller_next_action_response', [])
                seller_next_action = None
                seller_action_deadline = None
                if seller_actions:
                    action_data = seller_actions[0]
                    seller_next_action = action_data.get('action')
                    deadline_timestamp = action_data.get('deadline')
                    if deadline_timestamp:
                        seller_action_deadline = shop._convert_unix_to_datetime(deadline_timestamp)

                # Extract refund amount
                refund_amount = cancel_data.get('refund_amount', {})
                refund_currency = refund_amount.get('currency')
                refund_total = shop._parse_number(refund_amount.get('refund_total', 0))
                refund_subtotal = shop._parse_number(refund_amount.get('refund_subtotal', 0))
                refund_shipping_fee = shop._parse_number(refund_amount.get('refund_shipping_fee', 0))
                refund_tax = shop._parse_number(refund_amount.get('refund_tax', 0))
                retail_delivery_fee = shop._parse_number(refund_amount.get('retail_delivery_fee', 0))
                buyer_service_fee = shop._parse_number(refund_amount.get('buyer_service_fee', 0))

                # Handle cancel reason
                cancel_reason_id = False
                if cancel_data.get('cancel_reason') and cancel_data.get('cancel_reason_text'):
                    reason_model = self.env['tiktok.cancel.reason']
                    cancel_reason = reason_model._upsert_reason(
                        cancel_data.get('cancel_reason'),
                        cancel_data.get('cancel_reason_text')
                    )
                    if cancel_reason:
                        cancel_reason_id = cancel_reason.id

                # Prepare values
                values = {
                    'cancel_id': cancel_id,
                    'tiktok_order_id': cancel_data.get('order_id'),
                    'cancel_type': cancel_data.get('cancel_type'),
                    'cancel_status': cancel_data.get('cancel_status'),
                    'role': cancel_data.get('role'),
                    'cancel_reason_id': cancel_reason_id,
                    'create_time': shop._convert_unix_to_datetime(cancel_data.get('create_time')),
                    'update_time': shop._convert_unix_to_datetime(cancel_data.get('update_time')),
                    'seller_next_action': seller_next_action,
                    'seller_action_deadline': seller_action_deadline,
                    'refund_currency': refund_currency,
                    'refund_total': refund_total,
                    'refund_subtotal': refund_subtotal,
                    'refund_shipping_fee': refund_shipping_fee,
                    'refund_tax': refund_tax,
                    'retail_delivery_fee': retail_delivery_fee,
                    'buyer_service_fee': buyer_service_fee,
                    'shop_id': shop.id,
                    'raw_payload': cancel_data,
                }

                # Find related order
                if cancel_data.get('order_id'):
                    order = self.env['tiktok.order'].search([
                        ('tiktok_id', '=', cancel_data.get('order_id')),
                        ('shop_id', '=', shop.id)
                    ], limit=1)
                    if order:
                        values['order_id'] = order.id

                # Upsert cancellation using helper method
                cancel_record = self.env['tiktok.shop']._upsert(
                    'tiktok.cancel',
                    [('cancel_id', '=', cancel_id), ('shop_id', '=', shop.id)],
                    values
                )

                # Sync cancel lines for this cancellation
                cancel_line_items = cancel_data.get('cancel_line_items', [])
                if cancel_line_items:
                    line_model = self.env['tiktok.cancel.line']
                    for line_data in cancel_line_items:
                        line_model._upsert_cancel_line(line_data, cancel_record.id)

                total_synced += 1

            # Check pagination
            page_token = data.get("next_page_token")
            if not page_token:
                break

            page_number += 1

        if total_synced == 0:
            _logger.warning(f"Shop {shop.name}: No cancellations found")
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
                        'message': _('No cancellations found!'),
                        'type': 'warning',
                    }
                }

        _logger.info(f"Shop {shop.name}: Successfully synced {total_synced} cancellations across {page_number} pages")

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
                    'message': _('Synced %d cancellations successfully!') % total_synced,
                    'type': 'success',
                }
            }


class TiktokShop(models.Model):
    _inherit = "tiktok.shop"

    def action_sync_cancellations(self):
        """
        Đồng bộ Cancellations từ TikTok Shop API.
        - Single shop: chạy trực tiếp
        - Multiple shops: chạy đa luồng
        """
        if len(self) == 1:
            # Single shop - chạy trực tiếp
            return self.env["tiktok.cancel"]._sync_cancellations(self)
        else:
            # Multiple shops - chạy đa luồng
            return self._run_multi_thread_tasks(
                self,
                "Sync Cancellations",
                self.env["tiktok.cancel"]._sync_cancellations,
                max_workers=min(len(self), MAX_CONCURRENT_THREADS)
            )
