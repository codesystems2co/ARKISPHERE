#-*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class git_repository(http.Controller):

    @http.route('/sh_backups/begin', methods=['GET'], type='http', auth="public", website=True)
    def begin(self, **kw):
        request.env['sh.backup'].sudo().download_database()
