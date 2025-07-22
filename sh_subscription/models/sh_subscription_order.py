#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    @api.depends('name')
    def _compute_subscription_display_name(self):
        """Compute display name for subscription"""
        for record in self:
            record.subscription_display_name = f"{record.name} - Subscription"
    
    subscription_display_name = fields.Char("Subscription Name", compute='_compute_subscription_display_name', store=True)
    
    @api.depends('order_line.is_subscription', 'order_line.last_period', 'order_line.next_period')
    def _compute_subscription_periods(self):
        """Get first subscription line periods for display"""
        for record in self:
            subscription_lines = record.order_line.filtered(lambda line: line.is_subscription)
            if subscription_lines:
                first_line = subscription_lines[0]
                record.subscription_last_period = first_line.last_period
                record.subscription_next_period = first_line.next_period
            else:
                record.subscription_last_period = False
                record.subscription_next_period = False
    
    subscription_last_period = fields.Datetime("Last Period", compute='_compute_subscription_periods', store=True)
    subscription_next_period = fields.Datetime("Next Period", compute='_compute_subscription_periods', store=True)
    
    @api.depends('order_line.is_subscription', 'order_line.next_period')
    def _compute_subscription_status(self):
        """Get subscription status based on next period"""
        for record in self:
            if not record.order_line:
                record.subscription_status = 'inactive'
                continue
            
            subscription_lines = record.order_line.filtered(lambda line: line.is_subscription)
            if not subscription_lines:
                record.subscription_status = 'inactive'
                continue
            
            from datetime import datetime
            current_date = datetime.now().date()
            status = 'active'
            
            for line in subscription_lines:
                if line.next_period:
                    next_period_date = line.next_period.date() if hasattr(line.next_period, 'date') else line.next_period
                    if current_date > next_period_date:
                        status = 'overdue'
                        break
                    elif (next_period_date - current_date).days <= 7:
                        status = 'due_soon'
            
            record.subscription_status = status

    @api.depends('name')
    def _compute_subscription_invoice_count(self):
        """Count subscription invoices for this order"""
        for record in self:
            invoices = self.env['account.move'].search([
                ('invoice_origin', '=', record.name),
                ('move_type', '=', 'out_invoice'),
                ('has_subscription', '=', True)
            ])
            record.subscription_invoice_count = len(invoices)
    
    subscription_status = fields.Selection([
        ('active', 'Active'),
        ('due_soon', 'Due Soon'),
        ('overdue', 'Overdue'),
        ('inactive', 'Inactive')
    ], string="Subscription Status", compute='_compute_subscription_status', store=True)
    
    subscription_invoice_count = fields.Integer("Subscription Invoice Count", compute='_compute_subscription_invoice_count', store=True)
    
    def get_subscription_summary(self):
        """Get subscription summary info"""
        for record in self:
            subscription_lines = record.order_line.filtered(lambda line: line.is_subscription)
            if subscription_lines:
                total_lines = len(subscription_lines)
                total_amount = sum(line.price_total for line in subscription_lines)
                return {
                    'total_lines': total_lines,
                    'total_amount': total_amount,
                    'currency': record.currency_id.symbol
                }
            return {'total_lines': 0, 'total_amount': 0, 'currency': '€'}
    
    def action_view_subscription_invoices(self):
        """Action to view subscription invoices"""
        invoices = self.env['account.move'].search([
            ('invoice_origin', '=', self.name),
            ('move_type', '=', 'out_invoice'),
            ('has_subscription', '=', True)
        ])
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Subscription Invoices'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', invoices.ids)],
            'context': {'default_move_type': 'out_invoice'}
        }
    
    def action_process_subscription_billing(self):
        """Action to process subscription billing for this order"""
        return self.process_subscription_invoices() 