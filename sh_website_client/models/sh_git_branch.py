#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
from odoo import http
import logging
_logger = logging.getLogger(__name__)

class sh_git_branch(models.Model):

    _inherit = "sh.git_branch"
    _description = "sh.git_branch"

    def get_branch_connect(self, params):        
        try:
            response = {'error':False, 'editor':None, 'message':None}      
            branch = self.env['sh.git_branch'].sudo().browse(int(params['_branch_id']))    
            
            if(branch.kuber_exposers.domain):
                response['url'] = str('http://') + str(branch.kuber_exposers.domain) # + str(':') + str(branch.kuber_exposers.port)
            else:
                response['url'] = str('http://') + str(branch.kuber_exposers.ip) + str(':') + str(branch.kuber_exposers.port)
        except Exception as e:
            _logger.warning({"error":True, "message":"Not branch connection available. \n\n " + getattr(e, 'message', repr(e))})
            response = {"error":True, "message":"Not branch connection available. \n\n " + getattr(e, 'message', repr(e))}
            return response
        return response   