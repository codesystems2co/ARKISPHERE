#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _

class sh_git_collaborator(models.Model):

    _name = "git.collaborator"
    _description = "git.collaborator"
    _table = "res_partner"
    #_inherit = "res.partner"    

    name = fields.Char( string="Collaborator",  help="")
    is_collaborator = fields.Boolean( string="Is collaborator",  help="", default=True)
    permission = fields.One2many(comodel_name="sh.git_permissions",  inverse_name="collaborator",  string="Permission",  help="")
    username = fields.Char( string="Username",  help="")
    branches = fields.Many2many(comodel_name="sh.git_branch",  inverse_name="collaborators",  string="Repositories",  help="")