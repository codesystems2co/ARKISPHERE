# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from uuid import uuid4
import markupsafe
import json
import requests

import logging
_logger = logging.getLogger(__name__)



class loyalty_card(models.Model):
    _inherit = 'loyalty.card'

    @api.model
    def _generate_code(self):
        """
        Barcode identifiable codes.
        """
        return '044' + str(str(uuid4())[7:-18]).replace('-','').upper()

    @api.model_create_multi
    def create(self, vals_list):
        loyalty_card = super().create(vals_list)

        for record in loyalty_card:
            if record.company_id.meta_coupon_information:
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                sharable = str(base_url) + str('/shop') 
                model_id = record.env['ir.model'].search_read([('model','=','loyalty.card')],['id','model'], limit=1)[0]
                filter = [  
                            ('name','=','whatsapp_coupon_information'),
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
                if record.partner_id.mobile:
                    meta_to_phone_number= str(record.partner_id.mobile)
                else:
                    meta_to_phone_number = str(record.partner_id.phone)
                
                expiration = None
                if record.expiration_date:                
                    expiration = _('Before ') + str(record.expiration_date)
                else:
                    expiration = _('has not expiration')

                _payload = {
                                'meta_phone_number': str(record.company_id.meta_phone_number),
                                'meta_access_token': str(record.company_id.meta_access_token),

                                'meta_message_type': mail_template.meta_type,

                                'meta_to_phone_number': meta_to_phone_number,

                                'meta_template_name': rendered_template[record.id]['name'],
                                'meta_template_lenguage_code': rendered_template[record.id]['lang'],
                                'meta_header_title': _('Promotional Discount'),
                                                                
                                'meta_message_text':text,                                
                                'meta_preview_url': mail_template.meta_preview_url,
                                
                                'odoo_record_company': str(record.company_id.name),
                                'odoo_model_name': record._name,
                                'odoo_record_name':record.code,
                                'odoo_preview_url':'http://localhost',
                                'odoo_record_partner_name': record.partner_id.name,
                                
                                'odoo_record_coupon_code': record.code,
                                'odoo_record_coupon_code_expiration_date': expiration,
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
                                'meta_is_whatsapp': True,
                                'meta_has_error': True,
                                'meta_error_message': response_values['error']['message'],
                                'meta_error_type': response_values['error']['type'],
                                'meta_error_code': response_values['error']['code'],
                                'meta_ferror_btrace_id': response_values['error']['fbtrace_id'],
                                #'author_id':int(record.user_id.partner_id.id),
                                'model': record._name,
                                'res_id': record.id,
                                'message_type': str('comment'),
                                'record_name': str(record.program_id.name) + str(' - ') + str(record.code),
                                'body': str(response_values['error']['message']),
                                }
                    
                    mail_message = record.env['mail.message'].create(values)            
                else:
                    if 'messages' in response_values:
                        values = {
                                    'meta_is_whatsapp': True,
                                    'meta_has_error': False,
                                    'meta_message_id': response_values['messages'][0]['id'],
                                    'model': record._name,
                                    'res_id': record.id,
                                    'message_type': str('comment'),
                                    'record_name': str(record.program_id.name) + str(' - ') + str(record.code),
                                    'body': str("WHATSAPP") + str("\n\n") + str(text),
                                }
                        mail_message = record.env['mail.message'].create(values)
            
        
        return loyalty_card