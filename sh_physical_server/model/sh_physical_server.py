#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)

class sh_physical_server(models.Model):

    _name = "sh.physical_server"
    _description = "sh.physical_server"

    name = fields.Char( required=True, string="Name",  help="")
    provider = fields.Many2one(comodel_name="sh.cloud.provider", string="Provider")
    label = fields.Char( string="Label" )
    ram_size = fields.Char( string="RAM",  help="")
    disk_size = fields.Char( string="SSD",  help="")
    processor_core = fields.Char( string="Cores",  help="")
    ip = fields.Char( string="Internal Ip",  help="")
    ssh_host = fields.Char( string="SSH Ip/Host",  help="")
    port = fields.Char( string="Port",  help="")
    user = fields.Char( string="User",  help="")
    password = fields.Char( string="Password",  help="")
    is_busy = fields.Boolean( string="Busy",  help="")
    
    owner = fields.Many2many(comodel_name="res.users", string="User Owner",  help="")