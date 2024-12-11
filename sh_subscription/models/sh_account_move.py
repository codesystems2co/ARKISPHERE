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
            try:
                _order_lines = request.env["account.move.line"].search([
                                                                            ('move_id','=',record.id)       
                                                                       ])
                for _order_line in _order_lines:
                    if(_order_line.is_subscription):
                        try:
                            record.has_subscription = _order_line.is_subscription
                            return record.has_subscription
                        except:
                            record.has_subscription = False
                            return record.has_subscription
            except:
                record.has_subscription = False
                return record.has_subscription


    has_subscription = fields.Boolean("Has Subscription", compute=_has_subscription, default=False, store=True)