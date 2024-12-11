#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo import http
import logging
_logger = logging.getLogger(__name__)

class sh_git_repository(models.Model):

    _inherit = "sh.git_repository"
    _description = "sh.git_repository"

    so_server = fields.Many2one(comodel_name="so.server",  inverse_name="git_repositories",  string="Operating System") #, domain=[('owner', '=', lambda self: self.owner.id)],  help="")

    