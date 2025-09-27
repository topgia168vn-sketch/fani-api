# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import time


class TaLazadaWarehouse(models.Model):
    _name = 'ta.lazada.warehouse'
    _description = 'Lazada Warehouse'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'warehouse_name'

    # Basic Information from API
    warehouse_name = fields.Char('Warehouse Name', required=True)
    warehouse_code = fields.Char('Warehouse Code', required=True)
    country_code = fields.Selection([
        ('SG', 'Singapore'),
        ('MY', 'Malaysia'),
        ('TH', 'Thailand'),
        ('PH', 'Philippines'),
        ('ID', 'Indonesia'),
        ('VN', 'Vietnam'),
    ], string='Country Code', required=True)
    
    # Location Information
    town_code = fields.Char('Town Code')
    area_code = fields.Char('Area Code')
    city_code = fields.Char('City Code')
    division_id = fields.Char('Division ID')
    zip_code = fields.Char('ZIP Code')
    latitude = fields.Float('Latitude', digits=(10, 6))
    longitude = fields.Float('Longitude', digits=(10, 6))
    
    # Platform Information
    platform_name = fields.Char('Platform Name', help='Supported platforms (e.g., LAZADA_SG, LAZADA_MY)')
    multi_channel = fields.Boolean('Multi Channel', default=False, help='Whether warehouse supports multiple channels')
    
    # Shop Relationship
    authorized_shop_id = fields.Many2one('ta.lazada.authorized.shop', 'Authorized Shop', required=True)
    
    # Sync Information
    last_sync_date = fields.Datetime('Last Sync Date')
    sync_status = fields.Selection([
        ('pending', 'Pending'),
        ('synced', 'Synced'),
        ('failed', 'Failed'),
    ], string='Sync Status', default='pending')
    
    # Status
    active = fields.Boolean('Active', default=True)
    
    _sql_constraints = [
        ('warehouse_code_unique', 'unique(warehouse_code, authorized_shop_id)', 'Warehouse Code must be unique per authorized shop'),
    ]

    @api.model
    def import_from_lazada_for_shop(self, authorized_shop):
        """Import warehouses from Lazada for a specific shop with pagination support"""
        if not authorized_shop.access_token:
            raise ValidationError(_('Shop must have valid access token'))
        
        try:
            # Initialize pagination variables
            total_synced = 0
            page = 1
            per_page = authorized_shop.warehouse_page_size or 20
            country_code = authorized_shop.warehouse_country_code or authorized_shop.country_code or 'VN'
            total_pages = None
            
            # Loop through all pages
            while True:
                # Get warehouses from Lazada API for current page
                endpoint = '/fbl/warehouses/get'
                params = {
                    'country_code': country_code,
                    'page': page,
                    'per_page': per_page,
                }

                response = authorized_shop._make_api_request(endpoint, params, 'GET')
                
                if response.get('code') == '0':
                    warehouses_data = response.get('data', [])
                    
                    # Process warehouses for current page
                    page_sync_count = self._process_warehouses_data(warehouses_data, authorized_shop)
                    total_synced += page_sync_count
                    
                    # Get pagination info from response
                    total_count = int(response.get('total_count', 0))
                    current_total_pages = int(response.get('total_page', 1))
                    
                    # Set total_pages if not set yet
                    if total_pages is None:
                        total_pages = current_total_pages
                    
                    # Check if we have more pages to process
                    if page >= total_pages or len(warehouses_data) < per_page:
                        break
                        
                    page += 1
                    
                    # Add a small delay between requests to avoid rate limiting
                    time.sleep(0.5)
                    
                else:
                    error_msg = response.get('error_message', 'Failed to fetch warehouses')
                    raise ValidationError(_('Warehouse sync failed on page %d: %s') % (page, error_msg))
            
            # Add note to shop about sync result
            message = _('Warehouse sync completed successfully. Imported %d warehouses from %d pages.') % (total_synced, total_pages or page)
            authorized_shop.message_post(body=message, message_type='notification')
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Warehouses synced successfully. Imported %d warehouses from %d pages.') % (total_synced, total_pages or page),
                    'type': 'success',
                }
            }
                
        except Exception as e:
            raise ValidationError(_('Warehouse sync failed: %s') % str(e))
    
    @api.model
    def _process_warehouses_data(self, warehouses_data, authorized_shop):
        """Process warehouses data and create/update warehouses in Odoo"""
        total_count = 0
        
        for warehouse_data in warehouses_data:
            # Create or update warehouse
            self._create_or_update_warehouse(warehouse_data, authorized_shop)
            total_count += 1
        
        return total_count
    
    @api.model
    def _create_or_update_warehouse(self, warehouse_data, authorized_shop):
        """Create or update a single warehouse"""
        warehouse_code = warehouse_data.get('warehouse_code')
        
        if not warehouse_code:
            return None
        
        # Find existing warehouse by warehouse_code and shop
        existing_warehouse = self.search([
            ('warehouse_code', '=', warehouse_code),
            ('authorized_shop_id', '=', authorized_shop.id)
        ], limit=1)
        
        # Prepare warehouse values
        warehouse_vals = {
            'warehouse_name': warehouse_data.get('warehouse_name', f"Warehouse {warehouse_code}"),
            'warehouse_code': warehouse_code,
            'country_code': warehouse_data.get('country_code', authorized_shop.country_code),
            'town_code': warehouse_data.get('town_code'),
            'area_code': warehouse_data.get('area_code'),
            'city_code': warehouse_data.get('city_code'),
            'division_id': warehouse_data.get('division_id'),
            'zip_code': warehouse_data.get('zip_code'),
            'platform_name': warehouse_data.get('platform_name'),
            'multi_channel': str(warehouse_data.get('multi_channel', '')).upper() == 'TRUE',
            'authorized_shop_id': authorized_shop.id,
            'sync_status': 'synced',
            'last_sync_date': fields.Datetime.now(),
        }
        
        # Parse latitude and longitude if available
        try:
            if warehouse_data.get('latitude'):
                warehouse_vals['latitude'] = float(warehouse_data.get('latitude'))
        except (ValueError, TypeError):
            pass
            
        try:
            if warehouse_data.get('longitude'):
                warehouse_vals['longitude'] = float(warehouse_data.get('longitude'))
        except (ValueError, TypeError):
            pass
        
        if existing_warehouse:
            # Update existing warehouse
            existing_warehouse.write(warehouse_vals)
            return existing_warehouse
        else:
            # Create new warehouse
            return self.create(warehouse_vals)
