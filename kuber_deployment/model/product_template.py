#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
import logging
import os
_logger = logging.getLogger(__name__)

class kuber_deploy(models.Model):

    _inherit = "product.template"
    _description = "Product Template"
    
    kuber_deployments = fields.Many2one(comodel_name="kuber.deploy",  inverse_name="git_repository",  string="Deployments",  help="") 