#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _

class sh_development(models.Model):

    _name = "sh.development"
    _description = "sh.development"


    name = fields.Char(string="Name")
    stage = fields.Many2one(comodel_name="sh.stage",  inverse_name="developments",  string="Stage",  help="")
    branches = fields.Many2one(comodel_name="sh.git_branch",  string="Branches",  help="")
