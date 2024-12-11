#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _

class kuber_template(models.Model):

    _name = "kuber.template"
    _description = "Kuber Template"

    name = fields.Char( required=True, string="Name",  help="")
    _type = fields.Selection(       
                                string="Type",
                                selection=[
                                            ("namespace","Namespace"),
                                            ("secret","Secret"),
                                            ("deployment","Deployment"),
                                            ("service","Service"),
                                            ("pod","Pod"),
                                            ("volumen","Volumen"),
                                            ("volumen_claim","Volumen Claim"),
                                            ("ingress_controller","Ingress Controllers")
                                           ],  
                                help=""
                            )
    content = fields.Text( string="Content",  help="")
    kuber_deploy = fields.Many2many(comodel_name="kuber.deploy",  string="Kuber deploy",  help="")
    priority = fields.Integer(string="Priority")
    expose_public = fields.Boolean(string="Expose Public")
    expose_selector= fields.Char(string="App Selector")
    app_port = fields.Integer(string="App Port")

    def replace_tag(self, template, find, replace):
        return str(template).replace(find,replace)