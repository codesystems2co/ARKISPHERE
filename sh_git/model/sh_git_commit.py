#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _

class sh_git_commit(models.Model):

    _name = "sh.git_commit"
    _description = "sh.git_commit"

    name = fields.Char( required=True, string="Name",  help="")
    sha = fields.Char( string="Sha",  help="")
    node_id = fields.Char( string="Node",  help="")
    url = fields.Char( string="Url",  help="")
    message = fields.Char( string="Message",  help="")
    username = fields.Char( string="Username",  help="")


    branch = fields.Many2one(comodel_name="sh.git_branch",  inverse_name="commits",  string="Branch",  help="")