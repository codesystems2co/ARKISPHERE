#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _

class kuber_docker_image(models.Model):

    _name = "kuber.docker_image"
    _description = "Docker Image"
    name = fields.Char( required=True, string="Name",  help="")
    version = fields.Char( string="Version",  help="")

    kuber_deploy = fields.Many2one(comodel_name="kuber.deploy",  string="Kuber deploy",  help="")