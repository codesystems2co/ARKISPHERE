#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)

class sh_account_move(models.Model):
    _inherit = "account.move"

    def _has_subscription(self):
        for record in self:
            record.has_subscription = False  # Default value
            try:
                # First check invoice lines directly (most reliable)
                for line in record.invoice_line_ids:
                    if line.display_type:  # Skip section/note lines
                        continue
                    
                    # Force recalculation of line subscription status
                    line._is_subscription()
                    
                    if line.is_subscription:
                        record.has_subscription = True
                        _logger.info("Account move %s has subscription - found subscription line %s", record.name, line.id)
                        break
                
                # Fallback: check original sale order
                if not record.has_subscription and record.invoice_origin:
                    _order = self.env["sale.order"].search([('name', '=', record.invoice_origin)], limit=1)
                    if _order and _order.order_line:
                        subscription_lines = _order.order_line.filtered(lambda line: line.is_subscription)
                        if subscription_lines:
                            record.has_subscription = True
                            _logger.info("Account move %s has subscription from order %s", record.name, _order.name)
                        
            except Exception as e:
                _logger.error("Error computing has_subscription for move %s: %s", record.name, str(e))
                record.has_subscription = False

    has_subscription = fields.Boolean("Has Subscription", compute=_has_subscription, default=False, store=True)