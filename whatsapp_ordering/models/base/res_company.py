# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import markupsafe
import logging
_logger = logging.getLogger(__name__)



class res_company(models.Model):
    _inherit = "res.company"

    meta_access_token = fields.Char(string="Access Token")
    meta_phone_number = fields.Char(string="Phone Number")
    meta_webhook = fields.Char(string="Webhook", compute="_meta_webhook", readonly=True)

    # settings
    meta_account_creation = fields.Boolean(string="Account Creation")
    meta_sale_order_confirmation = fields.Boolean(string="Order Confirmation")
    meta_payment_transaction_confirmation = fields.Boolean(string="Payment Confirmation")
    meta_invoice_confirmation = fields.Boolean(string="Invoice Confirmation")
    meta_coupon_information = fields.Boolean(string="Coupon Information")
    meta_delivery_confirmation = fields.Boolean(string="Delivery Confirmation")
    meta_product_creation = fields.Boolean(string="Share New Products", help='with customers orders in same product category')

    def _meta_webhook(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') 
        for record in self:
            record.meta_webhook = str(base_url) + str('/meta/whatsapp/webhook')