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
            _order = request.env["sale.order"].search([('name','=',record.move_id.invoice_origin)], limit=1)
            if(_order):
                _order_line = request.env["sale.order.line"].search([
                                                                        ('name','=',record.name),
                                                                        ('product_uom_qty','=',record.quantity),
                                                                        ('product_id','=',record.product_id.id)
                                                                    ], limit=1)
                if(_order_line):
                    for _order_line in _order_line:
                        record.multiplier_factor_number = _order_line.multiplier_factor_number
                
        return record.multiplier_factor_number

    multiplier_factor_number = fields.Integer("* Period", compute='_multiplier_factor_number')

    def _multiplier_factor_label(self):
        for record in self:
            _order = request.env["sale.order"].search([('name','=',record.move_id.invoice_origin)], limit=1)
            if(_order):
                _order_line = request.env["sale.order.line"].search([
                                                                        ('name','=',record.name),
                                                                        ('product_uom_qty','=',record.quantity),
                                                                        ('product_id','=',record.product_id.id)
                                                                    ], limit=1)
                if(_order_line):
                    for _order_line in _order_line:
                        record.multiplier_factor_label = _order_line.multiplier_factor_label
                    
            return record.multiplier_factor_label

    multiplier_factor_label = fields.Char("Period", compute='_multiplier_factor_label')

    def _is_subscription(self):
        for record in self:
            _order = request.env["sale.order"].search([('name','=',record.move_id.invoice_origin)], limit=1)
            if(_order):
                _order_line = request.env["sale.order.line"].search([
                                                                        ('name','=',record.name),
                                                                        ('product_uom_qty','=',record.quantity),
                                                                        ('product_id','=',record.product_id.id)
                                                                    ], limit=1)
                if(_order_line):
                    for _order_line in _order_line:
                        record.is_subscription = _order_line.is_subscription
                    
            return record.is_subscription

    is_subscription = fields.Boolean("Is Subscription", compute='_is_subscription')    

    def _last_period(self):
        for record in self:
            _order = request.env["sale.order"].search([('name','=',record.move_id.invoice_origin)], limit=1)
            if(_order):
                _order_line = request.env["sale.order.line"].search([
                                                                        ('name','=',record.name),
                                                                        ('product_uom_qty','=',record.quantity),
                                                                        ('product_id','=',record.product_id.id)
                                                                    ], limit=1)
                if(not record.last_period):
                    record.last_period = _order_line.last_period
                    if(_order_line.last_period > record.next_period):
                        record.last_period = record.next_period

            
            return record.last_period

    last_period = fields.Datetime("Last Period", compute='_last_period')

    def _next_period(self):
        for record in self:
            _order = request.env["sale.order"].search([('name','=',record.move_id.invoice_origin)], limit=1)
            if(_order):
                _order_line = request.env["sale.order.line"].search([
                                                                        ('name','=',record.name),
                                                                        ('product_uom_qty','=',record.quantity),
                                                                        ('product_id','=',record.product_id.id)
                                                                    ], limit=1)

                if(record.is_subscription):
                    if(record.last_period):
                        record.next_period = _order_line.next_period                  
            return record.next_period

    next_period = fields.Datetime("Next Period", compute='_next_period')