# -*- coding: utf-8 -*-
# from odoo import http


# class WhatsappOrdering(http.Controller):
#     @http.route('/whatsapp_ordering/whatsapp_ordering', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/whatsapp_ordering/whatsapp_ordering/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('whatsapp_ordering.listing', {
#             'root': '/whatsapp_ordering/whatsapp_ordering',
#             'objects': http.request.env['whatsapp_ordering.whatsapp_ordering'].search([]),
#         })

#     @http.route('/whatsapp_ordering/whatsapp_ordering/objects/<model("whatsapp_ordering.whatsapp_ordering"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('whatsapp_ordering.object', {
#             'object': obj
#         })

