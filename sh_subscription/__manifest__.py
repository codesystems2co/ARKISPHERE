# -*- coding: utf-8 -*-
{
    'name': "SH Subscription",

    'summary': """""",

    'description': """""",

    'author': "Alex Grisales Rivera",
    'website': "",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'web', 'account', 'website_sale', 'product', 'sale' , 'so_server', 'mail'],
    'data': [
                'views/product_template_attribute_value.xml',
                'views/sale_order.xml',
                'views/sale_order_line.xml',
                'views/account_move.xml',
                'views/account_move_line.xml',
                'static/src/qweb/variants.xml',
                'views/ir_cron.xml',                
                'data/mail_template.xml',
            ],
    'assets': {
                'web.assets_frontend': [
                                            'sh_subscription/static/src/css/frontend.css',
                                            'sh_subscription/static/src/js/website.js'
                                        ],
                },
}
