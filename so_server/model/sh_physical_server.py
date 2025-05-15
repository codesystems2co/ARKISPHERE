#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)

class sh_physical_server(models.Model):

    _inherit = "sh.physical_server"
    _description = "sh.physical_server"

    # remaining capacity
    def _ram_size_used(self):
        total_ram_remaining = 0.0
        for record in self:
            so_servers = request.env['so.server'].sudo().search([('physical_server','=',record.id), ('id','!=',record.so_server.id), ('id','!=',record.so_server.id)])            
            for so_server in so_servers:
                total_ram_remaining += float(so_server.ram_size)
            record.ram_size_used = float(total_ram_remaining)

    ram_size_used = fields.Float( string="Ram Remaining",  help="", readonly=True, compute="_ram_size_used")

    def _disk_size_used(self):
        total_disk_remaining = 0.0
        for record in self:
            so_servers = request.env['so.server'].sudo().search([('physical_server','=',record.id), ('id','!=',record.so_server.id)])            
            for so_server in so_servers:
                total_disk_remaining += float(so_server.disk_size)
            record.disk_size_used = float(total_disk_remaining)

    disk_size_used = fields.Float( string="Disk Remaining",  help="", readonly=True, compute="_disk_size_used")

    # remaining capacity
    def _ram_size_available(self):
        for record in self:
            _logger.warning(float(record.so_server.id))
            record.ram_size_available = float(record.so_server.ram_size) - float(record.ram_size_used) 
            return record.ram_size_available

    ram_size_available = fields.Float( string="Ram Available",  help="", readonly=True, compute="_ram_size_available")

    def _disk_size_available(self):
        for record in self:
            record.disk_size_available = float(record.so_server.disk_size) - float(record.disk_size_used) 
            return record.disk_size_available

    disk_size_available = fields.Float( string="Disk Available",  help="", readonly=True, compute="_disk_size_available")
    
    so_server = fields.One2many(comodel_name="so.server", inverse_name="physical_server", string="Operating System Server", help="")