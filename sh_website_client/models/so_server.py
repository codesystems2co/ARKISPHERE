#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
from odoo import http

class so_server(models.Model):

    _inherit = "so.server"

    order_line = fields.Many2one(comodel_name="sale.order.line",  inverse_name="so_server",  string="Sale Order Line",  help="")
    sale_order = fields.Many2one(comodel_name="sale.order",  related="order_line.order_id",  string="Sale Order",  help="")

    def get_current_server(self):
        so_server_id = None
        if('server' in http.request.params):
            so_server_id = http.request.params['server']
        if(so_server_id):
            return so_server_id