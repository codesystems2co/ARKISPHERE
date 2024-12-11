#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
from dateutil.relativedelta import *

import logging
_logger = logging.getLogger(__name__)

class sh_sale_order_line(models.Model):
    _inherit = "sale.order.line"

    is_subscription = fields.Boolean("Is Subscription", default=False)
    multiplier_factor_number = fields.Integer("* Period", default=False)
    multiplier_factor_label = fields.Char("Period", default=False)
    periods_billed = fields.Char("Period(s) Billed", default=0)
    so_server = fields.Many2one(comodel_name="so.server",  inverse_name="order_line",  string="S.O Server",  help="")

    def _last_period(self):
        for record in self:
            record.last_period = None
            _order = record.env["sale.order"].search([('id','=',record.order_id.id)], limit=1)
            if(not record.last_period and record.is_subscription and _order.date_order):
                record.last_period = _order.date_order
                record.last_period += relativedelta(months=+(int(record.multiplier_factor_number)*int(record.periods_billed)))
            #return record.last_period

    last_period = fields.Datetime("Last Period", compute='_last_period')

    def _next_period(self):
        for record in self:
            record.next_period = None
            if(record.is_subscription):
                if(record.last_period):
                    record.next_period = record.last_period + relativedelta(months=+(int(record.multiplier_factor_number)))

        #return self.next_period

    next_period = fields.Datetime("Next Period", compute='_next_period')  

    