#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _

class sh_production(models.Model):

    _name = "sh.production"
    _description = "sh.production"


    name = fields.Char(string="Name")
    stage = fields.Many2one(comodel_name="sh.stage",  inverse_name="production",  string="Stage",  help="")
    branch = fields.Many2one(comodel_name="sh.git_branch",  inverse_name="production",  string="Branch",  help="")
