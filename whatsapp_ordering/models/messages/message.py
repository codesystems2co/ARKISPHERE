# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class message(models.Model):
    _inherit = 'mail.message'

    meta_is_whatsapp = fields.Boolean(string="Whatsapp")
    # errors fields
    meta_has_error = fields.Boolean(string="Delivery Error", readonly=True)
    meta_error_message = fields.Char(string="Description", readonly=True)
    meta_error_type = fields.Char(string="Type", readonly=True)
    meta_error_code = fields.Char(string="Code", readonly=True)
    meta_ferror_btrace_id = fields.Char(string="Trace Id", readonly=True)

    meta_message_id = fields.Char(string="Message", readonly=True)