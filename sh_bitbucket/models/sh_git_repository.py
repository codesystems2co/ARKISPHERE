#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
from odoo import http
import sys
import logging
import time
import os
_logger = logging.getLogger(__name__)


class sh_git_repository(models.Model):

    _inherit = "sh.git_repository"
    _description = "sh.git_repository"
