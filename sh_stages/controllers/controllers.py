# -*- coding: utf-8 -*-
# from odoo import http


# class /odoosh/custom/addons/shStages(http.Controller):
#     @http.route('//odoosh/custom/addons/sh_stages//odoosh/custom/addons/sh_stages/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('//odoosh/custom/addons/sh_stages//odoosh/custom/addons/sh_stages/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('/odoosh/custom/addons/sh_stages.listing', {
#             'root': '//odoosh/custom/addons/sh_stages//odoosh/custom/addons/sh_stages',
#             'objects': http.request.env['/odoosh/custom/addons/sh_stages./odoosh/custom/addons/sh_stages'].search([]),
#         })

#     @http.route('//odoosh/custom/addons/sh_stages//odoosh/custom/addons/sh_stages/objects/<model("/odoosh/custom/addons/sh_stages./odoosh/custom/addons/sh_stages"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('/odoosh/custom/addons/sh_stages.object', {
#             'object': obj
#         })
