#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _

class so_server(models.Model):

    _name = "so.server"
    _description = "so.server"

    name = fields.Char( required=True, string="Name",  help="")
    brand = fields.Char( string="Brand",  help="")

    ram_size = fields.Float( string="RAM",  help="")    
    ram_size_gb = fields.Char( string="RAM",  help="", default=0)

    disk_size = fields.Float( string="SSD",  help="")
    disk_size_gb = fields.Char( string="SSD",  help="", default=0)

    processor_core = fields.Float( string="Cores",  help="")
    processor_core_gb = fields.Char( string="Cores",  help="", default=0)


    def create_so(self, ):
        pass


    def update_so(self, ):
        pass


    def delete_so(self, ):
        pass


    def get_so_servers(self, _id=None):
        if(not _id):
            return self.search([('owner','=',self.env.user.partner_id.id)])
        else:
            return self.search([('owner','=',_id)])


    def update_ram_size(self, ):
        pass


    def update_disk_size(self, ):
        pass
        
    physical_server = fields.Many2one(comodel_name="sh.physical_server", string="Physical Server", help="")
    git_repositories = fields.Many2one(comodel_name="sh.git_repository", inverse_name="so_server", string="Repository", help="")
    owner = fields.Many2many(comodel_name="so.owner", inverse_name="so_servers", string="Owner", help="")