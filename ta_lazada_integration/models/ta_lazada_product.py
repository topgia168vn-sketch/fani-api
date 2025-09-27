# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import requests
import json
import base64
from datetime import datetime, timedelta


class TaLazadaProduct(models.Model):
    _name = 'ta.lazada.product'
    _description = 'Lazada Product'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    # Basic Information
    name = fields.Char('Product Name', required=True)
    sku = fields.Char('SKU', required=True)
    seller_sku = fields.Char('Seller SKU')
    shop_sku = fields.Char('Shop SKU')
    lazada_item_id = fields.Char('Lazada Item ID', help='Item ID in Lazada')
    lazada_sku_id = fields.Char('Lazada SKU ID', help='SKU ID in Lazada (variant)')
    # Lazada product variants
    sku_ids = fields.One2many('ta.lazada.product.sku', 'product_id', 'SKUs')
    item_type = fields.Selection([
        ('simple', 'Simple Product'),
        ('variable', 'Variable Product'),
    ], string='Item Type', default='simple')
    authorized_shop_id = fields.Many2one('ta.lazada.authorized.shop', 'Authorized Shop', required=True)
    config_id = fields.Many2one('ta.lazada.config', 'ISV Configuration', related='authorized_shop_id.isv_config_id', store=True, readonly=True)
    
    # Product Details
    brand = fields.Char('Brand')
    model = fields.Char('Model')
    warranty = fields.Char('Warranty')
    package_weight = fields.Float('Package Weight (kg)')
    package_length = fields.Float('Package Length (cm)')
    package_width = fields.Float('Package Width (cm)')
    package_height = fields.Float('Package Height (cm)')
    description_html = fields.Html('Description')
    video_id = fields.Char('Video ID')
    url = fields.Char('Product URL')
    
    # Pricing
    price = fields.Float('Price', required=True)
    special_price = fields.Float('Special Price')
    special_price_from = fields.Datetime('Special Price From')
    special_price_to = fields.Datetime('Special Price To')
    currency = fields.Char('Currency')
    
    # Inventory
    quantity = fields.Integer('Quantity', default=0)
    min_quantity = fields.Integer('Min Quantity', default=0)
    barcode = fields.Char('Barcode/EAN/UPC')
    
    # Status (lowercase to match search filters and Lazada states)
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('deleted', 'Deleted'),
        ('pending', 'Pending'),
        ('rejected', 'Rejected'),
    ], string='Status', default='pending')
    
    
    # Sync Information
    last_sync_date = fields.Datetime('Last Sync Date')
    sync_status = fields.Selection([
        ('pending', 'Pending'),
        ('synced', 'Synced'),
        ('failed', 'Failed'),
        ('updating', 'Updating'),
    ], string='Sync Status', default='pending')
    
    # Images
    image_ids = fields.One2many('ta.lazada.product.image', 'product_id', 'Images')
    
    # Categories
    category_id = fields.Many2one('ta.lazada.category', 'Primary Category')
    
    # Attributes
    attribute_ids = fields.One2many('ta.lazada.product.attribute', 'product_id', 'Attributes')
    
    
    _sql_constraints = [
        ('sku_shop_unique', 'unique(sku, authorized_shop_id)', 'SKU must be unique per authorized shop'),
        ('lazada_sku_unique', 'unique(lazada_sku_id, authorized_shop_id)', 'Lazada SKU ID must be unique per authorized shop'),
    ]

    def import_from_lazada_for_shop(self, authorized_shop):
        """Import products from Lazada for specific authorized shop"""
        if not authorized_shop.access_token:
            raise ValidationError(_('No access token available for shop %s') % authorized_shop.shop_name)
        
        try:
            # Use authorized shop's access token to make API request
            endpoint = '/products/get'
            limit = 50
            offset = 0
            total_expected = None
            total_imported = 0
            success_count = 0
            error_count = 0

            while True:
                params = {
                    'filter': 'all',
                    'offset': offset,
                    'limit': limit,
                }
                response = authorized_shop._make_api_request(endpoint, params, 'GET')

                if response.get('code') != '0' or not response.get('data'):
                    break

                data_node = response['data']
                if total_expected is None:
                    total_expected = data_node.get('total_products') or data_node.get('total') or 0

                products_data = data_node.get('products', []) or []

                for product_data in products_data:
                    try:
                        # Fetch full item detail to properly build variants/templates
                        item_id = product_data.get('item_id') or product_data.get('itemId')
                        detail = {}
                        if item_id:
                            try:
                                detail = authorized_shop._make_api_request('/product/item/get', {'item_id': item_id}, 'GET')
                            except Exception:
                                detail = {}
                        # Prefer detailed data if available
                        merged = product_data.copy()
                        if isinstance(detail, dict) and detail.get('code') == '0' and detail.get('data'):
                            merged.update(detail.get('data') or {})
                        # If detail's attributes exist, nest them consistently
                        if isinstance(detail, dict):
                            data_node = detail.get('data') or {}
                            if data_node.get('attributes') and not merged.get('attributes'):
                                merged['attributes'] = data_node.get('attributes')
                        # Create/update from merged data
                        self._create_or_update_product_from_lazada(merged, authorized_shop)
                        # Estimate imported count by number of skus
                        skus_data = merged.get('skus', [])
                        total_imported += max(1, len(skus_data) or 1)
                        success_count += 1
                    except Exception as product_error:
                        error_count += 1
                        pass

                # Break conditions: fetched less than limit, or reached total_expected
                if len(products_data) < limit:
                    break
                if total_expected and (offset + limit) >= int(total_expected):
                    break

                offset += limit

            # Post summary message
            try:
                if success_count > 0:
                    authorized_shop.message_post(
                        body=_('Successfully imported %d products (%d total items) from Lazada. %d errors occurred.') % (success_count, total_imported, error_count)
                    )
                else:
                    authorized_shop.message_post(
                        body=_('Failed to import any products. %d errors occurred.') % error_count
                    )
            except:
                pass

        except Exception as e:
            try:
                authorized_shop.message_post(
                    body=_('Error importing products: %s') % str(e)
                )
            except:
                # If message_post fails, just continue
                pass
            raise
    
    def _create_or_update_product_from_lazada(self, product_data, authorized_shop):
        """Create or update product from Lazada data"""
        # Check if this is a variant product (has multiple SKUs)
        skus_data = product_data.get('skus', [])
        
        if len(skus_data) > 1:
            # Handle variant product (multiple SKUs)
            self._handle_variant_product(product_data, authorized_shop, skus_data)
        else:
            # Handle simple product (single SKU)
            self._handle_simple_product(product_data, authorized_shop)
    
    def _handle_simple_product(self, product_data, authorized_shop):
        """Handle simple product without variants"""
        # Get lazada_sku_id for simple product
        lazada_sku_id = product_data.get('sku_id') or product_data.get('skuId') or product_data.get('SkuId')
        lazada_item_id = product_data.get('item_id') or product_data.get('itemId')
        
        # For simple products, search by lazada_item_id first (more reliable)
        existing_product = self.search([
            ('lazada_item_id', '=', lazada_item_id),
            ('authorized_shop_id', '=', authorized_shop.id)
        ], limit=1)
        
        # If not found by lazada_item_id, try by lazada_sku_id (fallback)
        if not existing_product and lazada_sku_id:
            existing_product = self.search([
                ('lazada_sku_id', '=', lazada_sku_id),
                ('authorized_shop_id', '=', authorized_shop.id)
            ], limit=1)
        
        # Get SKU from product data
        sku = (product_data.get('sku') or product_data.get('SellerSku') or '').strip()
        
        # Generate unique SKU if empty
        if not sku:
            sku = f"LAZADA-{product_data.get('item_id', 'NO-ID')}"
        
        # Map Lazada category
        category_ref = product_data.get('primary_category') or product_data.get('primary_category_id') or product_data.get('category_id') or product_data.get('categoryId')
        lazada_category = False
        if category_ref:
            lazada_category = self.env['ta.lazada.category'].search([
                ('lazada_category_id', '=', str(category_ref)),
                ('authorized_shop_id', '=', authorized_shop.id)
            ], limit=1)
        
        # Extract attributes block
        attributes_map = product_data.get('attributes') or {}
        # Normalize fields from attributes
        brand_val = attributes_map.get('brand') or product_data.get('brand')
        model_val = attributes_map.get('model') or product_data.get('model')
        name_val = attributes_map.get('name') or product_data.get('name')
        description_val = attributes_map.get('description') or product_data.get('description')
        video_val = attributes_map.get('video') or product_data.get('video')

        vals = {
            'name': name_val or '',
            'sku': sku,
            'seller_sku': (product_data.get('SellerSku') or '').strip() or sku,
            'shop_sku': (product_data.get('ShopSku') or '').strip() or False,
            'lazada_item_id': lazada_item_id,
            'lazada_sku_id': lazada_sku_id,
            'authorized_shop_id': authorized_shop.id,
            'item_type': 'simple',
            'price': float(product_data.get('price', 0)),
            'special_price': float(product_data.get('special_price', 0) or 0),
            'quantity': int(product_data.get('quantity', product_data.get('Available', 0) or 0)),
            'status': str(product_data.get('status') or product_data.get('Status') or 'pending').lower(),
            'barcode': product_data.get('barcode') or product_data.get('ean') or product_data.get('upc'),
            'brand': brand_val,
            'model': model_val,
            'description_html': description_val,
            'video_id': video_val,
            'url': product_data.get('Url') or product_data.get('url'),
            'last_sync_date': fields.Datetime.now(),
            'category_id': lazada_category.id if lazada_category else False,
        }
        
        if existing_product:
            existing_product.write(vals)
            lazada_product = existing_product
        else:
            vals['sync_status'] = 'synced'
            lazada_product = self.create(vals)
        
        # Upsert product attributes one2many if present
        try:
            if attributes_map:
                # Clear existing attributes to avoid duplicates
                lazada_product.attribute_ids.unlink()
                kv_list = []
                for key, value in attributes_map.items():
                    if key == 'description':
                        continue
                    # Convert list to comma string for readability
                    if isinstance(value, list):
                        value_str = ', '.join([str(v) for v in value])
                    elif isinstance(value, dict):
                        # Flatten simple dicts as key1: v1; key2: v2
                        value_str = '; '.join([f"{k}: {v}" for k, v in value.items()])
                    else:
                        value_str = str(value)
                    kv_list.append((0, 0, {
                        'name': str(key),
                        'value': value_str,
                        'is_required': False,
                    }))
                if kv_list:
                    lazada_product.write({'attribute_ids': kv_list})
        except Exception:
            pass

        # Create or update SKU record for simple product
        try:
            lazada_sku_id_val = lazada_sku_id or 'SIMPLE'
            sku_vals = {
                'product_id': lazada_product.id,
                'lazada_sku_id': lazada_sku_id_val,
                'seller_sku': vals.get('seller_sku'),
                'shop_sku': vals.get('shop_sku'),
                'status': vals.get('status'),
                'price': vals.get('price'),
                'special_price': vals.get('special_price'),
                'quantity': vals.get('quantity'),
                'url': vals.get('url'),
                'package_weight': vals.get('package_weight') or 0.0,
                'package_length': vals.get('package_length') or 0.0,
                'package_width': vals.get('package_width') or 0.0,
                'package_height': vals.get('package_height') or 0.0,
            }
            existing_sku = self.env['ta.lazada.product.sku'].search([
                ('product_id', '=', lazada_product.id),
                ('lazada_sku_id', '=', lazada_sku_id_val)
            ], limit=1)
            if existing_sku:
                existing_sku.write(sku_vals)
            else:
                self.env['ta.lazada.product.sku'].create(sku_vals)
        except Exception:
            pass

        # Import product images
        self._import_product_images(lazada_product, product_data)
    
    def _handle_variant_product(self, product_data, authorized_shop, skus_data):
        """Handle product with variants (e.g., 1 bịch, 2 bịch, 3 bịch)"""
        # Get main product information
        main_sku = product_data.get('sku', '').strip()
        # Take name from attributes if any
        variant_attributes_map = product_data.get('attributes') or {}
        attributes_map = variant_attributes_map  # For use in variant creation
        product_name = (variant_attributes_map.get('name') or product_data.get('name') or 'Lazada Product')
        
        # Generate unique SKU if empty
        if not main_sku:
            main_sku = f"LAZADA-{product_data.get('item_id', 'NO-ID')}"
        
        # Check if main product already exists by lazada_item_id and shop
        existing_main_product = self.search([
            ('lazada_item_id', '=', product_data.get('item_id') or product_data.get('itemId')),
            ('authorized_shop_id', '=', authorized_shop.id),
            ('lazada_sku_id', 'in', [False, None, ''])  # Main product has no specific SKU ID
        ], limit=1)
        
        # If no main product exists, create one first
        if not existing_main_product:
            # Map category
            category_ref = product_data.get('primary_category') or product_data.get('primary_category_id') or product_data.get('category_id') or product_data.get('categoryId')
            lazada_category = False
            if category_ref:
                lazada_category = self.env['ta.lazada.category'].search([
                    ('lazada_category_id', '=', str(category_ref)),
                    ('authorized_shop_id', '=', authorized_shop.id)
                ], limit=1)
            
            # Create main product record
            main_product_vals = {
                'name': product_name,
                'sku': main_sku,
                'lazada_item_id': product_data.get('item_id') or product_data.get('itemId'),
                'lazada_sku_id': None,  # Main product has no specific SKU ID
                'authorized_shop_id': authorized_shop.id,
                'item_type': 'variable',
                'price': 0.0,  # Will be set from first SKU
                'special_price': 0.0,
                'quantity': 0,  # Will be calculated from all SKUs
                'status': 'pending',
                'sync_status': 'synced',
                'last_sync_date': fields.Datetime.now(),
                'category_id': lazada_category.id if lazada_category else False,
            }
            
            # Extract attributes for main product
            attributes_map = product_data.get('attributes') or {}
            brand_val = attributes_map.get('brand') or product_data.get('brand')
            model_val = attributes_map.get('model') or product_data.get('model')
            description_val = attributes_map.get('description') or product_data.get('description')
            video_val = attributes_map.get('video') or product_data.get('video')
            
            main_product_vals.update({
                'brand': brand_val,
                'model': model_val,
                'description_html': description_val,
                'video_id': video_val,
                'url': product_data.get('Url') or product_data.get('url'),
            })
            
            existing_main_product = self.create(main_product_vals)
            
            # Create attributes for main product
            try:
                if attributes_map:
                    # Clear existing attributes first
                    existing_main_product.attribute_ids.unlink()
                    kv_list = []
                    for key, value in attributes_map.items():
                        if key == 'description':
                            continue
                        # Convert list to comma string for readability
                        if isinstance(value, list):
                            value_str = ', '.join([str(v) for v in value])
                        elif isinstance(value, dict):
                            # Flatten simple dicts as key1: v1; key2: v2
                            value_str = '; '.join([f"{k}: {v}" for k, v in value.items()])
                        else:
                            value_str = str(value)
                        kv_list.append((0, 0, {
                            'name': str(key),
                            'value': value_str,
                            'is_required': False,
                        }))
                    if kv_list:
                        existing_main_product.write({'attribute_ids': kv_list})
            except Exception as e:
                # Log error but continue
                pass
        else:
            # Update existing main product attributes if needed
            try:
                if attributes_map:
                    # Clear existing attributes first
                    existing_main_product.attribute_ids.unlink()
                    kv_list = []
                    for key, value in attributes_map.items():
                        if key == 'description':
                            continue
                        # Convert list to comma string for readability
                        if isinstance(value, list):
                            value_str = ', '.join([str(v) for v in value])
                        elif isinstance(value, dict):
                            # Flatten simple dicts as key1: v1; key2: v2
                            value_str = '; '.join([f"{k}: {v}" for k, v in value.items()])
                        else:
                            value_str = str(value)
                        kv_list.append((0, 0, {
                            'name': str(key),
                            'value': value_str,
                            'is_required': False,
                        }))
                    if kv_list:
                        existing_main_product.write({'attribute_ids': kv_list})
            except Exception as e:
                # Log error but continue
                pass
        
        # Create variants for each SKU
        for sku_data in skus_data:
            seller_sku = (sku_data.get('SellerSku') or sku_data.get('sku') or '').strip()
            variant_price = float(sku_data.get('price', 0))
            variant_special_price = float(sku_data.get('special_price', 0) or 0)
            variant_quantity = int(sku_data.get('quantity', sku_data.get('Available', 0) or 0))
            sale_prop = sku_data.get('saleProp') or {}
            # Human-friendly label from saleProp (e.g., "Phân loại")
            variant_label = None
            if isinstance(sale_prop, dict) and sale_prop:
                variant_label = next(iter(sale_prop.values()))
            if not variant_label:
                variant_label = sku_data.get('Phân loại') or seller_sku
            variant_name = f"{product_name} - {variant_label}" if variant_label else f"{product_name} - Variant {skus_data.index(sku_data) + 1}"
            
            # Generate unique SKU using lazada_sku_id to ensure uniqueness
            lazada_sku_id = sku_data.get('sku_id') or sku_data.get('skuId') or sku_data.get('SkuId')
            if lazada_sku_id:
                variant_sku = f"LAZADA-{lazada_sku_id}"
            elif seller_sku:
                variant_sku = f"{seller_sku}-{skus_data.index(sku_data) + 1}"
            else:
                variant_sku = f"{main_sku}-V{skus_data.index(sku_data) + 1}"
            
            # Create or update Lazada product record for this variant
            existing_variant_product = self.search([
                ('lazada_sku_id', '=', lazada_sku_id),
                ('authorized_shop_id', '=', authorized_shop.id)
            ], limit=1)
        
            vals = {
                'name': variant_name or f"{product_name} - {variant_sku}",
                'sku': variant_sku,
                'seller_sku': seller_sku or variant_sku,
                'shop_sku': (sku_data.get('ShopSku') or '').strip() or False,
                'lazada_item_id': product_data.get('item_id') or product_data.get('itemId'),
                'lazada_sku_id': lazada_sku_id,
                'authorized_shop_id': authorized_shop.id,
                'item_type': 'variable',
                'price': variant_price,
                'special_price': variant_special_price,
                'quantity': variant_quantity,
                'status': str(sku_data.get('Status') or product_data.get('status') or 'pending').lower(),
                'barcode': sku_data.get('barcode') or sku_data.get('ean') or sku_data.get('upc'),
                'url': sku_data.get('Url') or product_data.get('Url') or product_data.get('url'),
                'last_sync_date': fields.Datetime.now(),
                'category_id': existing_main_product.category_id.id if existing_main_product.category_id else False,
            }

            # Update package info per SKU if available (strings to float)
            try:
                for key_src, field_dst in [
                    ('package_weight', 'package_weight'),
                    ('package_length', 'package_length'),
                    ('package_width', 'package_width'),
                    ('package_height', 'package_height'),
                ]:
                    val = sku_data.get(key_src)
                    if val:
                        try:
                            vals[field_dst] = float(val)
                        except Exception:
                            pass
            except Exception:
                pass
            
            if existing_variant_product:
                existing_variant_product.write(vals)
                variant_product = existing_variant_product
            else:
                vals['sync_status'] = 'synced'
                variant_product = self.create(vals)
            
            # Create or update SKU child record for this variant
            try:
                sku_vals = {
                    'product_id': existing_main_product.id,  # Link to main product
                    'lazada_sku_id': lazada_sku_id,
                    'seller_sku': seller_sku,
                    'shop_sku': vals.get('shop_sku'),
                    'status': vals.get('status'),
                    'price': vals.get('price'),
                    'special_price': vals.get('special_price'),
                    'quantity': vals.get('quantity'),
                    'url': vals.get('url'),
                    'variant_name': variant_name,
                    'package_weight': vals.get('package_weight') or 0.0,
                    'package_length': vals.get('package_length') or 0.0,
                    'package_width': vals.get('package_width') or 0.0,
                    'package_height': vals.get('package_height') or 0.0,
                }
                existing_sku = self.env['ta.lazada.product.sku'].search([
                    ('product_id', '=', existing_main_product.id),
                    ('lazada_sku_id', '=', lazada_sku_id)
                ], limit=1)
                if existing_sku:
                    existing_sku.write(sku_vals)
                else:
                    self.env['ta.lazada.product.sku'].create(sku_vals)
            except Exception:
                pass
            
            # Create or update attributes for variant product
            try:
                if attributes_map:
                    # Clear existing attributes to avoid duplicates
                    variant_product.attribute_ids.unlink()
                    kv_list = []
                    for key, value in attributes_map.items():
                        if key == 'description':
                            continue
                        # Convert list to comma string for readability
                        if isinstance(value, list):
                            value_str = ', '.join([str(v) for v in value])
                        elif isinstance(value, dict):
                            # Flatten simple dicts as key1: v1; key2: v2
                            value_str = '; '.join([f"{k}: {v}" for k, v in value.items()])
                        else:
                            value_str = str(value)
                        kv_list.append((0, 0, {
                            'name': str(key),
                            'value': value_str,
                            'is_required': False,
                        }))
                    if kv_list:
                        variant_product.write({'attribute_ids': kv_list})
            except Exception:
                pass

        # Import images for main product (shared across all variants)
        self._import_product_images(existing_main_product, product_data)
    
    def _import_product_images(self, lazada_product, product_data):
        """Import product images from Lazada data"""
        try:
            # Clear existing images
            lazada_product.env['ta.lazada.product.image'].search([
                ('product_id', '=', lazada_product.id)
            ]).unlink()
            
            # Get images from product data
            images_data = product_data.get('images', [])
            if not images_data:
                # Try alternative image fields
                images_data = product_data.get('image_urls', [])
            
            # If images_data is a string (single URL), convert to list
            if isinstance(images_data, str):
                images_data = [images_data]
            
            # Import each image
            for index, image_data in enumerate(images_data):
                if isinstance(image_data, dict):
                    image_url = image_data.get('url') or image_data.get('image_url')
                    image_name = image_data.get('name', f"Image {index + 1}")
                    hash_code = image_data.get('hash_code')
                    sort_order = image_data.get('sort_order', index)
                else:
                    # If image_data is just a URL string
                    image_url = image_data
                    image_name = f"Image {index + 1}"
                    hash_code = None
                    sort_order = index
                
                if image_url:
                    # Download and store image
                    try:
                        response = requests.get(image_url, timeout=30)
                        if response.status_code == 200:
                            image_binary = base64.b64encode(response.content)
                            
                            # Create image record
                            lazada_product.env['ta.lazada.product.image'].create({
                                'product_id': lazada_product.id,
                                'name': image_name,
                                'image': image_binary,
                                'image_url': image_url,
                                'hash_code': hash_code,
                                'sort_order': sort_order,
                            })
                    except Exception as e:
                        # Log error but continue with other images
                        continue
                        
        except Exception as e:
            # Log error but don't stop product creation
            pass


