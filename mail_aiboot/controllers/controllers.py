# -*- coding: utf-8 -*-
# from odoo import http


# class MailAiboot(http.Controller):
#     @http.route('/mail_aiboot/mail_aiboot', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mail_aiboot/mail_aiboot/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('mail_aiboot.listing', {
#             'root': '/mail_aiboot/mail_aiboot',
#             'objects': http.request.env['mail_aiboot.mail_aiboot'].search([]),
#         })

#     @http.route('/mail_aiboot/mail_aiboot/objects/<model("mail_aiboot.mail_aiboot"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mail_aiboot.object', {
#             'object': obj
#         })

