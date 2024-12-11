# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request

import markupsafe
from urllib.parse import urlparse, parse_qs

import logging
_logger = logging.getLogger(__name__)



class product_template(models.Model):
    _inherit = "product.template"

    @api.model_create_multi
    def create(self, vals_list):
        company_id = self.env['ir.http'].session_info().get('user_companies')['current_company']
        company_id = self.env['res.company'].browse(int(company_id))
        product_template_id = super().create(vals_list)
        for record in product_template_id:
            if company_id.meta_product_creation:
                if record.categ_id:
                    product_template_ids = record.env['product.template'].search_read([('categ_id','=',int(record.categ_id.id)),('id','!=',int(record.id))], ['id'])
                    if product_template_ids:
                        tmpl_ids = []
                        for _product_template_id in product_template_ids:
                            tmpl_ids.append(_product_template_id['id'])

                        product_product_ids = record.env['product.product'].search_read([('product_tmpl_id','in',tmpl_ids)],['id'])
                        if product_product_ids:
                            prod_prod_ids = []
                            for product_product_id in product_product_ids:
                                prod_prod_ids.append(str(product_product_id['id']))

                            query = """SELECT  DISTINCT order_partner_id AS contact_id  FROM sale_order_line WHERE state='sale' AND product_id IN (""" + str(','.join(prod_prod_ids)) + """)"""
                            request.cr.execute(query)
                            order_partner_ids = request.cr.dictfetchall()
                            _logger.info('order_partner_ids::: >')
                            _logger.info(order_partner_ids)
                            if order_partner_ids:
                                for order_partner_id in  order_partner_ids:
                                    contact = record.env['res.partner'].browse(int(order_partner_id['contact_id']))

                                    model_id = record.env['ir.model'].search_read([('model','=','product.template')],['id','model'], limit=1)[0]

                                    filter = [  
                                                ('name','=','whatsapps_product_creation'),
                                                ('meta_is_whatsapp','=',True),
                                                ('model_id','=',int(model_id['id']))
                                            ]

                                    #mail_template = record.env['mail.template'].search_read(filter,
                                    #                                                        ['id']
                                    #                                                        , limit=1)[0]
                                    #
                                    #mail_template  = record.env['mail.template'].browse(int(mail_template['id']))
                                    # auth
                                    service = whatsapp(meta_path='messages')
                                    service.meta_phone_number = str(company_id.meta_phone_number)
                                    service.meta_access_token = str(company_id.meta_access_token)

                                    # init message
                                    service.meta_message.messaging_product = str('whatsapp')
                                    if contact.mobile:
                                        service.meta_message.to_phone_number = str(contact.mobile)
                                    else:
                                        service.meta_message.to_phone_number = str(contact.phone)
                                    service.meta_message.recipient_type = 'individual'
                                    service.meta_message._type = 'interactive'    
                                    service.meta_message._interactive = {
                                                                            "type": "cta_url",
                                                                            "header": {
                                                                            "type": "text",
                                                                            "text": record.name
                                                                            },
                                                                            "body": {
                                                                            "text": _('Maybe you like this new product published recently')
                                                                            },
                                                                            "footer": {
                                                                            "text": record.categ_id.name
                                                                            },
                                                                            "action": {
                                                                            "name": "cta_url",
                                                                            "parameters": {
                                                                                "display_text": _('Shop Now'),
                                                                                "url": record.website_url
                                                                            }
                                                                            }
                                                                        }
                                    
                                    service.meta_payload = service.meta_message.body()

                                    _logger.warning("META payload::")
                                    _logger.warning(service.meta_payload)

                                    response = service.do_request()

                                    _logger.warning("META response::")
                                    _logger.warning(response.json())
                                    
        return product_template_id