# -*- coding: utf-8 -*-
{
    'name': 'YonSuite Integration',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Integration with YonSuite API for sales orders and authentication',
    'description': """
        YonSuite Integration Module
        ===========================
        
        This module provides integration with YonSuite API including:
        - Access token management with automatic refresh
        - Sales order synchronization
        - Configuration settings for API credentials
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base', 'sale', 'sale_management'],
            'data': [
                'security/ir.model.access.csv',
                'data/cron_data.xml',
                'wizard/yonsuite_actions_views.xml',
                'views/yonsuite_partner_views.xml',
                'views/yonsuite_admindept_views.xml',
                'views/yonsuite_orgunit_views.xml',
                'views/yonsuite_getallorgdept_views.xml',
                'views/yonsuite_salearea_views.xml',
                'views/yonsuite_store_views.xml',
                'views/yonsuite_vendor_views.xml',
                'views/yonsuite_product_views.xml',
                'views/yonsuite_order_views.xml',
                'views/yonsuite_order_line_views.xml',
                'views/res_config_settings_views.xml',
                'views/yonsuite_brand_views.xml',
                'views/yonsuite_unit_views.xml',
                'views/yonsuite_warehouse_views.xml',
                'views/yonsuite_carrier_views.xml',
                'views/yonsuite_staff_views.xml',
                'views/yonsuite_country_views.xml',
                'views/yonsuite_currency_views.xml',
                'views/yonsuite_management_class_views.xml',
                'views/yonsuite_purchase_class_views.xml',
                'views/yonsuite_sale_class_views.xml',
                'views/yonsuite_menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
