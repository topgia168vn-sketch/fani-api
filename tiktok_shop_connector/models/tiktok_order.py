import logging
from datetime import datetime
from odoo import api, models, fields, _
from .tiktok_shop import MAX_CONCURRENT_THREADS

_logger = logging.getLogger(__name__)


class TiktokOrder(models.Model):
    _name = "tiktok.order"
    _description = "TikTok Shop Orders"
    _order = "create_time desc"
    _rec_name = "tiktok_id"

    # ===== Basic Information =====
    tiktok_id = fields.Char(string="TikTok Order ID", required=True, index=True)
    states = fields.Selection([
        ('UNPAID', 'Unpaid'),
        ('ON_HOLD', 'On Hold'),
        ('AWAITING_SHIPMENT', 'Awaiting Shipment'),
        ('PARTIALLY_SHIPPING', 'Partially Shipping'),
        ('AWAITING_COLLECTION', 'Awaiting Collection'),
        ('IN_TRANSIT', 'In Transit'),
        ('DELIVERED', 'Delivered'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ], string="Order Status")
    create_time = fields.Datetime(string="Create Time", index=True)
    update_time = fields.Datetime(string="Update Time", index=True)

    # ===== Customer Information =====
    user_id = fields.Char(string="Buyer UID")
    buyer_message = fields.Text(string="Buyer Message")
    buyer_email = fields.Char(string="Buyer Email")
    buyer_info = fields.Json(string="Buyer Information")

    # ===== Recipient Information =====
    recipient_name = fields.Char(string="Recipient Name")
    recipient_first_name = fields.Char(string="Recipient First Name")
    recipient_last_name = fields.Char(string="Recipient Last Name")
    recipient_first_name_local_script = fields.Char(string="Recipient First Name (Local Script)")
    recipient_last_name_local_script = fields.Char(string="Recipient Last Name (Local Script)")
    recipient_phone = fields.Char(string="Recipient Phone")
    recipient_region_code = fields.Char(string="Recipient Region Code")
    recipient_postal_code = fields.Char(string="Recipient Postal Code")
    recipient_post_town = fields.Char(string="Recipient Post Town")
    recipient_address_line1 = fields.Char(string="Recipient Address Line 1")
    recipient_address_line2 = fields.Char(string="Recipient Address Line 2")
    recipient_address_line3 = fields.Char(string="Recipient Address Line 3")
    recipient_address_line4 = fields.Char(string="Recipient Address Line 4")
    recipient_district_info = fields.Json(string="Recipient District Info")
    recipient_delivery_preferences = fields.Json(string="Recipient Delivery Preferences")

    # ===== Payment Information =====
    payment_info = fields.Json(string="Payment Information")
    payment_method_name = fields.Char(string="Payment Method Name")
    payment_method_code = fields.Char(string="Payment Method Code")
    payment_card_type = fields.Selection([
        ('Debit', 'Debit'),
        ('Credit', 'Credit'),
        ('Prepaid', 'Prepaid'),
        ('Unknown', 'Unknown'),
    ], string="Payment Card Type")
    payment_auth_code = fields.Char(string="Payment Auth Code")
    is_cod = fields.Boolean(string="Is COD")

    # ===== Payment Amounts =====
    payment_currency = fields.Char(string="Payment Currency")
    payment_sub_total = fields.Float(string="Payment Sub Total", digits="Product Price")
    payment_shipping_fee = fields.Float(string="Payment Shipping Fee", digits="Product Price")
    payment_seller_discount = fields.Float(string="Payment Seller Discount", digits="Product Price")
    payment_platform_discount = fields.Float(string="Payment Platform Discount", digits="Product Price")
    payment_total_amount = fields.Float(string="Payment Total Amount", digits="Product Price")
    payment_original_total_product_price = fields.Float(string="Payment Original Total Product Price", digits="Product Price")
    payment_original_shipping_fee = fields.Float(string="Payment Original Shipping Fee", digits="Product Price")
    payment_shipping_fee_seller_discount = fields.Float(string="Payment Shipping Fee Seller Discount", digits="Product Price")
    payment_shipping_fee_platform_discount = fields.Float(string="Payment Shipping Fee Platform Discount", digits="Product Price")
    payment_shipping_fee_co_funded_discount = fields.Float(string="Payment Shipping Fee Co-funded Discount", digits="Product Price")
    payment_tax = fields.Float(string="Payment Tax", digits="Product Price")
    payment_small_order_fee = fields.Float(string="Payment Small Order Fee", digits="Product Price")
    payment_shipping_fee_tax = fields.Float(string="Payment Shipping Fee Tax", digits="Product Price")
    payment_product_tax = fields.Float(string="Payment Product Tax", digits="Product Price")
    payment_retail_delivery_fee = fields.Float(string="Payment Retail Delivery Fee", digits="Product Price")
    payment_buyer_service_fee = fields.Float(string="Payment Buyer Service Fee", digits="Product Price")
    payment_handling_fee = fields.Float(string="Payment Handling Fee", digits="Product Price")
    payment_shipping_insurance_fee = fields.Float(string="Payment Shipping Insurance Fee", digits="Product Price")
    payment_item_insurance_fee = fields.Float(string="Payment Item Insurance Fee", digits="Product Price")

    # ===== Shipping Information =====
    shipping_provider = fields.Char(string="Shipping Provider")
    shipping_provider_id = fields.Char(string="Shipping Provider ID")
    shipping_type = fields.Selection([
        ('TIKTOK', 'TikTok'),
        ('SELLER', 'Seller'),
    ], string="Shipping Type")
    tracking_number = fields.Char(string="Tracking Number")
    delivery_type = fields.Selection([
        ('HOME_DELIVERY', 'Home Delivery'),
        ('COLLECTION_POINT', 'Collection Point'),
    ], string="Delivery Type")
    delivery_option_id = fields.Char(string="Delivery Option ID")
    delivery_option_name = fields.Char(string="Delivery Option Name")
    delivery_due_time = fields.Datetime(string="Delivery Due Time")
    delivery_time = fields.Datetime(string="Delivery Time")
    shipping_due_time = fields.Datetime(string="Shipping Due Time")
    recipient_address = fields.Json(string="Recipient Address")

    # ===== Order Items =====
    item_list = fields.Json(string="Order Items (Raw Data)")
    line_ids = fields.One2many("tiktok.order.line", "order_id", string="Order Lines")

    # ===== Fulfillment Information =====
    fulfillment_type = fields.Selection([
        ('FULFILLMENT_BY_SELLER', 'Fulfillment by Seller'),
        ('FULFILLMENT_BY_TIKTOK', 'Fulfillment by TikTok'),
        ('FULFILLMENT_BY_DILAYANI_TOKOPEDIA', 'Fulfillment by Dilayani Tokopedia'),
    ], string="Fulfillment Type")
    warehouse_id = fields.Char(string="Warehouse ID")
    packages = fields.Json(string="Packages")
    is_sample_order = fields.Boolean(string="Is Sample Order")
    split_or_combine_tag = fields.Selection([
        ('combined', 'Combined'),
        ('split', 'Split'),
    ], string="Split or Combine Tag")
    has_updated_recipient_address = fields.Boolean(string="Has Updated Recipient Address")

    # ===== Logistics Information =====
    rts_time = fields.Datetime(string="RTS Time")
    rts_sla_time = fields.Datetime(string="RTS SLA Time")
    tts_sla_time = fields.Datetime(string="TTS SLA Time")
    paid_time = fields.Datetime(string="Paid Time")
    collection_time = fields.Datetime(string="Collection Time")
    collection_due_time = fields.Datetime(string="Collection Due Time")
    pick_up_cut_off_time = fields.Datetime(string="Pick Up Cut Off Time")
    fast_dispatch_sla_time = fields.Datetime(string="Fast Dispatch SLA Time")
    delivery_sla_time = fields.Datetime(string="Delivery SLA Time")
    delivery_option_required_delivery_time = fields.Datetime(string="Delivery Option Required Delivery Time")

    # ===== Order Lifecycle =====
    cancellation_initiator = fields.Selection([
        ('SELLER', 'Seller'),
        ('BUYER', 'Buyer'),
        ('SYSTEM', 'System'),
    ], string="Cancellation Initiator")
    cancel_reason = fields.Char(string="Cancel Reason")
    cancel_time = fields.Datetime(string="Cancel Time")
    request_cancel_time = fields.Datetime(string="Request Cancel Time")
    cancel_order_sla_time = fields.Datetime(string="Cancel Order SLA Time")
    is_buyer_request_cancel = fields.Boolean(string="Is Buyer Request Cancel")
    is_on_hold_order = fields.Boolean(string="Is On Hold Order")
    is_replacement_order = fields.Boolean(string="Is Replacement Order")
    replaced_order_id = fields.Char(string="Replaced Order ID")
    is_exchange_order = fields.Boolean(string="Is Exchange Order")
    exchange_source_order_id = fields.Char(string="Exchange Source Order ID")

    # ===== Additional Information =====
    seller_note = fields.Text(string="Seller Note")
    order_type = fields.Selection([
        ('NORMAL', 'Normal'),
        ('ZERO_LOTTERY', 'Zero Lottery'),
        ('PRE_ORDER', 'Pre Order'),
        ('MADE_TO_ORDER', 'Made to Order'),
        ('BACK_ORDER', 'Back Order'),
        ('SELLER_FUND_FREE_SAMPLE', 'Seller Fund Free Sample'),
    ], string="Order Type")
    ecommerce_platform = fields.Selection([
        ('TIKTOK_SHOP', 'TikTok Shop'),
        ('TOKOPEDIA', 'Tokopedia'),
    ], string="Ecommerce Platform")
    release_date = fields.Datetime(string="Release Date")
    handling_duration = fields.Json(string="Handling Duration")
    auto_combine_group_id = fields.Char(string="Auto Combine Group ID")
    cpf = fields.Char(string="CPF")
    cpf_name = fields.Char(string="CPF Name")
    consultation_id = fields.Char(string="Consultation ID")
    channel_entity_national_registry_id = fields.Char(string="Channel Entity National Registry ID")
    need_upload_invoice = fields.Selection([
        ('UNKNOWN', 'Unknown'),
        ('NEED_INVOICE', 'Need Invoice'),
        ('NO_NEED', 'No Need'),
        ('INVOICE_UPLOADED', 'Invoice Uploaded'),
    ], string="Need Upload Invoice")
    fast_delivery_program = fields.Selection([
        ('3_DAY_DELIVERY', '3 Day Delivery'),
    ], string="Fast Delivery Program")

    # ===== Shop Reference =====
    shop_id = fields.Many2one("tiktok.shop", string="TikTok Shop", required=True, index=True, ondelete="cascade")

    # ===== Raw Data =====
    raw_payload = fields.Json()

    _sql_constraints = [
        ('unique_tiktok_id_per_shop', 'unique(tiktok_id, shop_id)',
         'TikTok Order ID must be unique per shop!'),
    ]

    @api.model
    def _get_smart_updated_since(self, shop):
        """
        Lấy updated_since thông minh cho shop (updated_since hoặc sync_data_since).
        """
        shop.ensure_one()
        sync_data_since = shop.sync_data_since

        # Tìm max update_time của orders trong shop này
        updated_since = self.env['tiktok.order'].search([
            ('shop_id', '=', shop.id)
        ], order='update_time desc', limit=1).update_time

        if updated_since:
            last_cron_start = self.env['tiktok.shop']._get_last_cron_start('tiktok_shop_connector.ir_cron_sync_tiktok_all_data')
            if last_cron_start:
                updated_since = min(updated_since, last_cron_start)
            if sync_data_since:
                updated_since = max(updated_since, sync_data_since)
            _logger.info(f"Shop {shop.name}: Incremental order sync since {updated_since.strftime('%Y-%m-%d %H:%M:%S')}")

        else:
            if sync_data_since:
                updated_since = sync_data_since
                _logger.info(f"Shop {shop.name}: Full order sync since {updated_since.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                updated_since = None
                _logger.info(f"Shop {shop.name}: Full order sync")

        return updated_since

    @api.model
    def _sync_orders(self, shop, updated_since=None, page_size=100, max_page=None):
        """
        Sync orders từ TikTok Shop API.
        Process từng page để tiết kiệm memory.
        """
        shop.ensure_one()
        sync_from_cron = self.env.context.get('sync_from_cron', False)

        _logger.info(f"Shop {shop.name}: Starting order sync")

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
            # Gọi API Get Order List
            params = {
                'shop_cipher': shop.shop_cipher,
                'page_size': page_size,
                'sort_order': 'ASC',
                'sort_field': 'update_time'
            }
            if page_token:
                params['page_token'] = page_token

            data = shop._request("POST", "/order/202309/orders/search", params=params, json_body=json_body)
            orders = data.get("orders", [])

            if not orders:
                page_token = None
                break

            _logger.info(f"Shop {shop.name}: Processing page {page_number}, got {len(orders)} orders")

            # Process orders trong page này theo batch (max 50 orders per call)
            order_ids = [order['id'] for order in orders if order.get('id')]
            batch_size = 50
            page_synced = 0

            for i in range(0, len(order_ids), batch_size):
                batch_ids = order_ids[i:i + batch_size]

                # Gọi API Get Order Details theo batch
                detail_params = {
                    'shop_cipher': shop.shop_cipher,
                    'ids': ','.join(batch_ids)
                }

                batch_response = shop._request("GET", "/order/202507/orders", params=detail_params)
                batch_orders = batch_response.get('orders', [])

                if not batch_orders:
                    _logger.warning(f"Shop {shop.name}: No order details returned for batch {i//batch_size + 1}")
                    continue

                # Process từng order trong batch
                for order_data in batch_orders:
                    order_id = order_data.get('id')
                    if not order_id:
                        continue

                    # Extract payment information
                    payment_data = order_data.get('payment', {})

                    # Extract recipient address information
                    recipient_address = order_data.get('recipient_address', {})

                    # Prepare values từ Get Order Details response
                    values = {
                        # Basic Information
                        'tiktok_id': order_data.get('id'),
                        'states': order_data.get('states'),
                        'create_time': shop._convert_unix_to_datetime(order_data.get('create_time')),
                        'update_time': shop._convert_unix_to_datetime(order_data.get('update_time')),

                        # Customer Information
                        'user_id': order_data.get('user_id'),
                        'buyer_message': order_data.get('buyer_message'),
                        'buyer_email': order_data.get('buyer_email'),
                        'buyer_info': {
                            'cpf': order_data.get('cpf'),
                            'cpf_name': order_data.get('cpf_name'),
                        },

                        # Recipient Information
                        'recipient_name': recipient_address.get('name'),
                        'recipient_first_name': recipient_address.get('first_name'),
                        'recipient_last_name': recipient_address.get('last_name'),
                        'recipient_first_name_local_script': recipient_address.get('first_name_local_script'),
                        'recipient_last_name_local_script': recipient_address.get('last_name_local_script'),
                        'recipient_phone': recipient_address.get('phone_number'),
                        'recipient_region_code': recipient_address.get('region_code'),
                        'recipient_postal_code': recipient_address.get('postal_code'),
                        'recipient_post_town': recipient_address.get('post_town'),
                        'recipient_address_line1': recipient_address.get('address_line1'),
                        'recipient_address_line2': recipient_address.get('address_line2'),
                        'recipient_address_line3': recipient_address.get('address_line3'),
                        'recipient_address_line4': recipient_address.get('address_line4'),
                        'recipient_district_info': recipient_address.get('district_info', []),
                        'recipient_delivery_preferences': recipient_address.get('delivery_preferences', {}),

                        # Payment Information
                        'payment_info': payment_data,
                        'payment_method_name': order_data.get('payment_method_name'),
                        'payment_method_code': order_data.get('payment_method_code'),
                        'payment_card_type': order_data.get('payment_card_type'),
                        'payment_auth_code': order_data.get('payment_auth_code'),
                        'is_cod': order_data.get('is_cod', False),

                        # Payment Amounts
                        'payment_currency': payment_data.get('currency'),
                        'payment_sub_total': shop._parse_number(payment_data.get('sub_total', 0)),
                        'payment_shipping_fee': shop._parse_number(payment_data.get('shipping_fee', 0)),
                        'payment_seller_discount': shop._parse_number(payment_data.get('seller_discount', 0)),
                        'payment_platform_discount': shop._parse_number(payment_data.get('platform_discount', 0)),
                        'payment_total_amount': shop._parse_number(payment_data.get('total_amount', 0)),
                        'payment_original_total_product_price': shop._parse_number(payment_data.get('original_total_product_price', 0)),
                        'payment_original_shipping_fee': shop._parse_number(payment_data.get('original_shipping_fee', 0)),
                        'payment_shipping_fee_seller_discount': shop._parse_number(payment_data.get('shipping_fee_seller_discount', 0)),
                        'payment_shipping_fee_platform_discount': shop._parse_number(payment_data.get('shipping_fee_platform_discount', 0)),
                        'payment_shipping_fee_co_funded_discount': shop._parse_number(payment_data.get('shipping_fee_co_funded_discount', 0)),
                        'payment_tax': shop._parse_number(payment_data.get('tax', 0)),
                        'payment_small_order_fee': shop._parse_number(payment_data.get('small_order_fee', 0)),
                        'payment_shipping_fee_tax': shop._parse_number(payment_data.get('shipping_fee_tax', 0)),
                        'payment_product_tax': shop._parse_number(payment_data.get('product_tax', 0)),
                        'payment_retail_delivery_fee': shop._parse_number(payment_data.get('retail_delivery_fee', 0)),
                        'payment_buyer_service_fee': shop._parse_number(payment_data.get('buyer_service_fee', 0)),
                        'payment_handling_fee': shop._parse_number(payment_data.get('handling_fee', 0)),
                        'payment_shipping_insurance_fee': shop._parse_number(payment_data.get('shipping_insurance_fee', 0)),
                        'payment_item_insurance_fee': shop._parse_number(payment_data.get('item_insurance_fee', 0)),

                        # Shipping Information
                        'shipping_provider': order_data.get('shipping_provider'),
                        'shipping_provider_id': order_data.get('shipping_provider_id'),
                        'shipping_type': order_data.get('shipping_type'),
                        'tracking_number': order_data.get('tracking_number'),
                        'delivery_type': order_data.get('delivery_type'),
                        'delivery_option_id': order_data.get('delivery_option_id'),
                        'delivery_option_name': order_data.get('delivery_option_name'),
                        'delivery_due_time': shop._convert_unix_to_datetime(order_data.get('delivery_due_time')),
                        'delivery_time': shop._convert_unix_to_datetime(order_data.get('delivery_time')),
                        'shipping_due_time': shop._convert_unix_to_datetime(order_data.get('shipping_due_time')),
                        'recipient_address': order_data.get('recipient_address', {}),

                        # Order Items
                        'item_list': order_data.get('line_items', []),

                        # Fulfillment Information
                        'fulfillment_type': order_data.get('fulfillment_type'),
                        'warehouse_id': order_data.get('warehouse_id'),
                        'packages': order_data.get('packages', []),
                        'is_sample_order': order_data.get('is_sample_order', False),
                        'split_or_combine_tag': order_data.get('split_or_combine_tag'),
                        'has_updated_recipient_address': order_data.get('has_updated_recipient_address', False),

                        # Logistics Information
                        'rts_time': shop._convert_unix_to_datetime(order_data.get('rts_time')),
                        'rts_sla_time': shop._convert_unix_to_datetime(order_data.get('rts_sla_time')),
                        'tts_sla_time': shop._convert_unix_to_datetime(order_data.get('tts_sla_time')),
                        'paid_time': shop._convert_unix_to_datetime(order_data.get('paid_time')),
                        'collection_time': shop._convert_unix_to_datetime(order_data.get('collection_time')),
                        'collection_due_time': shop._convert_unix_to_datetime(order_data.get('collection_due_time')),
                        'pick_up_cut_off_time': shop._convert_unix_to_datetime(order_data.get('pick_up_cut_off_time')),
                        'fast_dispatch_sla_time': shop._convert_unix_to_datetime(order_data.get('fast_dispatch_sla_time')),
                        'delivery_sla_time': shop._convert_unix_to_datetime(order_data.get('delivery_sla_time')),
                        'delivery_option_required_delivery_time': shop._convert_unix_to_datetime(order_data.get('delivery_option_required_delivery_time')),
                        'fast_delivery_program': order_data.get('fast_delivery_program'),

                        # Order Lifecycle
                        'cancellation_initiator': order_data.get('cancellation_initiator'),
                        'cancel_reason': order_data.get('cancel_reason'),
                        'cancel_time': shop._convert_unix_to_datetime(order_data.get('cancel_time')),
                        'request_cancel_time': shop._convert_unix_to_datetime(order_data.get('request_cancel_time')),
                        'cancel_order_sla_time': shop._convert_unix_to_datetime(order_data.get('cancel_order_sla_time')),
                        'is_buyer_request_cancel': order_data.get('is_buyer_request_cancel', False),
                        'is_on_hold_order': order_data.get('is_on_hold_order', False),
                        'is_replacement_order': order_data.get('is_replacement_order', False),
                        'replaced_order_id': order_data.get('replaced_order_id'),
                        'is_exchange_order': order_data.get('is_exchange_order', False),
                        'exchange_source_order_id': order_data.get('exchange_source_order_id'),

                        # Additional Information
                        'seller_note': order_data.get('seller_note'),
                        'order_type': order_data.get('order_type'),
                        'ecommerce_platform': order_data.get('ecommerce_platform'),
                        'release_date': shop._convert_unix_to_datetime(order_data.get('release_date')),
                        'handling_duration': order_data.get('handling_duration', {}),
                        'auto_combine_group_id': order_data.get('auto_combine_group_id'),
                        'cpf': order_data.get('cpf'),
                        'cpf_name': order_data.get('cpf_name'),
                        'consultation_id': order_data.get('consultation_id'),
                        'channel_entity_national_registry_id': order_data.get('channel_entity_national_registry_id'),
                        'need_upload_invoice': order_data.get('need_upload_invoice'),

                        # Shop Reference
                        'shop_id': shop.id,

                        # Raw Data
                        'raw_payload': order_data,  # Store complete order data
                    }

                    # Upsert order using helper method
                    order = self.env['tiktok.shop']._upsert(
                        'tiktok.order',
                        [('tiktok_id', '=', order_id), ('shop_id', '=', shop.id)],
                        values
                    )

                    # Sync order lines for this order
                    line_items_data = order_data.get('line_items', [])
                    if line_items_data:
                        line_model = self.env['tiktok.order.line']
                        for line_data in line_items_data:
                            line_model._upsert_line_item(line_data, order.id)

                    page_synced += 1
                    total_synced += 1

            # Check pagination
            page_token = data.get("next_page_token")
            if not page_token:
                break

            page_number += 1

        if total_synced == 0:
            _logger.warning(f"Shop {shop.name}: No orders found")
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
                        'message': _('No orders found!'),
                        'type': 'warning',
                    }
                }

        _logger.info(f"Shop {shop.name}: Successfully synced {total_synced} orders across {page_number} pages")

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
                    'message': _('Synced %d orders successfully!') % total_synced,
                    'type': 'success',
                }
            }


class TiktokShop(models.Model):
    _inherit = "tiktok.shop"

    def action_sync_orders(self):
        """
        Đồng bộ Orders từ TikTok Shop API.
        - Single shop: chạy trực tiếp
        - Multiple shops: chạy đa luồng
        """
        if len(self) == 1:
            # Single shop - chạy trực tiếp
            return self.env["tiktok.order"]._sync_orders(self)
        else:
            # Multiple shops - chạy đa luồng
            return self._run_multi_thread_tasks(
                self,
                "Sync Orders",
                self.env["tiktok.order"]._sync_orders,
                max_workers=min(len(self), MAX_CONCURRENT_THREADS)
            )
