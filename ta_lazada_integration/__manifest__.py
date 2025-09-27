# -*- coding: utf-8 -*-
{
    'name': 'TA Lazada Integration',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Integrate Odoo with Lazada marketplace for product and order synchronization',
    'description': """
        TA Lazada Integration
        ====================
        
        This module provides integration between Odoo and Lazada marketplace:
        
        * Product synchronization (create, update, delete)
        * Order synchronization and management
        * Category mapping
        * Inventory synchronization
        * Automatic order import via cron jobs
        * Multi-store support
        
        Features:
        ---------
        * Sync products from Odoo to Lazada
        * Import orders from Lazada to Odoo
        * Manage product categories
        * Track inventory levels
        * Handle order status updates
        * Support for multiple Lazada stores
    """,
    'depends': [
        'base',
        'sale',
        'stock',
        'product',
        'account',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/ta_lazada_security.xml',
        # Load Authorized Shop action before it's referenced in config views
        'views/ta_lazada_authorized_shop_views.xml',
        'views/ta_lazada_config_views.xml',
        'views/ta_lazada_product_views.xml',
        'views/ta_lazada_order_views.xml',
        'views/ta_lazada_category_views.xml',
        'views/ta_lazada_campaign_views.xml',
        'views/ta_lazada_warehouse_views.xml',
        'views/oauth_templates.xml',
        'views/ta_lazada_menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'images': ['static/description/banner.png'],
    'price': 0,
    'currency': 'USD',
}