class TaLazadaProductImage(models.Model):
    _name = 'ta.lazada.product.image'
    _description = 'Lazada Product Image'

    product_id = fields.Many2one('ta.lazada.product', 'Product', required=True, ondelete='cascade')
    name = fields.Char('Image Name')
    image = fields.Binary('Image')
    image_url = fields.Char('Image URL')
    hash_code = fields.Char('Hash Code')
    sort_order = fields.Integer('Sort Order', default=0)


class TaLazadaProductAttribute(models.Model):
    _name = 'ta.lazada.product.attribute'
    _description = 'Lazada Product Attribute'

    product_id = fields.Many2one('ta.lazada.product', 'Product', required=True, ondelete='cascade')
    name = fields.Char('Attribute Name', required=True)
    value = fields.Char('Attribute Value', required=True)
    is_required = fields.Boolean('Required', default=False)


class TaLazadaProductSku(models.Model):
    _name = 'ta.lazada.product.sku'
    _description = 'Lazada Product SKU'

    product_id = fields.Many2one('ta.lazada.product', 'Lazada Product', required=True, ondelete='cascade')
    lazada_sku_id = fields.Char('Lazada SKU ID', required=True)
    seller_sku = fields.Char('Seller SKU')
    shop_sku = fields.Char('Shop SKU')
    variant_name = fields.Char('Variant Name')
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('deleted', 'Deleted'),
        ('pending', 'Pending'),
        ('rejected', 'Rejected'),
    ], string='Status', default='pending')
    price = fields.Float('Price')
    special_price = fields.Float('Special Price')
    quantity = fields.Float('Quantity')
    url = fields.Char('URL')

    package_weight = fields.Float('Package Weight (kg)')
    package_length = fields.Float('Package Length (cm)')
    package_width = fields.Float('Package Width (cm)')
    package_height = fields.Float('Package Height (cm)')

    _sql_constraints = [
        ('sku_unique_per_product', 'unique(product_id, lazada_sku_id)', 'SKU must be unique per Lazada product'),
    ]
