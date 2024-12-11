#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)

class sh_product_template(models.Model):
    _inherit = 'product.template'