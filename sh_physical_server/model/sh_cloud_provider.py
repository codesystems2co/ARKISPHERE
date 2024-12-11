from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class hetzner(models.Model):
    _name = "sh.cloud.provider"

    name = fields.Char(string='Name')
    token = fields.Char(string="Token")
    state = fields.Boolean(string='State')
    _type = fields.Selection(string="Type", selection=[('server','Hetzner Server'),('s3','Hetzner Storage'),('goo_drive','Google Drive')], default="server")
    credentials = fields.Binary(string='Credentials')
    credentials_filename = fields.Char()
    _default = fields.Boolean(string='Default')    

    #@api.onchange('_default')
    #def _onchange__default(self):
    #    defaults = self.env['sh.cloud.provider'].sudo().search_read([('_default','=',True)])
#
    #    _logger.warning('_default_onchange defaults >>')
    #    _logger.warning(defaults)
#
    #    if defaults:
    #        raise ValidationError(_('Already exist a default server. Kindly, switch of and try again.'))