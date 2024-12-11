# -*- coding: utf-8 -*-
from odoo import http
from http import cookies
import sys, os, base64
from github import Github



class SH_so_server(http.Controller):

    @http.route('/git/get_so_server', methods=['POST'], type='json', auth="public", website=True)
    def get_so_server(self, **kw):
        partner_id = kw.get('partner_id')
        
        if(len(partner_id)>0):
            try:
                so_servers = http.request.env['so.server'].search([('owner','=',partner_id)])
                if(so_servers):
                    for so_server in so_servers:
                        pass
                        
            except Exception as e:
                return {"status":"error", "message":getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno)}
    
    @http.route('/app/logs', methods=['POST'], type='json', auth="public", website=True)
    def get_app_logs(self, **kw):
        branch_id = kw.get('branch_id')        
        if(len(branch_id)>0):
            try:
                app_logs = http.request.env['kuber.deploy'].get_app_logs(branch_id)
                return {"status":"success","app_logs":app_logs}
            except Exception as e:
                return {"status":"error", "message":getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno)}