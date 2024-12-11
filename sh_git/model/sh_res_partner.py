#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _

class sh_res_partner(models.Model):

    _inherit = "res.partner"
    # autor fields
    access_token = fields.Char( string="Access Token",  help="https://github.com/settings/tokens")
    is_autor = fields.Boolean( string="Is autor",  help="", default=True)
    is_collaborator = fields.Boolean( string="Is collaborator",  help="")
    platform = fields.Selection( [('github','Github'), ('gitlab','Gitlab'), ('odoo','Odoo')], string="Platform",  help="")
    identifier = fields.Char( string="Identifier",  help="")
    name = fields.Char( string="Autor",  help="")
    username = fields.Char( string="Username",  help="")
    _gpassword = fields.Char( string="Git Password",  help="")
    html_url = fields.Char( string="Html url",  help="")

    #collabrator fields
    name = fields.Char( string="Collaborator",  help="")
    is_collaborator = fields.Boolean( string="Is collaborator",  help="", default=True)    
    permission = fields.One2many(comodel_name="sh.git_permissions",  inverse_name="collaborator",  string="Permission",  help="")
    

    def get_current_autor_id(self):
        return self.env.user.partner_id.id