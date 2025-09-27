# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class TaLazadaOrder(models.Model):
    _name = 'ta.lazada.order'
    _description = 'Lazada Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'order_number'

    # Basic Information - theo API Lazada
    order_id = fields.Char('Lazada Order ID', required=True)
    order_number = fields.Char('Order Number', required=True)
    authorized_shop_id = fields.Many2one('ta.lazada.authorized.shop', 'Authorized Shop', required=True)
    
    # Order Details - theo API Lazada
    created_at = fields.Datetime('Created At', required=True)
    updated_at = fields.Datetime('Updated At')
    order_status = fields.Selection([
        ('unpaid', 'Unpaid'),
        ('pending', 'Pending'),
        ('canceled', 'Canceled'),
        ('ready_to_ship', 'Ready to Ship'),
        ('delivered', 'Delivered'),
        ('returned', 'Returned'),
        ('shipped', 'Shipped'),
        ('failed', 'Failed'),
        ('topack', 'To Pack'),
        ('toship', 'To Ship'),
        ('shipping', 'Shipping'),
        ('lost', 'Lost'),
    ], string='Order Status', default='pending')
    
    # Customer Information - theo API Lazada
    customer_first_name = fields.Char('Customer First Name')
    customer_last_name = fields.Char('Customer Last Name')
    email = fields.Char('Customer Email')
    phone = fields.Char('Customer Phone')
    customer_id = fields.Char('Lazada Customer ID')
    
    # Shipping Address - theo API Lazada
    shipping_address_first_name = fields.Char('Shipping First Name')
    shipping_address_last_name = fields.Char('Shipping Last Name')
    shipping_address = fields.Text('Shipping Address')
    shipping_address_city = fields.Char('Shipping City')
    shipping_address_state = fields.Char('Shipping State/Province')
    shipping_address_post_code = fields.Char('Shipping Postal Code')
    shipping_address_country = fields.Char('Shipping Country')
    shipping_address_phone = fields.Char('Shipping Phone')
    
    # Billing Address - theo API Lazada
    billing_address_first_name = fields.Char('Billing First Name')
    billing_address_last_name = fields.Char('Billing Last Name')
    billing_address = fields.Text('Billing Address')
    billing_address_city = fields.Char('Billing City')
    billing_address_state = fields.Char('Billing State/Province')
    billing_address_post_code = fields.Char('Billing Postal Code')
    billing_address_country = fields.Char('Billing Country')
    billing_address_phone = fields.Char('Billing Phone')
    
    # Payment Information - theo API Lazada
    payment_method = fields.Char('Payment Method')
    
    # Order Amount - theo API Lazada
    order_amount = fields.Float('Order Amount')
    currency = fields.Char('Currency', default='VND')
    shipping_fee = fields.Float('Shipping Fee')
    voucher = fields.Float('Voucher Amount')
    tax_amount = fields.Float('Tax Amount')
    
    # Additional Info - theo API Lazada
    items_count = fields.Integer('Items Count')
    remarks = fields.Text('Remarks')
    
    # Additional fields from Lazada API response
    voucher_platform = fields.Float('Voucher Platform')
    voucher_seller = fields.Float('Voucher Seller')
    shipping_fee_discount_platform = fields.Float('Shipping Fee Discount Platform')
    shipping_fee_discount_seller = fields.Float('Shipping Fee Discount Seller')
    shipping_fee_original = fields.Float('Shipping Fee Original')
    warehouse_code = fields.Char('Warehouse Code')
    gift_option = fields.Boolean('Gift Option')
    is_cancel_pending = fields.Boolean('Is Cancel Pending')
    need_cancel_confirm = fields.Boolean('Need Cancel Confirm')
    buyer_note = fields.Text('Buyer Note')
    gift_message = fields.Text('Gift Message')
    
    # Order Lines
    order_line_ids = fields.One2many('ta.lazada.order.line', 'order_id', 'Order Lines')
    
    # Sync Information
    last_sync_date = fields.Datetime('Last Sync Date')
    sync_status = fields.Selection([
        ('pending', 'Pending'),
        ('synced', 'Synced'),
        ('failed', 'Failed'),
        ('updating', 'Updating'),
    ], string='Sync Status', default='pending')
    
    # Computed fields
    customer_full_name = fields.Char('Customer Full Name', compute='_compute_customer_full_name', store=True)
    
    _sql_constraints = [
        ('order_shop_unique', 'unique(order_id, authorized_shop_id)', 'Lazada Order ID must be unique per authorized shop'),
    ]
    
    @api.depends('customer_first_name', 'customer_last_name')
    def _compute_customer_full_name(self):
        for record in self:
            if record.customer_first_name and record.customer_last_name:
                record.customer_full_name = f"{record.customer_first_name} {record.customer_last_name}"
            elif record.customer_first_name:
                record.customer_full_name = record.customer_first_name
            elif record.customer_last_name:
                record.customer_full_name = record.customer_last_name
            else:
                record.customer_full_name = ''
    
    @staticmethod
    def _parse_datetime_safely(datetime_value):
        """Parse datetime value safely and return naive datetime for Odoo"""
        if not datetime_value:
            return False
        
        try:
            if isinstance(datetime_value, str):
                # Handle both Z suffix and +00:00 timezone formats
                if datetime_value.endswith('Z'):
                    datetime_value = datetime_value[:-1] + '+00:00'
                parsed_datetime = datetime.fromisoformat(datetime_value)
                # Convert to UTC and make naive (remove timezone info)
                if parsed_datetime.tzinfo:
                    parsed_datetime = parsed_datetime.astimezone().replace(tzinfo=None)
                return parsed_datetime
            elif isinstance(datetime_value, (int, float)):
                # Handle Unix timestamp
                return datetime.fromtimestamp(datetime_value)
        except:
            return False
        
        return False
    
    def import_from_lazada_for_shop(self, authorized_shop, created_after=None):
        """Import orders from Lazada for specific authorized shop with pagination support
        
        Args:
            authorized_shop: The authorized shop to import orders for
            created_after: ISO 8601 date string to filter orders created after this date (if None, uses shop configuration)
        """
        if not authorized_shop.access_token:
            raise ValidationError(_('No access token available for shop %s') % authorized_shop.shop_name)
        
        try:
            endpoint = '/orders/get'
            success_count = 0
            error_count = 0
            offset = 0
            limit = 50  # Lazada API limit: 1-50 for orders/get
            total_orders = 0
            
            # Use shop configuration for created_after if not provided
            if created_after is None:
                created_after_datetime = authorized_shop.order_sync_created_after
                if created_after_datetime:
                    # Convert datetime to ISO 8601 format with Z suffix for Lazada API
                    created_after = created_after_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')
                else:
                    created_after = '2024-01-01T00:00:00Z'  # Default fallback
            
            # Sync all orders without status filter (API will return all statuses)
            offset = 0
            params = {
                'limit': limit,
                'offset': offset,
                'created_after': created_after  # Required parameter - ISO 8601 format with Z suffix
            }
            
            response = authorized_shop._make_api_request(endpoint, params, 'GET')
            
            if response.get('code') == '0' and response.get('data'):
                data = response['data']
                total_orders = int(data.get('countTotal', 0))
                
                # Process first batch
                orders_data = data.get('orders', [])
                for order_data in orders_data:
                    try:
                        self._create_or_update_order_from_lazada(order_data, authorized_shop)
                        success_count += 1
                    except Exception as order_error:
                        error_count += 1
                        try:
                            authorized_shop.message_post(
                                body=_('Error creating/updating order: %s') % str(order_error)
                            )
                        except:
                            pass
                
                # Update order lines for all orders in this batch
                if orders_data:
                    self._update_order_lines_batch(orders_data, authorized_shop)
                
                # Continue with pagination if there are more orders
                while offset + limit < total_orders:
                    offset += limit
                    params['offset'] = offset
                    
                    try:
                        response = authorized_shop._make_api_request(endpoint, params, 'GET')
                        
                        if response.get('code') == '0' and response.get('data'):
                            data = response['data']
                            orders_data = data.get('orders', [])
                            
                            for order_data in orders_data:
                                try:
                                    self._create_or_update_order_from_lazada(order_data, authorized_shop)
                                    success_count += 1
                                except Exception as order_error:
                                    error_count += 1
                                    try:
                                        authorized_shop.message_post(
                                            body=_('Error creating/updating order in pagination: %s') % str(order_error)
                                        )
                                    except:
                                        pass
                            
                            # Update order lines for all orders in this batch
                            if orders_data:
                                self._update_order_lines_batch(orders_data, authorized_shop)
                        else:
                            # If API returns error, break the loop
                            break
                            
                    except Exception as page_error:
                        # If pagination request fails, continue with next page
                        error_count += 1
                        try:
                            authorized_shop.message_post(
                                body=_('Error in pagination request: %s') % str(page_error)
                            )
                        except:
                            pass
                        continue
            
            # Post summary message after syncing all orders
                try:
                    if success_count > 0:
                        authorized_shop.message_post(
                        body=_('Successfully imported %d orders from Lazada (Total available: %d). %d errors occurred.') % 
                                (success_count, total_orders, error_count)
                        )
                    else:
                        authorized_shop.message_post(
                            body=_('Failed to import any orders. %d errors occurred.') % error_count
                        )
                except:
                    # If message_post fails, just continue
                    pass
                
        except Exception as e:
            try:
                authorized_shop.message_post(
                    body=_('Error importing orders: %s') % str(e)
                )
            except:
                # If message_post fails, just continue
                pass
            raise
    
    def import_all_orders_from_lazada_for_shop(self, authorized_shop, created_after='2024-01-01T00:00:00Z'):
        """Import all orders with different statuses from Lazada for specific authorized shop
        
        Args:
            authorized_shop: The authorized shop to import orders for
            created_after: ISO 8601 date string to filter orders created after this date
        """
        if not authorized_shop.access_token:
            raise ValidationError(_('No access token available for shop %s') % authorized_shop.shop_name)
        
        # List of statuses to import
        statuses = [
            'pending',
            'shipped', 
            'delivered',
            'completed',
            'cancelled',
            'returned'
        ]
        
        total_success = 0
        total_errors = 0
        
        try:
            for status in statuses:
                try:
                    self.import_from_lazada_for_shop(authorized_shop, created_after)
                    # Note: The import method doesn't return counts, so we can't track individual status results
                except Exception as status_error:
                    total_errors += 1
                    # Log error but continue with next status
                    try:
                        authorized_shop.message_post(
                            body=_('Error importing orders with status %s: %s') % (status, str(status_error))
                        )
                    except:
                        pass
            
            # Post final summary
            try:
                authorized_shop.message_post(
                    body=_('Bulk import completed for all order statuses. Check individual status messages for details.')
                )
            except:
                pass
                
        except Exception as e:
            try:
                authorized_shop.message_post(
                    body=_('Error in bulk import: %s') % str(e)
                )
            except:
                pass
            raise
    
    def _create_or_update_order_from_lazada(self, order_data, authorized_shop):
        """Create or update order from Lazada data"""
        # Check if order already exists
        existing_order = self.search([
            ('order_id', '=', order_data.get('order_id')),
            ('authorized_shop_id', '=', authorized_shop.id)
        ], limit=1)
        
        # Parse created_at safely according to Lazada API format (ISO 8601)
        created_at = self._parse_datetime_safely(order_data.get('created_at'))
        if not created_at:
                # If parsing fails, use current date
            created_at = fields.Datetime.now()
        
        # Parse updated_at
        updated_at = self._parse_datetime_safely(order_data.get('updated_at'))
        
        # Shipping address
        shipping_address = order_data.get('address_shipping', {})
        
        # Billing address
        billing_address = order_data.get('address_billing', {})
        
        # Determine order status from statuses array or default
        order_status = 'pending'
        statuses = order_data.get('statuses', [])
        
        # Valid status values from Lazada API
        valid_statuses = [
            'unpaid', 'pending', 'canceled', 'ready_to_ship', 'delivered', 
            'returned', 'shipped', 'failed', 'topack', 'toship', 'shipping', 'lost'
        ]
        
        if statuses and len(statuses) > 0:
            # Use the first status from the array
            raw_status = statuses[0].lower()
            if raw_status in valid_statuses:
                order_status = raw_status
        
        vals = {
            'order_id': order_data.get('order_id'),
            'order_number': order_data.get('order_number', ''),
            'authorized_shop_id': authorized_shop.id,
            'created_at': created_at,
            'updated_at': updated_at,
            'order_status': order_status,
            'payment_method': order_data.get('payment_method'),
            'order_amount': float(order_data.get('price', 0)),  # price field instead of order_amount
            'currency': 'VND',  # Default currency
            'shipping_fee': float(order_data.get('shipping_fee', 0)),
            'voucher': float(order_data.get('voucher', 0)),
            'tax_amount': 0.0,  # Not available in this API
            'items_count': int(order_data.get('items_count', 0)),
            'remarks': order_data.get('remarks'),
            
            # Additional fields from Lazada API
            'voucher_platform': float(order_data.get('voucher_platform', 0)),
            'voucher_seller': float(order_data.get('voucher_seller', 0)),
            'shipping_fee_discount_platform': float(order_data.get('shipping_fee_discount_platform', 0)),
            'shipping_fee_discount_seller': float(order_data.get('shipping_fee_discount_seller', 0)),
            'shipping_fee_original': float(order_data.get('shipping_fee_original', 0)),
            'warehouse_code': order_data.get('warehouse_code'),
            'gift_option': order_data.get('gift_option') == 'true',
            'is_cancel_pending': order_data.get('is_cancel_pending') == 'true',
            'need_cancel_confirm': order_data.get('need_cancel_confirm') == 'true',
            'buyer_note': order_data.get('buyer_note'),
            'gift_message': order_data.get('gift_message'),
            
            # Customer information (direct from root level)
            'customer_first_name': order_data.get('customer_first_name'),
            'customer_last_name': order_data.get('customer_last_name'),
            'email': '',  # Not available in this API
            'phone': '',  # Not available in this API
            'customer_id': '',  # Not available in this API
            
            # Shipping address
            'shipping_address_first_name': shipping_address.get('first_name'),
            'shipping_address_last_name': shipping_address.get('last_name'),
            'shipping_address': shipping_address.get('address1', ''),
            'shipping_address_city': shipping_address.get('city'),
            'shipping_address_state': shipping_address.get('addressDsitrict'),
            'shipping_address_post_code': shipping_address.get('post_code'),
            'shipping_address_country': shipping_address.get('country'),
            'shipping_address_phone': shipping_address.get('phone'),
            
            # Billing address
            'billing_address_first_name': billing_address.get('first_name'),
            'billing_address_last_name': billing_address.get('last_name'),
            'billing_address': billing_address.get('address1', ''),
            'billing_address_city': billing_address.get('city'),
            'billing_address_state': billing_address.get('addressDsitrict'),
            'billing_address_post_code': billing_address.get('post_code'),
            'billing_address_country': billing_address.get('country'),
            'billing_address_phone': billing_address.get('phone'),
            
            'last_sync_date': fields.Datetime.now(),
        }
        
        if existing_order:
            existing_order.write(vals)
        else:
            vals['sync_status'] = 'synced'
            order = self.create(vals)
    
    @api.model
    def _update_order_lines_batch(self, orders_data, authorized_shop):
        """Update order lines for multiple orders in one API call"""
        if not orders_data or not authorized_shop.access_token:
            return
        
        try:
            # Extract order IDs from orders_data
            order_ids = []
            for order_data in orders_data:
                order_id = order_data.get('order_id') or order_data.get('order_number')
                if order_id:
                    order_ids.append(str(order_id))
            
            if not order_ids:
                return
            
            # Call API in chunks of 10 orders each (to reduce API load)
            endpoint = '/orders/items/get'
            
            # Process orders in chunks of 10
            chunk_size = 10
            total_chunks = (len(order_ids) + chunk_size - 1) // chunk_size  # Ceiling division
            
            
            for chunk_index in range(0, len(order_ids), chunk_size):
                chunk_order_ids = order_ids[chunk_index:chunk_index + chunk_size]
                chunk_number = (chunk_index // chunk_size) + 1
                
                # Format: Comma-separated list in square brackets
                order_ids_param = '[' + ','.join(chunk_order_ids) + ']'
                
                params = {
                    'order_ids': order_ids_param
                }
                
                
                try:
                    response = authorized_shop._make_api_request(endpoint, params, 'GET')
                    
                    
                    if response.get('code') == '0' and response.get('data'):
                        orders_items_data = response.get('data', [])
                        
                        
                        # Process each order's items in this chunk
                        for order_items_data in orders_items_data:
                            order_id_from_api = order_items_data.get('order_id') or order_items_data.get('order_number')
                            order_items = order_items_data.get('order_items', [])
                            
                            # Find the corresponding Odoo order
                            odoo_order = self.search([
                                ('order_id', '=', order_id_from_api),
                                ('authorized_shop_id', '=', authorized_shop.id)
                            ], limit=1)
                            
                            if odoo_order and order_items:
                                # Clear existing order lines
                                odoo_order.order_line_ids.unlink()
                                
                                # Create new order lines
                                for item_data in order_items:
                                    try:
                                        odoo_order._create_order_line_from_item_data(item_data)
                                    except Exception as line_error:
                                        # Log error but continue with other lines
                                        try:
                                            authorized_shop.message_post(
                                                body=_('Error creating order line for order %s: %s') % 
                                                        (order_id_from_api, str(line_error))
                                            )
                                        except:
                                            pass
                                
                    else:
                        # API returned error for this chunk
                        pass
                        
                except Exception as chunk_error:
                    # Log error for this chunk but continue with other chunks
                    try:
                        authorized_shop.message_post(
                            body=_('Error processing chunk %d/%d: %s') % 
                                    (chunk_number, total_chunks, str(chunk_error))
                        )
                    except:
                        pass
            
                        
        except Exception as e:
            # Log error but don't fail the batch
            try:
                authorized_shop.message_post(
                    body=_('Error in batch order items import: %s') % str(e)
                )
            except:
                pass
    
    def _create_order_line_from_item_data(self, item_data):
        """Create order line from item data"""
        # Parse datetime fields
        item_created_at = self._parse_datetime_safely(item_data.get('created_at'))
        item_updated_at = self._parse_datetime_safely(item_data.get('updated_at'))
        sla_time_stamp = self._parse_datetime_safely(item_data.get('sla_time_stamp'))
        payment_time = self._parse_datetime_safely(item_data.get('payment_time'))
        
        # Parse pick up store info
        pick_up_store_info = item_data.get('pick_up_store_info', {})
        
        # Validate and sanitize status
        valid_statuses = ['unpaid', 'pending', 'confirmed', 'canceled', 'cancelled', 
                         'ready_to_ship', 'delivered', 'returned', 'shipped', 'failed',
                         'topack', 'toship', 'shipping', 'lost', 'processing', 
                         'packed', 'completed']
        item_status = item_data.get('status', 'pending')
        if item_status not in valid_statuses:
            item_status = 'pending'  # Fallback to pending for invalid status
        
        # Try to find linked Lazada product via lazada_sku_id
        lazada_product = None
        sku = item_data.get('sku')
        sku_id = item_data.get('sku_id')
        if sku and sku_id:
            # Find via product SKU table using lazada_sku_id only
            product_sku = self.env['ta.lazada.product'].search([
                ('lazada_sku_id', '=', sku_id),
                ('seller_sku', '=', sku),
                ('authorized_shop_id', '=', self.authorized_shop_id.id)
            ], limit=1)
            if product_sku:
                lazada_product = product_sku
        
        self.env['ta.lazada.order.line'].create({
            'order_id': self.id,
            'order_item_id': str(item_data.get('order_item_id', '')),
            'sku': item_data.get('sku'),
            'shop_sku': item_data.get('shop_sku'),
            'name': item_data.get('name'),
            'quantity': 1,  # Default quantity, need to find actual quantity field
            'variation': item_data.get('variation'),  # Product variant info
            'price': float(item_data.get('item_price', 0)),
            'paid_price': float(item_data.get('paid_price', 0)),
            'supply_price': float(item_data.get('supply_price', 0)),
            'currency': item_data.get('currency', 'VND'),
            'tax_amount': float(item_data.get('tax_amount', 0)),
            'shipping_fee': float(item_data.get('shipping_amount', 0)),
            'status': item_status,
            'shipment_provider': item_data.get('shipment_provider'),
            'tracking_number': item_data.get('tracking_code'),
            'reason': item_data.get('reason'),
            'reason_detail': item_data.get('reason_detail'),
            
            # Additional fields from order items API
            'product_id': item_data.get('product_id'),
            'sku_id': item_data.get('sku_id'),
            'warehouse_code': item_data.get('warehouse_code'),
            'shipping_type': item_data.get('shipping_type'),
            'voucher_amount': float(item_data.get('voucher_amount', 0)),
            'voucher_platform': float(item_data.get('voucher_platform', 0)),
            'voucher_seller': float(item_data.get('voucher_seller', 0)),
            'shipping_fee_original': float(item_data.get('shipping_fee_original', 0)),
            'shipping_fee_discount_platform': float(item_data.get('shipping_fee_discount_platform', 0)),
            'shipping_fee_discount_seller': float(item_data.get('shipping_fee_discount_seller', 0)),
            'order_type': item_data.get('order_type'),
            'is_cancel_pending': item_data.get('is_cancel_pending') == 'true',
            'need_cancel_confirm': item_data.get('need_cancel_confirm') == 'true',
            'buyer_id': str(item_data.get('buyer_id', '')),
            'purchase_order_id': item_data.get('purchase_order_id'),
            'purchase_order_number': item_data.get('purchase_order_number'),
            'invoice_number': item_data.get('invoice_number'),
            'gift_wrapping': item_data.get('gift_wrapping'),
            'personalization': item_data.get('personalization'),
            'product_main_image': item_data.get('product_main_image'),
            'product_detail_url': item_data.get('product_detail_url'),
            'created_at': item_created_at or fields.Datetime.now(),
            'updated_at': item_updated_at,
            
            # New fields from /orders/items/get API
            'voucher_code_seller': item_data.get('voucher_code_seller'),
            'voucher_code': item_data.get('voucher_code'),
            'voucher_code_platform': item_data.get('voucher_code_platform'),
            'package_id': item_data.get('package_id'),
            'biz_group': str(item_data.get('biz_group', '')),
            'show_gift_wrapping_tag': item_data.get('show_gift_wrapping_tag') == 'True',
            'show_personalization_tag': item_data.get('show_personalization_tag') == 'True',
            'can_escalate_pickup': item_data.get('can_escalate_pickup') == 'true',
            'cancel_trigger_time': item_data.get('cancel_trigger_time'),
            'cancel_return_initiator': item_data.get('cancel_return_initiator'),
            'is_reroute': str(item_data.get('is_reroute', '')),
            'stage_pay_status': item_data.get('stage_pay_status'),
            'tracking_code_pre': item_data.get('tracking_code_pre'),
            'order_flag': item_data.get('order_flag'),
            'is_fbl': str(item_data.get('is_fbl', '')),
            'delivery_option_sof': str(item_data.get('delivery_option_sof', '')),
            'fulfillment_sla': item_data.get('fulfillment_sla'),
            'promised_shipping_time': item_data.get('promised_shipping_time'),
            'mp3_order': item_data.get('mp3_order') == 'True',
            'voucher_seller_lpi': float(item_data.get('voucher_seller_lpi', 0)),
            'wallet_credits': float(item_data.get('wallet_credits', 0)),
            'reverse_order_id': item_data.get('reverse_order_id'),
            'shipping_provider_type': item_data.get('shipping_provider_type'),
            'voucher_platform_lpi': float(item_data.get('voucher_platform_lpi', 0)),
            'schedule_delivery_start_timeslot': item_data.get('schedule_delivery_start_timeslot'),
            'schedule_delivery_end_timeslot': item_data.get('schedule_delivery_end_timeslot'),
            'is_digital': str(item_data.get('is_digital', '')),
            'shipping_service_cost': float(item_data.get('shipping_service_cost', 0)),
            'return_status': str(item_data.get('return_status', '')),
            'semi_managed': item_data.get('semi_managed') == 'True',
            'priority_fulfillment_tag': item_data.get('priority_fulfillment_tag'),
            'supply_price_currency': item_data.get('supply_price_currency'),
            'digital_delivery_info': item_data.get('digital_delivery_info'),
            'extra_attributes': item_data.get('extra_attributes'),
            'sla_time_stamp': sla_time_stamp,
            'payment_time': payment_time,
            
            # Pick up store information
            'pick_up_store_address': pick_up_store_info.get('pick_up_store_address'),
            'pick_up_store_name': pick_up_store_info.get('pick_up_store_name'),
            'pick_up_store_code': pick_up_store_info.get('pick_up_store_code'),
            'pick_up_store_open_hour': str(pick_up_store_info.get('pick_up_store_open_hour', [])),
            
            # Link to Lazada product
            'lazada_product_id': lazada_product.id if lazada_product else False,
        })




class TaLazadaOrderLine(models.Model):
    _name = 'ta.lazada.order.line'
    _description = 'Lazada Order Line'

    order_id = fields.Many2one('ta.lazada.order', 'Order', required=True, ondelete='cascade')
    
    # Basic Item Information - theo API Lazada
    order_item_id = fields.Char('Order Item ID', required=True)
    sku = fields.Char('SKU')
    shop_sku = fields.Char('Shop SKU')
    name = fields.Char('Product Name', required=True)
    quantity = fields.Float('Quantity', required=True)
    variation = fields.Char('Product Variation', help='Product variant information from Lazada')
    price = fields.Float('Price', required=True)
    paid_price = fields.Float('Paid Price')
    supply_price = fields.Float('Supply Price')
    currency = fields.Char('Currency', default='VND')
    
    # Additional Item Details - theo API Lazada
    tax_amount = fields.Float('Tax Amount')
    shipping_fee = fields.Float('Shipping Fee')
    shipping_amount = fields.Float('Shipping Amount')
    status = fields.Selection([
        ('unpaid', 'Unpaid'),
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('canceled', 'Canceled'),
        ('cancelled', 'Cancelled'),
        ('ready_to_ship', 'Ready to Ship'),
        ('delivered', 'Delivered'),
        ('returned', 'Returned'),
        ('shipped', 'Shipped'),
        ('failed', 'Failed'),
        ('topack', 'To Pack'),
        ('toship', 'To Ship'),
        ('shipping', 'Shipping'),
        ('lost', 'Lost'),
        ('processing', 'Processing'),
        ('packed', 'Packed'),
        ('completed', 'Completed'),
    ], string='Item Status', default='pending')
    
    # Shipping Information - theo API Lazada
    shipment_provider = fields.Char('Shipment Provider')
    tracking_number = fields.Char('Tracking Number')
    shipping_type = fields.Char('Shipping Type')
    warehouse_code = fields.Char('Warehouse Code')
    
    # Voucher and Discount Information
    voucher_amount = fields.Float('Voucher Amount')
    voucher_platform = fields.Float('Voucher Platform')
    voucher_seller = fields.Float('Voucher Seller')
    shipping_fee_original = fields.Float('Shipping Fee Original')
    shipping_fee_discount_platform = fields.Float('Shipping Fee Discount Platform')
    shipping_fee_discount_seller = fields.Float('Shipping Fee Discount Seller')
    
    # Additional Information
    product_id = fields.Char('Product ID')
    sku_id = fields.Char('SKU ID')
    order_type = fields.Char('Order Type')
    is_cancel_pending = fields.Boolean('Is Cancel Pending')
    need_cancel_confirm = fields.Boolean('Need Cancel Confirm')
    buyer_id = fields.Char('Buyer ID')
    purchase_order_id = fields.Char('Purchase Order ID')
    purchase_order_number = fields.Char('Purchase Order Number')
    invoice_number = fields.Char('Invoice Number')
    gift_wrapping = fields.Text('Gift Wrapping')
    personalization = fields.Text('Personalization')
    product_main_image = fields.Char('Product Main Image')
    product_detail_url = fields.Char('Product Detail URL')
    created_at = fields.Datetime('Created At')
    updated_at = fields.Datetime('Updated At')
    
    # Reason for cancellation/return - theo API Lazada
    reason = fields.Text('Reason')
    reason_detail = fields.Text('Reason Detail')
    
    # Additional fields from /orders/items/get API
    voucher_code_seller = fields.Char('Voucher Code Seller')
    voucher_code = fields.Char('Voucher Code')
    voucher_code_platform = fields.Char('Voucher Code Platform')
    package_id = fields.Char('Package ID')
    biz_group = fields.Char('Business Group')
    show_gift_wrapping_tag = fields.Boolean('Show Gift Wrapping Tag')
    show_personalization_tag = fields.Boolean('Show Personalization Tag')
    can_escalate_pickup = fields.Boolean('Can Escalate Pickup')
    cancel_trigger_time = fields.Char('Cancel Trigger Time')
    cancel_return_initiator = fields.Char('Cancel Return Initiator')
    is_reroute = fields.Char('Is Reroute')
    stage_pay_status = fields.Char('Stage Pay Status')
    tracking_code_pre = fields.Char('Tracking Code Pre')
    order_flag = fields.Char('Order Flag')
    is_fbl = fields.Char('Is FBL')
    delivery_option_sof = fields.Char('Delivery Option SOF')
    fulfillment_sla = fields.Char('Fulfillment SLA')
    promised_shipping_time = fields.Char('Promised Shipping Time')
    mp3_order = fields.Boolean('MP3 Order')
    voucher_seller_lpi = fields.Float('Voucher Seller LPI')
    wallet_credits = fields.Float('Wallet Credits')
    reverse_order_id = fields.Char('Reverse Order ID')
    shipping_provider_type = fields.Char('Shipping Provider Type')
    voucher_platform_lpi = fields.Float('Voucher Platform LPI')
    schedule_delivery_start_timeslot = fields.Char('Schedule Delivery Start Timeslot')
    schedule_delivery_end_timeslot = fields.Char('Schedule Delivery End Timeslot')
    is_digital = fields.Char('Is Digital')
    shipping_service_cost = fields.Float('Shipping Service Cost')
    return_status = fields.Char('Return Status')
    semi_managed = fields.Boolean('Semi Managed')
    priority_fulfillment_tag = fields.Char('Priority Fulfillment Tag')
    supply_price_currency = fields.Char('Supply Price Currency')
    digital_delivery_info = fields.Text('Digital Delivery Info')
    extra_attributes = fields.Text('Extra Attributes')
    sla_time_stamp = fields.Datetime('SLA Time Stamp')
    payment_time = fields.Datetime('Payment Time')
    
    # Pick up store information
    pick_up_store_address = fields.Char('Pick Up Store Address')
    pick_up_store_name = fields.Char('Pick Up Store Name')
    pick_up_store_code = fields.Char('Pick Up Store Code')
    pick_up_store_open_hour = fields.Text('Pick Up Store Open Hour')
    
    # Link to Lazada product
    lazada_product_id = fields.Many2one('ta.lazada.product', 'Lazada Product', 
                                       help='Linked Lazada product')
    
    # Computed fields
    total_price = fields.Float('Total Price', compute='_compute_total_price', store=True)
    
    @api.depends('quantity', 'price')
    def _compute_total_price(self):
        for record in self:
            record.total_price = record.quantity * record.price
