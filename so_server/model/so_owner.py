#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _

class so_owner(models.Model):

    _name = "so.owner"
    _description = "Server Owner"
    #_inherit = "so.owner"
    _table = "res_partner"


    name = fields.Char( required=True, string="Name",  help="")
    is_autor = fields.Boolean( string="Is autor",  help="", default=True)
    so_servers = fields.One2many(comodel_name="so.server",  inverse_name="owner",  string="Servers",  help="")