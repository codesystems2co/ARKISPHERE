#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
from dateutil.relativedelta import *
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)

class sh_sale_order_line(models.Model):
    _inherit = "sale.order.line"

    is_subscription = fields.Boolean("Is Subscription", default=False)
    multiplier_factor_number = fields.Integer("* Period", default=False)
    multiplier_factor_label = fields.Char("Period", default=False)
    periods_billed = fields.Char("Period(s) Billed", default=0)
    so_server = fields.Many2one('so.server', string="S.O Server", ondelete='restrict')

    def _last_period(self):
        for record in self:
            record.last_period = None
            if record.is_subscription and record.order_id and record.order_id.date_order:
                try:
                    periods_billed = int(record.periods_billed) if record.periods_billed else 0
                    multiplier = int(record.multiplier_factor_number) if record.multiplier_factor_number else 1
                    
                    # Calculate last period end date
                    if periods_billed > 0:
                        # If we have billed periods, last period is order date + (periods_billed * multiplier) months
                        record.last_period = record.order_id.date_order + relativedelta(months=periods_billed * multiplier)
                    else:
                        # If no periods billed yet, last period starts from order date
                        record.last_period = record.order_id.date_order
                except (ValueError, TypeError):
                    # Fallback to order date if conversion fails
                    record.last_period = record.order_id.date_order

    last_period = fields.Datetime("Last Period", compute='_last_period')

    def _next_period(self):
        for record in self:
            record.next_period = False  # Initialize with False for non-subscription items
            
            if record.is_subscription:
                try:
                    multiplier = int(record.multiplier_factor_number) if record.multiplier_factor_number else 1
                    current_time = datetime.now()
                    
                    if record.last_period:
                        # Calculate next billing period
                        calculated_next = record.last_period + relativedelta(months=multiplier)
                        
                        # If calculated next period is in the past, calculate the correct future date
                        if calculated_next < current_time:
                            # Calculate how many periods we need to add to get to current or future date
                            months_diff = (current_time.year - calculated_next.year) * 12 + (current_time.month - calculated_next.month)
                            periods_to_add = (months_diff // multiplier) + 1
                            record.next_period = calculated_next + relativedelta(months=periods_to_add * multiplier)
                        else:
                            record.next_period = calculated_next
                    else:
                        # If no last period, calculate from order date
                        if record.order_id and record.order_id.date_order:
                            periods_billed = int(record.periods_billed) if record.periods_billed else 0
                            next_period_date = record.order_id.date_order + relativedelta(months=(periods_billed + 1) * multiplier)
                            
                            # If this is still in the past, move to current or future
                            if next_period_date < current_time:
                                months_diff = (current_time.year - next_period_date.year) * 12 + (current_time.month - next_period_date.month)
                                periods_to_add = (months_diff // multiplier) + 1
                                record.next_period = next_period_date + relativedelta(months=periods_to_add * multiplier)
                            else:
                                record.next_period = next_period_date
                        else:
                            # Fallback: start from current time
                            record.next_period = current_time + relativedelta(months=multiplier)
                        
                except (ValueError, TypeError) as e:
                    # Fallback to current time + multiplier months
                    _logger.warning("Error calculating next_period for line %s: %s", record.id, str(e))
                    multiplier = 1
                    record.next_period = datetime.now() + relativedelta(months=multiplier)

    next_period = fields.Datetime("Next Period", compute='_next_period')  

    