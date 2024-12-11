#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _

class sh_git_autor(models.Model):

    _name = "git.autor"
    _description = "git.autor"
    #_inherit = "res.partner"
    _table = "res_partner"

    access_token = fields.Char( string="Access Token",  help="https://github.com/settings/tokens")
    is_autor = fields.Boolean( string="Is autor",  help="", default=True)
    is_collaborator = fields.Boolean( string="Is collaborator",  help="")
    platform = fields.Selection( [('github','Github'), ('gitlab','Gitlab'), ('odoo','Odoo')], string="Platform",  help="")
    identifier = fields.Char( string="Identifier",  help="")
    name = fields.Char( string="Autor",  help="")
    username = fields.Char( string="Username",  help="")
    _gpassword = fields.Char( string="Git Password",  help="")
    html_url = fields.Char( string="Html url",  help="")

    repositories = fields.Many2many(comodel_name="sh.git_repository",  inverse_name="autor",  string="Repositories",  help="")


    def auth_connect(self, params):
        return params
        pass


    def get_repository(self, ):
        pass


    def get_repository_branches(self, ):
        pass


    def get_branch_commits(self, ):
        pass      

    def check_github_password(self, _gpassword):
        autor = self.search([
                                ('id','=',self.env.user.partner_id.id),
                                ('_gpassword','=',_gpassword)
                            ])
        if autor : return True
        else : return False
        