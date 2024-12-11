# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
import json
import requests
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
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

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

                            if order_partner_ids:
                                for order_partner_id in  order_partner_ids:
                                    contact = record.env['res.partner'].browse(int(order_partner_id['contact_id']))

                                    model_id = record.env['ir.model'].search_read([('model','=','product.template')],['id','model'], limit=1)[0]

                                    filter = [  
                                                ('name','=','whatsapps_product_creation'),
                                                ('meta_is_whatsapp','=',True),
                                                ('model_id','=',int(model_id['id']))
                                            ]

                                    mail_template = record.env['mail.template'].search_read(filter,
                                                                                            ['id']
                                                                                            , limit=1)[0]
                                    
                                    mail_template  = record.env['mail.template'].browse(int(mail_template['id']))

                                    rendered_template = mail_template._generate_template([record.id], ['name','lang','body_html'])     
                                    text = markupsafe.escape(rendered_template[record.id]['body_html']).striptags() 

                                    meta_to_phone_number = None
                                    if contact.mobile:
                                        meta_to_phone_number= str(contact.mobile)
                                    else:
                                        meta_to_phone_number = str(contact.phone)
                                        
                                    _payload = {
                                                    'meta_phone_number': str(company_id.meta_phone_number),
                                                    'meta_access_token': str(company_id.meta_access_token),

                                                    'meta_message_type': mail_template.meta_type,

                                                    'meta_to_phone_number': meta_to_phone_number,

                                                    'meta_template_name': rendered_template[record.id]['name'],
                                                    'meta_template_lenguage_code': contact.lang,
                                                    'meta_header_image_link': str(base_url) + str(record.website_url),
                                                                                    
                                                    'meta_message_text':text,                                
                                                    'meta_preview_url': mail_template.meta_preview_url,
                                                    
                                                    'odoo_record_company': str(company_id.name),
                                                    'odoo_model_name': record._name,
                                                    'odoo_record_name':record.name,
                                                    'odoo_preview_url':str(base_url) + str(record.website_url),
                                                    'odoo_record_partner_name': contact.name,
                                                    
                                                }
                
                                    _logger.info('BRIDGE - _payload')
                                    _logger.info(_payload)
                                    
                                    headers = {'Content-Type':'application/json'}
                                    response = requests.request("POST", url='http://localhost:8069/whatsapp/send_message', headers=headers, data=json.dumps(_payload))
                                    
                                    response_values = response.json()['result']

                                    _logger.info('BRIDGE - response_values')
                                    _logger.info(response_values)

                                    if 'error' in response_values:                    
                                        values = {
                                                    'meta_is_whatsapp':True,
                                                    'meta_has_error':True,
                                                    'meta_error_message':response_values['error']['message'],
                                                    'meta_error_type':response_values['error']['type'],
                                                    'meta_error_code':response_values['error']['code'],
                                                    'meta_ferror_btrace_id':response_values['error']['fbtrace_id'],
                                                    #'author_id':int(record.user_id.partner_id.id),
                                                    'model':record._name,
                                                    'res_id':record.id,
                                                    'message_type':str('comment'),
                                                    'record_name':str(record.name),
                                                    'body':str(response_values['error']['message']),
                                                }
                                        mail_message = record.env['mail.message'].create(values)
                                    else:
                                        if 'messages' in response_values:
                                            values = {
                                                        'meta_is_whatsapp':True,
                                                        'meta_has_error':False,
                                                        'meta_message_id':response_values['messages'][0]['id'],
                                                        'model':record._name,
                                                        'res_id':record.id,
                                                        'message_type':str('comment'),
                                                        'record_name':str(record.name),
                                                        'body':str("WHATSAPP") + str("\n\n") + str(text),
                                                    }
                                            mail_message = record.env['mail.message'].create(values)

        return product_template_id