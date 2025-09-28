{
    'name': 'TikTok Business Connector',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Connect with TikTok Business API',
    'description': """
        TikTok Business Connector
        ========================
        This module provides integration with TikTok Business API for:
        - Authorization and token management
        - Business and advertiser information
        - Advertising campaign management
        - Ad group management
        - Ad management
        - Ad creative management
        - Ad report management
        - Ad insight management
        - Ad insight report management
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base_setup'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/tiktok_business_account_views.xml',
        'views/tiktok_advertiser_views.xml',
        'views/tiktok_campaign_views.xml',
        'views/tiktok_ad_group_views.xml',
        'views/tiktok_ad_views.xml',
        'views/tiktok_menus.xml',
        'reporting/tiktok_bc_report_views.xml',
        'wizards/views/wizard_sync_advertiser.xml',
        'wizards/views/wizard_sync_campaign.xml',
        'wizards/views/wizard_sync_ad_group.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
