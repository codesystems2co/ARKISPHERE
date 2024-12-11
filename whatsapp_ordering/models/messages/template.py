# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import markupsafe
import logging
_logger = logging.getLogger(__name__)



class message_template(models.Model):
    # represented as message template
    # https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-message-templates
    _inherit = 'mail.template'

    meta_is_whatsapp = fields.Boolean(string="Whatsapp")
    meta_type = fields.Selection([
                                    ('text','Text'),
                                    ('template','Template')
                                 ], string="Type", default="text", readonly=False)
    meta_template_subtype = fields.Selection([  
                                                # Multitemplates with different components
                                                # https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-message-templates
                                                ('text','Text'),
                                                ('coupon_code','Coupon Code')
                                             ], string="Subtype", default="text", readonly=True)
    
    meta_preview_url = fields.Boolean(string="Preview URL", default=False, help="Send object sharable link if available")

    @api.onchange('meta_preview_url')
    def check_meta_preview_url(self):
        for record in self:
            if record.model_id.model == str('sale.order'):
                record.meta_preview_url = True
                pass
            else:
                record.meta_preview_url = False
                return  {
                            'type': 'ir.actions.client',
                            'tag':'display_notification',
                            'params': {
                                        'title':_('URL Preview'),
                                        'message':_('This feature is not available')
                                      }
                        }