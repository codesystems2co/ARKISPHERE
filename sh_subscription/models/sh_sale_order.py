#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
from dateutil.relativedelta import *
from datetime import datetime
from datetime import date
import re

import logging
_logger = logging.getLogger(__name__)

class sh_sale_order(models.Model):
    _inherit = "sale.order"

    @api.depends('order_line.is_subscription')
    def _compute_has_subscription(self):
        """Compute if order has subscription lines"""
        for record in self:
            try:
                subscription_lines = record.order_line.filtered(lambda line: line.is_subscription)
                record.has_subscription = bool(subscription_lines)
            except Exception as e:
                _logger.warning(f"Error computing has_subscription for order {record.id}: {e}")
                record.has_subscription = False

    has_subscription = fields.Boolean("Has Subscription", compute='_compute_has_subscription', store=True)

    def account_move_subscriptions(self, sale_order):
        """
        Create all subscription invoices for a sale order based on billing periods
        """
        try:
            _logger.info("Processing subscription invoices for sale order: %s", sale_order.name)
            
            # Get all subscription lines for this order
            subscription_lines = sale_order.order_line.filtered(lambda line: line.is_subscription)
            
            if not subscription_lines:
                _logger.info("No subscription lines found for order %s", sale_order.name)
                return
            
            _logger.info("Found %s subscription lines", len(subscription_lines))
            
            # Calculate how many periods should have been billed
            current_date = datetime.now()
            order_date = sale_order.date_order
            
            if not order_date:
                _logger.warning("No order date found for sale order %s", sale_order.name)
                return
            
            _logger.info("Order date: %s, Current date: %s", order_date, current_date)
            
            # Process each subscription line to determine billing periods
            for line in subscription_lines:
                try:
                    multiplier = int(line.multiplier_factor_number) if line.multiplier_factor_number else 1
                    periods_billed = int(line.periods_billed) if line.periods_billed else 0
                    
                    _logger.info("Line %s: multiplier=%s, periods_billed=%s", line.id, multiplier, periods_billed)
                    
                    # Calculate how many periods should have been billed by now
                    months_since_order = (current_date.year - order_date.year) * 12 + (current_date.month - order_date.month)
                    periods_should_be_billed = (months_since_order // multiplier) + 1
                    
                    _logger.info("Months since order: %s, Periods should be billed: %s", months_since_order, periods_should_be_billed)
                    
                    # Create invoices for missing periods
                    missing_periods = periods_should_be_billed - periods_billed
                    
                    if missing_periods > 0:
                        _logger.info("Creating %s missing invoices for line %s", missing_periods, line.id)
                        
                        for period_num in range(1, missing_periods + 1):
                            # Calculate invoice date for this period
                            invoice_period = periods_billed + period_num
                            invoice_date = order_date + relativedelta(months=(invoice_period - 1) * multiplier)
                            
                            # Don't create invoices for future dates
                            if invoice_date > current_date:
                                _logger.info("Skipping future invoice for period %s (date: %s)", invoice_period, invoice_date)
                                break
                            
                            _logger.info("Creating invoice for period %s with date %s", invoice_period, invoice_date)
                            
                            # Prepare invoice values
                            invoice_vals = sale_order._prepare_invoice()
                            invoice_vals["invoice_date"] = invoice_date.date() if isinstance(invoice_date, datetime) else invoice_date
                            
                            # Add invoice lines - only subscription lines
                            invoice_vals['invoice_line_ids'] = []  # Clear default lines
                            
                            for order_line in sale_order.order_line:
                                if order_line.is_subscription:
                                    line_vals = order_line._prepare_invoice_line()
                                    line_vals["quantity"] = order_line.product_uom_qty
                                    invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                            
                            # Create the invoice
                            invoice = request.env["account.move"].create(invoice_vals)
                            
                            # Force update subscription flags after creation
                            for inv_line in invoice.invoice_line_ids:
                                inv_line._is_subscription()
                            invoice._has_subscription()
                            
                            _logger.info("Created subscription invoice %s for period %s", invoice.name, invoice_period)
                            
                            # Update periods billed
                            line.sudo().update({
                                'periods_billed': str(periods_billed + period_num)
                            })
                            
                    else:
                        _logger.info("No missing periods for line %s", line.id)
                        
                except Exception as e:
                    _logger.error("Error processing subscription line %s: %s", line.id, str(e))
                    continue
                    
            _logger.info("Completed processing subscription invoices for sale order: %s", sale_order.name)
            
        except Exception as e:
            _logger.error("Error in account_move_subscriptions for order %s: %s", sale_order.name if sale_order else 'Unknown', str(e))


    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        response =  super(sh_sale_order, self)._cart_update(product_id, line_id, add_qty, set_qty, **kwargs)
        multiplier_factor = 1
        multiplier_factor_label = "Monthly"

        _order_line = request.env["sale.order.line"].sudo().browse(response['line_id'])
        if _order_line:
            try:
                attributes_values = str(re.findall(r'\(.*?\)', _order_line.name)[0]).replace('(','').replace(')','').split(',')
                values = []
                for value in attributes_values:
                    values.append(str(value).replace('Gi','').replace('Cores','').strip())
                
                _logger.info('_cart_update values >>')
                _logger.info(values)

                # Attributes change in order how display in view
                values = {'type':values[0],'period':values[1],'cores':values[2],'ram':values[3],'disk':values[4],'customisation':values[5]}

                _logger.info('_cart_update line id values >>')
                _logger.info(_order_line)

                _is_subscription = True
                if('Monthly' == values['period']):
                    multiplier_factor = 1
                    multiplier_factor_label = "Monthly"
                if('Semester' == values['period']):
                    multiplier_factor = 6
                    multiplier_factor_label = "Semester"
                if('Yearly' == values['period']):
                    multiplier_factor = 12
                    multiplier_factor_label = "Yearly"

                # External Server
                if('One time' in str(_order_line.name)):
                    multiplier_factor = 1
                    multiplier_factor_label = "One time"
                    _is_subscription = False

                line = {
                        "price_unit":(float(_order_line.price_unit)*float(multiplier_factor)) * float(response['quantity']),
                        "price_subtotal":(float(_order_line.price_subtotal)*float(multiplier_factor)) * float(response['quantity']),
                        "price_tax":(float(_order_line.price_tax)*float(multiplier_factor)) * float(response['quantity']),
                        "price_total":(float(_order_line.price_total)*float(multiplier_factor)) * float(response['quantity']),
                        "price_unit":(float(_order_line.price_unit)*float(multiplier_factor)) * float(response['quantity']),
                        "price_reduce_taxinc":(float(_order_line.price_reduce_taxinc)*float(multiplier_factor)) * float(response['quantity']),
                        "price_reduce_taxexcl":(float(_order_line.price_reduce_taxexcl)*float(multiplier_factor)) * float(response['quantity']),
                        "is_subscription":_is_subscription,
                        "multiplier_factor_number":multiplier_factor,
                        "multiplier_factor_label":multiplier_factor_label,
                        }
                
                _logger.info('line id updating >>')
                _logger.info(line)

                _order_line.sudo().update(line)
            except:
                pass
        return response

    def bill_period(self):
        try:
            _orders = self.env["sale.order"].search([])
            for _order in _orders:
                _order_lines = request.env["sale.order.line"].sudo().search([
                                                                                ('order_id','=',_order.id)                
                                                                            ])
                for_next_invoice = False
                _now = datetime.now() # + relativedelta(months=+(int(30)))
                
                for _order_line in _order_lines:
                    # Only process subscription lines
                    if not _order_line.is_subscription:
                        continue
                    
                    # Calculate next period manually instead of relying on computed field
                    try:
                        multiplier = int(_order_line.multiplier_factor_number) if _order_line.multiplier_factor_number else 1
                        periods_billed = int(_order_line.periods_billed) if _order_line.periods_billed else 0
                        
                        # Calculate when next invoice should be due
                        if _order.date_order:
                            should_invoice = False
                            
                            if periods_billed == 0:
                                # First period - bill immediately if order is at least 1 day old
                                days_since_order = (_now.date() - _order.date_order.date()).days
                                if days_since_order >= 0:  # Order exists, bill first period
                                    should_invoice = True
                                    _logger.warning("Line %s: FIRST PERIOD - PeriodsBilled=%s, DaysSinceOrder=%s", 
                                                   _order_line.id, periods_billed, days_since_order)
                            else:
                                # Subsequent periods - bill when due date arrives
                                next_invoice_date = _order.date_order + relativedelta(months=periods_billed * multiplier)
                                if _now.date() >= next_invoice_date.date():
                                    should_invoice = True
                                    _logger.warning("Line %s: RECURRING PERIOD - Current=%s, NextDue=%s, PeriodsBilled=%s", 
                                                   _order_line.id, _now.date(), next_invoice_date.date(), periods_billed)
                            
                            if should_invoice:
                                _logger.warning("INVOICE APPLIES for line %s", _order_line.id)
                                
                                # Update periods billed
                                _line_update = request.env["sale.order.line"].sudo().browse(_order_line.id)
                                _line_update.update({
                                    'periods_billed': str(periods_billed + 1)
                                })                    
                                
                                for_next_invoice = True                             
                            else:
                                _logger.warning("INVOICE DOES NOT APPLY for line %s", _order_line.id)
                        else:
                            _logger.warning("No order date for line %s", _order_line.id)
                            
                    except Exception as e:
                        _logger.error("Error processing line %s: %s", _order_line.id, str(e))            
                
                if(for_next_invoice): 
                    invoice_vals = _order._prepare_invoice() 
                    _logger.warning("___INVOICE")
                    _logger.warning(date.today() )
                    invoice_vals["invoice_date"] = date.today()
                    
                    # Clear default lines and only add subscription lines
                    invoice_vals['invoice_line_ids'] = []
                    
                    for line in _order.order_line:
                        if line.is_subscription:  # Only add subscription lines
                            _line_vals = line._prepare_invoice_line()                        
                            _line_vals["quantity"] = line.product_uom_qty
                            invoice_vals['invoice_line_ids'].append((0, 0, _line_vals))
                    
                    # Create the invoice
                    invoice = request.env["account.move"].create(invoice_vals)
                    
                    # Force update subscription flags after creation
                    for inv_line in invoice.invoice_line_ids:
                        inv_line._is_subscription()
                    invoice._has_subscription()
                    
                    _logger.warning("Created subscription invoice %s", invoice.name)
        except:
            pass
    
    def action_confirm(self):
        _logger.info("Starting sale order confirmation process for order %s", self.name)
        response = super(sh_sale_order, self).action_confirm()
        _logger.info("Super action_confirm completed for order %s", self.name)
        
        try:
            # Check for server lines
            server_lines = [line for line in self.order_line if line.so_server]
            _logger.info("Found %s server lines in order %s", len(server_lines), self.name)
            
            if server_lines:
                _logger.info("Attempting to send server details email for order %s", self.name)
                
                # Get email template
                try:
                    template = self.env.ref('sh_subscription.email_template_sale_order_server_details')
                    _logger.info("Email template found: %s", template.name if template else 'Not found')
                except Exception as e:
                    _logger.error("Failed to find email template: %s", str(e))
                    return response
                
                if template:
                    # Log server details that will be sent
                    for line in server_lines:
                        _logger.info("Server details for line %s:", line.id)
                        if line.so_server and line.so_server.physical_server:
                            server = line.so_server.physical_server
                            _logger.info("- Server Name: %s", server.name)
                            _logger.info("- IP: %s", server.ip)
                            _logger.info("- Specs: Cores=%s, RAM=%s, Disk=%s", 
                                       server.processor_core, server.ram_size, server.disk_size)
                    
                    # Send email
                    try:
                        _logger.info("Sending email to customer %s (%s)", 
                                   self.partner_id.name, self.partner_id.email)
                        template.send_mail(self.id, force_send=True)
                        _logger.info("Email sent successfully for order %s", self.name)
                    except Exception as e:
                        _logger.error("Failed to send email: %s", str(e))
            else:
                _logger.info("No server lines found in order %s, skipping email", self.name)
                
        except Exception as e:
            _logger.error("Error in action_confirm for order %s: %s", self.name, str(e))
        
        return response
        