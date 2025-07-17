#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
from dateutil.relativedelta import *
from datetime import datetime
from datetime import date
from odoo.tools import float_is_zero, float_compare

import logging
_logger = logging.getLogger(__name__)

class sh_account_move_line(models.Model):
    _inherit = "account.move.line"

    def _multiplier_factor_number(self):
        for record in self:
            record.multiplier_factor_number = 1  # Default value
            if record.move_id and record.move_id.invoice_origin:
                _order = self.env["sale.order"].search([('name','=',record.move_id.invoice_origin)], limit=1)
                if _order and _order.order_line:
                    # Try to find matching sale order line by product first
                    _order_line = _order.order_line.filtered(
                        lambda line: line.product_id.id == record.product_id.id and line.is_subscription
                    )
                    if _order_line:
                        record.multiplier_factor_number = _order_line[0].multiplier_factor_number or 1

    multiplier_factor_number = fields.Integer("* Period", compute='_multiplier_factor_number', default=1)

    def _multiplier_factor_label(self):
        for record in self:
            record.multiplier_factor_label = "Monthly"  # Default value
            if record.move_id and record.move_id.invoice_origin:
                _order = self.env["sale.order"].search([('name','=',record.move_id.invoice_origin)], limit=1)
                if _order and _order.order_line:
                    # Try to find matching sale order line by product first
                    _order_line = _order.order_line.filtered(
                        lambda line: line.product_id.id == record.product_id.id and line.is_subscription
                    )
                    if _order_line:
                        record.multiplier_factor_label = _order_line[0].multiplier_factor_label or "Monthly"

    multiplier_factor_label = fields.Char("Period", compute='_multiplier_factor_label', default="Monthly")

    def _is_subscription(self):
        for record in self:
            record.is_subscription = False  # Default value
            if record.move_id and record.move_id.invoice_origin:
                _order = self.env["sale.order"].search([('name','=',record.move_id.invoice_origin)], limit=1)
                if _order and _order.order_line:
                    # Check if this product exists in any subscription line
                    subscription_lines = _order.order_line.filtered(
                        lambda line: line.product_id.id == record.product_id.id and line.is_subscription
                    )
                    if subscription_lines:
                        record.is_subscription = True
                        _logger.info("Found subscription line for product %s in order %s", record.product_id.name, _order.name)

    is_subscription = fields.Boolean("Is Subscription", compute='_is_subscription', default=False, store=True)    

    def _last_period(self):
        for record in self:
            record.last_period = None
            if record.move_id and record.move_id.invoice_origin and record.is_subscription:
                _order = self.env["sale.order"].search([('name','=',record.move_id.invoice_origin)], limit=1)
                if _order and _order.order_line:
                    _order_line = _order.order_line.filtered(
                        lambda line: line.product_id.id == record.product_id.id and line.is_subscription
                    )
                    if _order_line:
                        record.last_period = _order_line[0].last_period

    last_period = fields.Datetime("Last Period", compute='_last_period')

    def _next_period(self):
        for record in self:
            record.next_period = None
            if record.move_id and record.move_id.invoice_origin and record.is_subscription:
                _order = self.env["sale.order"].search([('name','=',record.move_id.invoice_origin)], limit=1)
                if _order and _order.order_line:
                    _order_line = _order.order_line.filtered(
                        lambda line: line.product_id.id == record.product_id.id and line.is_subscription
                    )
                    if _order_line:
                        record.next_period = _order_line[0].next_period

    next_period = fields.Datetime("Next Period", compute='_next_period')