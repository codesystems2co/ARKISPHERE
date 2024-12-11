#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _

class sh_git_permission(models.Model):

    _name = "sh.git_permissions"
    _description = "sh.git_permissions"

    name = fields.Char( string="Name",  help="")
    pull = fields.Boolean( string="Pull",  help="")
    push = fields.Boolean( string="Push",  help="")
    admin = fields.Boolean( string="Admin",  help="")


    collaborator = fields.Many2one(comodel_name="git.collaborator",  string="Collaborator",  help="")
