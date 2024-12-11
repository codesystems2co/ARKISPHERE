# -*- coding: utf-8 -*-
{
    'name': "whatsapp_ordering",
    'summary': "",    
    'description': """ """,
    'author': "ROCKSCRIPTS",
    'website': "",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'mail', 'sale', 'stock', 'account', 'loyalty', 'website', 'payment', 'product', 'website_sale'],
    'data': [
                'views/base/res_company.xml',
                'views/messages/template.xml',
                'views/messages/message.xml',
                'views/website/form_checkout.xml',
                'views/website/portal_account.xml',
                'views//base/menu.xml',


                'data/message_template.xml',
            ],
    'assets':   {
                    'web.assets_frontend':[
                                            '/whatsapp_ordering/static/src/css/website.css',
                                          ],

                }
}