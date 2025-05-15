#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _

import logging, sys
_logger = logging.getLogger(__name__)

class sh_git_branch(models.Model):

    _inherit = "sh.git_branch"
    _description = "sh.git_branch"