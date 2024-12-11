#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _

class sh_git_branch(models.Model):

    #_name = "sh.git_branch"
    _description = "sh.git_branch"

    _inherit = "sh.git_branch"


    production = fields.One2many(comodel_name="sh.production",  inverse_name="branch",  string="Production",  help="")
    development = fields.One2many(comodel_name="sh.development",  inverse_name="branches",  string="Development",  help="")
    