#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)

class sh_physical_server(models.Model):

    _inherit = "sh.physical_server"
    _description = "Physical Server"

    kuber_exposer = fields.Many2one(comodel_name="kuber.exposer",  inverse_name="physical_server",  string="Physical Server",  help="")