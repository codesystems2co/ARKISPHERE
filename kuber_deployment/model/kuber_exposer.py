#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)

class kuber_exposer(models.Model):

    _name = "kuber.exposer"
    _description = "Kuber Exposer"

    name = fields.Char( required=True, string="Name",  help="")
    port = fields.Char( required=True, string="Assigned Port",  help="")    
    cluster_selector = fields.Char( string="Cluster Selector", default=str('not assigned'), help="")
    cluster_selector_type = fields.Char( string="Cluster Selector Type", default=str('not assigned'), help="")    
    selector_label = fields.Char( string="Tier", default=str('not assigned'), help="")   
    
    def _git_repository_name(self):
        if(self.git_branch):
            self.git_repository_name = str(self.git_branch.repository.name)
        else:
            self.git_repository_name = str('not assigned')
    
    def _git_physical_server_ip(self):      
        for record in self:  
            if(record.physical_server):
                record.ip = str(record.physical_server.ip)
            else:
                record.ip = str('XXX.XXX.XXX.XXX')

    git_repository_name = fields.Char( string="Repository", compute='_git_repository_name', default="not assigned")
    git_branch = fields.Many2one(comodel_name="sh.git_branch",  string="Git Branch",  help="")
    ip = fields.Char( string="IP", compute='_git_physical_server_ip', default="XXX.XXX.XXX.XXX")
    domain = fields.Char( string="Domain", placeholder=".com")
    physical_server = fields.Many2one(comodel_name="sh.physical_server",  string="Physical Server",  help="")

    @api.onchange('git_branch')
    def _git_repository_name(self):
        for record in self:
            if(record.git_branch):
                record.git_repository_name = str(record.git_branch.repository.name)
            else:
                record.git_repository_name = str('not assigned')