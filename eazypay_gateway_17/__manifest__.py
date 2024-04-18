# -*- coding: utf-8 -*-
{
    'name': "eazypay_gateway_17",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'payment'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
        'data/payment_acquirers.xml',
        'views/payment_acquirer_views.xml',

    ],
    'assets': {
        'web.assets_frontend': [
            'eazypay_gateway_17/static/src/js/payment_form.js',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

