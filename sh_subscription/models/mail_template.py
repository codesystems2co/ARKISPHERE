from odoo import models, fields

class MailTemplate(models.Model):
    _inherit = 'mail.template'
 
    meta_is_whatsapp = fields.Boolean(
        string='Is WhatsApp Template',
        default=False,
        help='Technical field to identify WhatsApp-specific templates'
    ) 