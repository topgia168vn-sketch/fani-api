import logging
from datetime import datetime
from odoo import api, models, fields, _
from .tiktok_shop import MAX_CONCURRENT_THREADS

_logger = logging.getLogger(__name__)


class TiktokReturn(models.Model):
    _name = "tiktok.return"
    _description = "TikTok Shop Returns"
    _order = "create_time desc"
    _rec_name = "return_id"

    # ===== Basic Information =====
    return_id = fields.Char(string="Return ID", required=True, index=True)
    order_id = fields.Many2one("tiktok.order", string="Original Order", ondelete="set null")
    tiktok_order_id = fields.Char(string="TikTok Order ID", help="Original order ID from TikTok")

    # ===== Return Type & Status =====
    return_type = fields.Selection([
        ("REFUND", "Refund Only"),
        ("RETURN_AND_REFUND", "Return and Refund"),
        ("REPLACEMENT", "Replacement")
    ], string="Return Type")

    return_status = fields.Selection([
        ("RETURN_OR_REFUND_REQUEST_PENDING", "Request Pending"),
        ("REFUND_OR_RETURN_REQUEST_REJECT", "Request Rejected"),
        ("AWAITING_BUYER_SHIP", "Awaiting Buyer Ship"),
        ("BUYER_SHIPPED_ITEM", "Buyer Shipped Item"),
        ("REJECT_RECEIVE_PACKAGE", "Reject Receive Package"),
        ("RETURN_OR_REFUND_REQUEST_SUCCESS", "Request Success"),
        ("RETURN_OR_REFUND_REQUEST_CANCEL", "Request Cancelled"),
        ("RETURN_OR_REFUND_REQUEST_COMPLETE", "Request Complete"),
        ("REPLACEMENT_REQUEST_PENDING", "Replacement Pending"),
        ("REPLACEMENT_REQUEST_REJECT", "Replacement Rejected"),
        ("REPLACEMENT_REQUEST_REFUND_SUCCESS", "Replacement Refund Success"),
        ("REPLACEMENT_REQUEST_CANCEL", "Replacement Cancelled"),
        ("REPLACEMENT_REQUEST_COMPLETE", "Replacement Complete"),
        ("AWAITING_BUYER_RESPONSE", "Awaiting Buyer Response")
    ], string="Return Status")

    arbitration_status = fields.Selection([
        ("IN_PROGRESS", "In Progress"),
        ("SUPPORT_BUYER", "Support Buyer"),
        ("SUPPORT_SELLER", "Support Seller"),
        ("CLOSED", "Closed")
    ], string="Arbitration Status")

    # ===== Return Details =====
    role = fields.Selection([
        ("BUYER", "Buyer"),
        ("SELLER", "Seller"),
        ("OPERATOR", "Operator"),
        ("SYSTEM", "System")
    ], string="Initiator Role")

    return_reason_id = fields.Many2one("tiktok.return.reason", string="Return Reason", ondelete="set null")

    # ===== Shipping Information =====
    shipment_type = fields.Selection([
        ("PLATFORM", "Platform Shipping"),
        ("BUYER_ARRANGE", "Buyer Arrange")
    ], string="Shipment Type")

    handover_method = fields.Selection([
        ("DROP_OFF", "Drop Off"),
        ("PICKUP", "Pick Up")
    ], string="Handover Method")

    return_tracking_number = fields.Char(string="Return Tracking Number")
    return_provider_name = fields.Char(string="Return Provider Name")
    return_provider_id = fields.Char(string="Return Provider ID")
    return_shipping_document_type = fields.Selection([
        ("SHIPPING_LABEL", "Shipping Label"),
        ("QR_CODE", "QR Code")
    ], string="Return Shipping Document Type")

    return_method = fields.Selection([
        ("SELLER_SHIPPED", "Seller Shipped"),
        ("BUYER_SHIPPED", "Buyer Shipped"),
        ("PLATFORM_SHIPPED", "Platform Shipped")
    ], string="Return Method")

    # ===== Timeline =====
    create_time = fields.Datetime(string="Create Time", index=True)
    update_time = fields.Datetime(string="Update Time", index=True)

    # ===== Seller Actions =====
    seller_next_action = fields.Char(string="Seller Next Action")
    seller_action_deadline = fields.Datetime(string="Seller Action Deadline")

    # ===== Special Flags =====
    can_buyer_keep_item = fields.Boolean(string="Can Buyer Keep Item")
    is_combined_return = fields.Boolean(string="Is Combined Return")
    combined_return_id = fields.Char(string="Combined Return ID")

    # ===== Seller Proposals =====
    seller_proposed_return_type = fields.Selection([
        ("PARTIAL_REFUND", "Partial Refund")
    ], string="Seller Proposed Return Type")

    partial_refund_currency = fields.Char(string="Partial Refund Currency")
    partial_refund_amount = fields.Float(string="Partial Refund Amount", digits="Product Price")
    buyer_rejected_partial_refund = fields.Boolean(string="Buyer Rejected Partial Refund")

    # ===== Return Warehouse =====
    return_warehouse_address = fields.Text(string="Return Warehouse Address")

    # ===== Financial Information =====
    refund_currency = fields.Char(string="Refund Currency")
    refund_total = fields.Float(string="Refund Total", digits="Product Price")
    refund_subtotal = fields.Float(string="Refund Subtotal", digits="Product Price")
    refund_shipping_fee = fields.Float(string="Refund Shipping Fee", digits="Product Price")
    refund_tax = fields.Float(string="Refund Tax", digits="Product Price")
    retail_delivery_fee = fields.Float(string="Retail Delivery Fee", digits="Product Price")
    buyer_service_fee = fields.Float(string="Buyer Service Fee", digits="Product Price")

    # ===== Relationships =====
    line_ids = fields.One2many("tiktok.return.line", "return_id", string="Return Lines")
    shop_id = fields.Many2one("tiktok.shop", string="TikTok Shop", required=True, index=True, ondelete="cascade")

    # ===== Raw Data =====
    raw_payload = fields.Json(string="Raw Payload")

    _sql_constraints = [
        ('unique_return_id_per_shop', 'unique(return_id, shop_id)', 'Return ID must be unique per shop!'),
    ]

    @api.model
    def _get_smart_updated_since(self, shop):
        """
        Lấy updated_since thông minh cho shop (updated_since hoặc sync_data_since).
        """
        shop.ensure_one()
        sync_data_since = shop.sync_data_since

        # Tìm max update_time của returns trong shop này
        updated_since = self.env['tiktok.return'].search([
            ('shop_id', '=', shop.id)
        ], order='update_time desc', limit=1).update_time

        if updated_since:
            last_cron_start = self.env['tiktok.shop']._get_last_cron_start('tiktok_shop_connector.ir_cron_sync_tiktok_all_data')
            if last_cron_start:
                updated_since = min(updated_since, last_cron_start)
            if sync_data_since:
                updated_since = max(updated_since, sync_data_since)
            _logger.info(f"Shop {shop.name}: Incremental return sync since {updated_since.strftime('%Y-%m-%d %H:%M:%S')}")

        else:
            if sync_data_since:
                updated_since = sync_data_since
                _logger.info(f"Shop {shop.name}: Full return sync since {updated_since.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                updated_since = None
                _logger.info(f"Shop {shop.name}: Full return sync")

        return updated_since

    @api.model
    def _sync_returns(self, shop, updated_since=None, page_size=50, max_page=None):
        """
        Sync returns từ TikTok Shop API.
        """
        shop.ensure_one()
        sync_from_cron = self.env.context.get('sync_from_cron', False)

        _logger.info(f"Shop {shop.name}: Starting return sync")

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
            # Gọi API Search Returns
            params = {
                'shop_cipher': shop.shop_cipher,
                'page_size': page_size,
                'sort_field': 'update_time',
                'sort_order': 'ASC',
            }
            if page_token:
                params['page_token'] = page_token

            data = shop._request("POST", "/return_refund/202309/returns/search", params=params, json_body=json_body)
            returns = data.get("return_orders", [])

            if not returns:
                page_token = None
                break

            _logger.info(f"Shop {shop.name}: Processing page {page_number}, got {len(returns)} returns")

            # Process từng return
            for return_data in returns:
                return_id = return_data.get('return_id')
                if not return_id:
                    continue

                # Extract seller next action
                seller_actions = return_data.get('seller_next_action_response', [])
                seller_next_action = None
                seller_action_deadline = None
                if seller_actions:
                    action_data = seller_actions[0]
                    seller_next_action = action_data.get('action')
                    deadline_timestamp = action_data.get('deadline')
                    if deadline_timestamp:
                        seller_action_deadline = shop._convert_unix_to_datetime(deadline_timestamp)

                # Extract partial refund info
                partial_refund = return_data.get('partial_refund', {})
                partial_refund_currency = partial_refund.get('currency')
                partial_refund_amount = shop._parse_number(partial_refund.get('amount', 0))

                # Extract refund amount
                refund_amount = return_data.get('refund_amount', {})
                refund_currency = refund_amount.get('currency')
                refund_total = shop._parse_number(refund_amount.get('refund_total', 0))
                refund_subtotal = shop._parse_number(refund_amount.get('refund_subtotal', 0))
                refund_shipping_fee = shop._parse_number(refund_amount.get('refund_shipping_fee', 0))
                refund_tax = shop._parse_number(refund_amount.get('refund_tax', 0))
                retail_delivery_fee = shop._parse_number(refund_amount.get('retail_delivery_fee', 0))
                buyer_service_fee = shop._parse_number(refund_amount.get('buyer_service_fee', 0))

                # Extract return warehouse address
                return_warehouse = return_data.get('return_warehouse_address', {})
                return_warehouse_address = return_warehouse.get('full_address')

                # Handle return reason
                return_reason_id = False
                if return_data.get('return_reason') and return_data.get('return_reason_text'):
                    reason_model = self.env['tiktok.return.reason']
                    return_reason = reason_model._upsert_reason(
                        return_data['return_reason'],
                        return_data['return_reason_text']
                    )
                    if return_reason:
                        return_reason_id = return_reason.id

                # Prepare values
                values = {
                    'return_id': return_id,
                    'tiktok_order_id': return_data.get('order_id'),
                    'return_type': return_data.get('return_type'),
                    'return_status': return_data.get('return_status'),
                    'arbitration_status': return_data.get('arbitration_status'),
                    'role': return_data.get('role'),
                    'return_reason_id': return_reason_id,
                    'shipment_type': return_data.get('shipment_type'),
                    'handover_method': return_data.get('handover_method'),
                    'return_tracking_number': return_data.get('return_tracking_number'),
                    'return_provider_name': return_data.get('return_provider_name'),
                    'return_provider_id': return_data.get('return_provider_id'),
                    'return_shipping_document_type': return_data.get('return_shipping_document_type'),
                    'return_method': return_data.get('return_method'),
                    'create_time': shop._convert_unix_to_datetime(return_data.get('create_time')),
                    'update_time': shop._convert_unix_to_datetime(return_data.get('update_time')),
                    'seller_next_action': seller_next_action,
                    'seller_action_deadline': seller_action_deadline,
                    'can_buyer_keep_item': return_data.get('can_buyer_keep_item', False),
                    'is_combined_return': return_data.get('is_combined_return', False),
                    'combined_return_id': return_data.get('combined_return_id'),
                    'seller_proposed_return_type': return_data.get('seller_proposed_return_type'),
                    'partial_refund_currency': partial_refund_currency,
                    'partial_refund_amount': partial_refund_amount,
                    'buyer_rejected_partial_refund': return_data.get('buyer_rejected_partial_refund', False),
                    'return_warehouse_address': return_warehouse_address,
                    'refund_currency': refund_currency,
                    'refund_total': refund_total,
                    'refund_subtotal': refund_subtotal,
                    'refund_shipping_fee': refund_shipping_fee,
                    'refund_tax': refund_tax,
                    'retail_delivery_fee': retail_delivery_fee,
                    'buyer_service_fee': buyer_service_fee,
                    'shop_id': shop.id,
                    'raw_payload': return_data,
                }

                # Find related order
                if return_data.get('order_id'):
                    order = self.env['tiktok.order'].search([
                        ('tiktok_id', '=', return_data.get('order_id')),
                        ('shop_id', '=', shop.id)
                    ], limit=1)
                    if order:
                        values['order_id'] = order.id

                # Upsert return using helper method
                return_record = self.env['tiktok.shop']._upsert(
                    'tiktok.return',
                    [('return_id', '=', return_id), ('shop_id', '=', shop.id)],
                    values
                )

                # Sync return lines for this return
                return_line_items = return_data.get('return_line_items', [])
                if return_line_items:
                    line_model = self.env['tiktok.return.line']
                    for line_data in return_line_items:
                        line_model._upsert_return_line(line_data, return_record.id)

                total_synced += 1

            # Check pagination
            page_token = data.get("next_page_token")
            if not page_token:
                break

            page_number += 1

        if total_synced == 0:
            _logger.warning(f"Shop {shop.name}: No returns found")
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
                        'message': _('No returns found!'),
                        'type': 'warning',
                    }
                }

        _logger.info(f"Shop {shop.name}: Successfully synced {total_synced} returns across {page_number} pages")

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
                    'message': _('Synced %d returns successfully!') % total_synced,
                    'type': 'success',
                }
            }


class TiktokShop(models.Model):
    _inherit = "tiktok.shop"

    def action_sync_returns(self):
        """
        Đồng bộ Returns từ TikTok Shop API.
        - Single shop: chạy trực tiếp
        - Multiple shops: chạy đa luồng
        """
        if len(self) == 1:
            # Single shop - chạy trực tiếp
            return self.env["tiktok.return"]._sync_returns(self)
        else:
            # Multiple shops - chạy đa luồng
            return self._run_multi_thread_tasks(
                self,
                "Sync Returns",
                self.env["tiktok.return"]._sync_returns,
                max_workers=min(len(self), MAX_CONCURRENT_THREADS)
            )
