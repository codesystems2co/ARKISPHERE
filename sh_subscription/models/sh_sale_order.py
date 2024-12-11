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

    def _has_subscription(self):
        try:                           
            for record in self:
                try:
                    _order_lines = request.env["sale.order.line"].search([
                                                                            ('order_id','=',record.id)            
                                                                         ])
                    for _order_line in _order_lines:
                        if(_order_line.is_subscription):
                            try:
                                record.has_subscription = _order_line.is_subscription
                                record.sudo.update({'has_subscription':record.has_subscription})
                                return record.has_subscription
                            except:
                                record.has_subscription = False
                                record.sudo.update({'has_subscription':record.has_subscription})
                                return record.has_subscription
                except:
                    try:
                        self.has_subscription = False
                        self.sudo().update({'has_subscription':record.has_subscription})
                        return self.has_subscription
                    except:
                        pass
        except:
            self.has_subscription = False
            self.sudo().update({'has_subscription':record.has_subscription})
            return self.has_subscription 
            pass

    has_subscription = fields.Boolean("Has Subscription", compute=_has_subscription)
    

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
                values = {'workers':values[0],'period':values[1],'cores':values[2],'ram':values[3],'disk':values[4],'customisation':values[5]}

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
                    if(_now > _order_line.next_period):
                        _line_update = request.env["sale.order.line"].sudo().browse(_order_line.id)
                        _line_update.update({
                                                'periods_billed':int(int(_order_line.periods_billed) + int(1))
                                            })                    
                        _logger.warning("INVOICE APPLIES")
                        for_next_invoice = True                             
                    else:
                        _logger.warning("INVOICE DOES NOT APPLY")            
                
                if(for_next_invoice): 
                    invoice_vals = _order._prepare_invoice() 
                    _logger.warning("___INVOICE")
                    _logger.warning(date.today() )
                    invoice_vals["invoice_date"] = date.today()
                    invoice_vals = _order._prepare_invoice()
                    for line in _order.order_line:          
                            _line_vals = line._prepare_invoice_line()                        
                            _line_vals["display_type"] = False 
                            _line_vals["quantity"] = line.product_uom_qty
                            invoice_vals['invoice_line_ids'].append((0, 0, _line_vals))
                    
                    
                    request.env["account.move"].create(invoice_vals)
        except:
            pass