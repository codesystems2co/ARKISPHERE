# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import markupsafe
import json
import requests
import logging
_logger = logging.getLogger(__name__)

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    def _action_done(self):
        action_done = super()._action_done()
        
        for record in self:
            if record.company_id.meta_delivery_confirmation:
                if record.state == 'done':
                    model_id = record.env['ir.model'].search_read([('model','=','stock.picking')],['id','model'], limit=1)[0]
                    filter = [  
                                ('name','=','whatsapp_shipping'),
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

                    _payload = {
                                    'meta_phone_number': str(record.company_id.meta_phone_number),
                                    'meta_access_token': str(record.company_id.meta_access_token),

                                    'meta_message_type': mail_template.meta_type,

                                    'meta_to_phone_number': meta_to_phone_number,

                                    'meta_template_name': rendered_template[record.id]['name'],
                                    'meta_template_lenguage_code': rendered_template[record.id]['lang'],
                                    'meta_header_title': _('Delivery Confirmed'),

                                    'odoo_record_company': str(record.company_id.name),
                                    'meta_message_text':text,

                                    'odoo_model_name': record._name,
                                    'odoo_record_name':record.name,
                                    'odoo_record_partner_name': record.partner_id.name,

                                    'meta_preview_url': mail_template.meta_preview_url,
                                    'odoo_preview_url':'http://localhost',                                    
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

        return action_done      
