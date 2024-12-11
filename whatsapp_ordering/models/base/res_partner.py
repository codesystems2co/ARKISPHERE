# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import json
import requests

import markupsafe
import logging
_logger = logging.getLogger(__name__)



class res_partner(models.Model):
    _inherit = "res.partner"

    @api.model_create_multi
    def create(self, vals_list):
        contact = super().create(vals_list)
        company_id = self.env['ir.http'].session_info().get('user_companies')['current_company']
        company_id = self.env['res.company'].browse(int(company_id))

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url_sharable = str(base_url) + str('/my/home')

        for record in contact:
            if company_id.meta_account_creation:
                model_id = record.env['ir.model'].search_read([('model','=','res.partner')],['id','model'], limit=1)[0]
                filter = [  
                            ('name','=','whatsapp_new_contact'),
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
                if record.mobile:
                    meta_to_phone_number= str(record.mobile)
                else:
                    meta_to_phone_number = str(record.phone)

                _payload = {
                                'meta_phone_number': str(company_id.meta_phone_number),
                                'meta_access_token': str(company_id.meta_access_token),

                                'meta_message_type': mail_template.meta_type,

                                'meta_to_phone_number': meta_to_phone_number,

                                'meta_template_name': rendered_template[record.id]['name'],
                                'meta_template_lenguage_code': rendered_template[record.id]['lang'],
                                'meta_header_title': _('Welcome'),

                                'odoo_record_company': str(record.company_id.name),
                                'meta_message_text':text,
                                
                                'meta_preview_url': mail_template.meta_preview_url,

                                'odoo_model_name': record._name,

                                'odoo_record_name':record.name,
                                'odoo_record_mail':record.email,

                                'odoo_preview_url': str(url_sharable)
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
                                'body':str(response_values['error']['message'])
                                }
                    
                    mail_message = record.env['mail.message'].create(values)
                    _logger.info('contact - action_create mail_message')
                    _logger.info(mail_message)
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
                                    'body':str('WHATSAPP') + str("\n\n") + str(text)
                                }

                        mail_message = record.env['mail.message'].create(values)
                        _logger.info('contact - action_create mail_message')
                        _logger.info(mail_message)
        return contact