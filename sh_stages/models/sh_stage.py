#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo import http
import werkzeug

class sh_stage(models.Model):

    _name = "sh.stage"
    _description = "Repository Stages"

    name = fields.Char(string="Name")

    is_production = fields.Boolean( string="For Production",  help="")
    is_development = fields.Boolean( string="For Development",  help="")
    production = fields.Many2one(comodel_name="sh.production",  inverse_name="stage",  string="Production",  help="")
    developments = fields.One2many(comodel_name="sh.development", inverse_name="stage",  string="Developments",  help="")
    repository = fields.Many2one(comodel_name="sh.git_repository", string="Repository",  help="")

    def get_repository_stages(self):
        repository_id = None
        if('repository' in http.request.params):
            repository_id = http.request.params['repository']
        if(repository_id):
            if(int(repository_id)>0):
                return self.search([('repository','=',int(repository_id))])
        else:
            return werkzeug.utils.redirect('/my/servers')
    
    def get_production(self):
        pass