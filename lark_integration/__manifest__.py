{
    'name': 'Lark Integration',
    "summary": "Lark Integration",
    'version': "1.0.0",
    "license": "LGPL-3",
    "category": "Sales",
    'depends': ['base_setup'],
    'external_dependencies': {
        'python': [
            'lark-oapi',
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'security/lark_security.xml',
        'data/lark_cron.xml',
        'views/res_config_settings.xml',
        'views/lark_approval_views.xml',
        'views/lark_department_views.xml',
        'views/lark_contact_views.xml',
        'views/lark_file_views.xml',
        'views/lark_file_bitable_table_views.xml',
        'views/res_users_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'lark_integration/static/src/**/*',
        ],
    },
    "installable": True,
    'application': True,
}
