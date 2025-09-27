from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import time


class TaLazadaCategory(models.Model):
    _name = 'ta.lazada.category'
    _description = 'Lazada Category'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char('Category Name', required=True)
    lazada_category_id = fields.Char('Lazada Category ID', required=True)
    parent_id = fields.Many2one('ta.lazada.category', 'Parent Category')
    child_ids = fields.One2many('ta.lazada.category', 'parent_id', 'Child Categories')
    authorized_shop_id = fields.Many2one('ta.lazada.authorized.shop', 'Authorized Shop', required=True)
    
    # Additional Lazada category information
    category_path = fields.Char('Category Path', help='Full category path in Lazada')
    category_level = fields.Integer('Category Level', default=1)
    is_mandatory = fields.Boolean('Is Mandatory', default=False)
    
    
    # Status
    active = fields.Boolean('Active', default=True)
    is_leaf = fields.Boolean('Is Leaf', default=False)
    is_var = fields.Boolean('Is Var', default=False)
    
    # Sync Information
    last_sync_date = fields.Datetime('Last Sync Date')
    sync_status = fields.Selection([
        ('pending', 'Pending'),
        ('synced', 'Synced'),
        ('failed', 'Failed'),
    ], string='Sync Status', default='pending')
    
    _sql_constraints = [
        ('lazada_category_id_unique', 'unique(lazada_category_id, authorized_shop_id)', 'Lazada Category ID must be unique per authorized shop'),
    ]

    @api.model
    def import_from_lazada_for_shop(self, authorized_shop):
        """Import categories from Lazada for a specific shop"""
        if not authorized_shop.access_token:
            raise ValidationError(_('Shop must have valid access token'))
        
        try:
            # Get category tree from Lazada
            endpoint = '/category/tree/get'
            params = {
                'access_token': authorized_shop.access_token,
                'timestamp': str(int(time.time() * 1000)),
            }
            if authorized_shop.country_code == 'VN':
                params['language_code'] = 'vi_VN'

            response = authorized_shop._make_api_request(endpoint, params, 'GET')
            
            if response.get('code') == '0' and response.get('data'):
                categories_data = response['data']
                sync_count = self._process_category_tree(categories_data, authorized_shop, None, {})
                
                # Add note to shop about sync result
                message = _('Category sync completed successfully. Imported %d categories from Lazada.') % sync_count
                authorized_shop.message_post(body=message, message_type='notification')
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Categories synced successfully. Imported %d categories.') % sync_count,
                        'type': 'success',
                    }
                }
            else:
                error_msg = response.get('message', 'Failed to fetch categories')
                raise ValidationError(_('Category sync failed: %s') % error_msg)
                
        except Exception as e:
            raise ValidationError(_('Category sync failed: %s') % str(e))
    
    @api.model
    def _process_category_tree(self, categories_data, authorized_shop, parent_category=None, category_cache=None):
        """Process category tree and create/update categories in Odoo recursively"""
        if category_cache is None:
            category_cache = {}
        
        total_count = 0
        for category_data in categories_data:
            # Create or update current category
            odoo_category = self._create_or_update_category(category_data, authorized_shop, parent_category, category_cache)
            total_count += 1
            
            # Process children if they exist
            children = category_data.get('children', [])
            if children:
                child_count = self._process_category_tree(children, authorized_shop, odoo_category, category_cache)
                total_count += child_count
        
        return total_count
    
    @api.model
    def _create_or_update_category(self, category_data, authorized_shop, parent_category=None, category_cache=None):
        """Create or update a single category"""
        if category_cache is None:
            category_cache = {}
            
        lazada_id = category_data.get('category_id')
        
        if not lazada_id:
            return None
        
        # Create cache key for this shop and lazada_id
        cache_key = f"{authorized_shop.id}_{lazada_id}"
        
        # Check cache first
        if cache_key in category_cache:
            return category_cache[cache_key]
        
        # Find existing category by Lazada ID and shop
        existing_category = self.search([
            ('lazada_category_id', '=', lazada_id),
            ('authorized_shop_id', '=', authorized_shop.id)
        ], limit=1)
        
        # Ensure name is not None or empty
        category_name = category_data.get('name') or f"Category {lazada_id}"
        
        # Calculate category level and path
        category_level = 1
        if parent_category:
            category_level = parent_category.category_level + 1
        
        category_path = category_name
        if parent_category and parent_category.category_path:
            category_path = f"{parent_category.category_path} > {category_name}"
        
        category_vals = {
            'name': category_name,
            'lazada_category_id': lazada_id,
            'is_leaf': category_data.get('leaf', False),
            'is_var': category_data.get('var', False),
            'authorized_shop_id': authorized_shop.id,
            'category_path': category_path,
            'category_level': category_level,
            'is_mandatory': category_data.get('is_mandatory', False),
            'sync_status': 'synced',
            'last_sync_date': fields.Datetime.now(),
        }
        
        if parent_category:
            category_vals['parent_id'] = parent_category.id
        
        if existing_category:
            # Update existing category
            existing_category.write(category_vals)
            category_cache[cache_key] = existing_category
            return existing_category
        else:
            # Create new category
            new_category = self.create(category_vals)
            category_cache[cache_key] = new_category
            return new_category
    