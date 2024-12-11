#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
from odoo import http
import logging
_logger = logging.getLogger(__name__)

class sh_git_repository(models.Model):

    _inherit = "sh.git_repository"
    _description = "Repository"
    # _repository_id
    def get_code_editor(self, params):  
        _logger.warning([('git_branch','=',params['_branch_id']),('cluster_selector','=',str("code-server"))])
        try:
            response = {'error':False, 'editor':None, 'message':None}
            _branch = self.env['sh.git_branch'].sudo().search([('name','=','main'),('repository','=',int(params['_repository_id']))],limit=1)
            kuber_exposer = self.env['kuber.exposer'].sudo().search([('git_branch','=',int(_branch.id)),('cluster_selector','=',str("code-server"))],limit=1)
            _logger.warning("kuber_exposer")
            _logger.warning(kuber_exposer)
            if(kuber_exposer.domain):
                response['editor'] = str('<iframe src="http://'+str(kuber_exposer.domain)+':'+str(kuber_exposer.port)+'" height="auto" width="auto" title="Code Editor"></iframe>')
                response['editor_external_url'] = str('http://'+str(kuber_exposer.domain) + ':' +str(kuber_exposer.port)) + str('/?folder=/var/lib/odoo/')   
            else:
                response['editor'] = str('<iframe src="http://'+str(kuber_exposer.ip)+':'+str(kuber_exposer.port)+'" height="auto" width="auto" title="Code Editor"></iframe>')
                response['editor_external_url'] = str('http://'+str(kuber_exposer.ip)+':'+str(kuber_exposer.port)) + str('/?folder=/var/lib/odoo/')        
        except Exception as e:
            response = {"error":True, "message":"Could not get code editor for this project \n\n " + getattr(e, 'message', repr(e))}
            return response
        return response

    def get_pgadmin(self, params):  
        _logger.warning([('git_branch','=',params['_branch_id']),('cluster_selector','=',str("pgadmin4"))])
        try:
            response = {'error':False, 'editor':None, 'message':None}
            _branch = self.env['sh.git_branch'].sudo().search([('name','=','main'),('repository','=',int(params['_repository_id']))],limit=1)
            kuber_exposer = self.env['kuber.exposer'].sudo().search([('git_branch','=',int(_branch.id)),('cluster_selector','=',str("pgadmin4"))],limit=1)
            if not kuber_exposer:
                response = {"error":True, 'message': _('Could not get postgres adminstrator service.')}
            _logger.warning("kuber_exposer")
            _logger.warning(kuber_exposer)
            if(kuber_exposer.domain):
                response['pgadmin_external_url'] = str('http://'+str(kuber_exposer.domain) + ':' +str(kuber_exposer.port))
            else:
                response['pgadmin_external_url'] = str('http://'+str(kuber_exposer.ip)+':'+str(kuber_exposer.port))
        except Exception as e:
            response = {"error":True, "message":"Could not get postgres administrator for this project \n\n " + getattr(e, 'message', repr(e))}
            return response
        return response