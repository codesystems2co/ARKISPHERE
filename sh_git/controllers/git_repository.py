#-*- coding: utf-8 -*-
from odoo import http

class git_repository(http.Controller):

    @http.route('/git/index', auth='public')
    def index(self, **kw):
        return "Hello, world"
