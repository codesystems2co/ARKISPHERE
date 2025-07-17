#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
import requests
import sys
import logging
import paramiko
import time
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError

class kuber_domains(models.Model):

    _name = "kuber.domains"
    _description = "Kuber Domains"

    name = fields.Char( required=True, string="Host",  help="")
    port = fields.Char( required=True, string="Port",  help="")
    branch = fields.Many2one(comodel_name="sh.git_branch",  inverse_name="kuber_domains",  string="Branch",  help="")
    domain_ssl = fields.Many2one(comodel_name="kuber.domains_ssl",  inverse_name="name",  string="SSL",  help="")
    
    def t(self):
        raise UserError('starting cron exec_commands...')
    
    def assign_domain(self, params):
        
        domains = []
        response = {'error':False, 'message':None, 'domains':domains}  
        try:                
            branch = self.env['sh.git_branch'].sudo().browse(int(params['_branch_id']))            
            tarjet_port = branch.kuber_exposers.port
            new_domain = self.env['kuber.domains'].sudo().create({ 'name':params['_domain_name'], 'branch':params['_branch_id'], 'port':tarjet_port })            
            branch.sudo().update({'kuber_domains':[(4,new_domain.id)]})
            response['message'] = str('Domain added to branch (') + str(branch.name) + str(")")
            for _domain in branch.kuber_domains:
                domains.append([_domain.id, _domain.name])
            response['domains'] = domains
            self.upstream_service(branch, params['_domain_name'],tarjet_port)
        except Exception as e:
            response = {"error":True, "message":"Could not assign domain to branch. \n\n " + getattr(e, 'message', repr(e)) } # +" ON LINE "+format(sys.exc_info()[-1].tb_lineno)
            return response
        return response

    def delete_domain(self, params):
        domains = []
        response = {'error':False, 'message':None, 'domains':domains}  
        try: 
            domain = self.env['kuber.domains'].sudo().browse(int(params['_domain_id']))
            domain_name = domain.name
            branch = self.env['sh.git_branch'].sudo().browse(int(params['_branch_id']))
            branch.sudo().update({'kuber_domains':[(2,str(params['_domain_id']))]})

            request.cr.execute(str("DELETE from kuber_domains_sh_git_branch_rel ") + str("WHERE kuber_domains_id=") + str(params['_domain_id']) + str(" AND ") + str("sh_git_branch_id=") + str(params['_branch_id']))
            
            response_domains = self.get_domains(params)
            _logger.warning(response_domains)
            response['domains'] = response_domains['domains']
            _logger.warning(domain)
            self.delete_upstream_service(branch, domain_name)

        except Exception as e:
            response = {"error":True, "message":"Could not delete domains for branch selected. \n\n " + getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno) }
            return response
        return response
    
    def get_domains(self, params):
        domains = []
        response = {'error':False, 'message':None, 'domains':domains}
        try:
            request.cr.execute(str("SELECT * from kuber_domains_sh_git_branch_rel ") + str("WHERE")+ str(" sh_git_branch_id=") + str(params['_branch_id']))
            _domains = request.cr.dictfetchall()
            if(len(_domains)>0):
                for domain in _domains:
                    if('kuber_domains_id' in domain):
                        _domain = self.env['kuber.domains'].sudo().browse(int(domain['kuber_domains_id']))
                        domains.append([_domain.id, _domain.name])
                response['domains'] = domains
        except Exception as e:
            response = {"error":True, "message":"Could not assign domain to branch. \n\n " + getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno) } # +" ON LINE "+format(sys.exc_info()[-1].tb_lineno)
            return response
        return response
    
    def delete_upstream_service(self, _branch, domain_name):
        _physical_server_id = _branch.repository.so_server.physical_server.id
        physical_server = self.env['sh.physical_server'].browse(_physical_server_id)     
        if(physical_server):
            ssh = self.get_ssh(physical_server)  
            _file = self.get_domain_file(_branch.repository, domain_name)
            _logger.warning(_file)
            command = str("rm /etc/nginx/sites-enabled/") + str(_file)
            _logger.warning(':: Removing upstream hostname resolver')
            _logger.warning(command)
            stdin, stdout, stderr = ssh.exec_command(command)
            for line in iter(stdout.readline, ""):
                _logger.warning(line)
            for line in iter(stderr.readline, ""):
                _logger.warning(line)

            # NOT USED BECAUSE RESTART OTHER CLIENTs SERVICEs
            #command = str("service nginx restart  ")
            #_logger.warning(command)
            #stdin, stdout, stderr = ssh.exec_command(command)
            #for line in iter(stdout.readline, ""):
            #    _logger.warning(line)
            #for line in iter(stderr.readline, ""):
            #    _logger.warning(line)
            ssh.close()
    
    def upstream_service(self, _branch, domain_name, tarjet_port):
        _physical_server_id = _branch.repository.so_server.physical_server.id
        _logger.warning("_physical_server_id")
        _logger.warning(_physical_server_id)
        physical_server = self.env['sh.physical_server'].browse(_physical_server_id)     
        if(physical_server):
            kuber_template = self.env['kuber.template'].search([('name','=','nginx.internal.domain.resolver')], limit=1)
            if(not kuber_template):
                raise Warning("Template does not exist: nginx.internal.domain.resolver")

            ssh = self.get_ssh(physical_server)
            
            # tags replacement on deployments templates
            content = self.tags_replace_matches_tpl(kuber_template.content, {'_ip':physical_server.ip, '_domain':domain_name, '_port':tarjet_port})
            _file = self.create_domain_file(ssh, _branch.repository, domain_name, content, physical_server)

            sites_enabled = str(" /etc/nginx/sites-enabled/") # + str(_branch.repository.autor.id)
            autor_repository_folder = str(" /etc/nginx/sites-enabled/") # + str(_branch.repository.autor.id)+str('/')+str(_branch.repository.id)

            command = str("mkdir -m 777 ") + str(" ") +str (sites_enabled)
            stdin, stdout, stderr = ssh.exec_command(command)

            command = str("cp -rf  ") + str(_file) + str(" ") +str (autor_repository_folder)
            _logger.warning(command)
            stdin, stdout, stderr = ssh.exec_command(command)
            for line in iter(stdout.readline, ""):
                _logger.warning(line)
            for line in iter(stderr.readline, ""):
                _logger.warning(line)
            
            # NOT USED BECAUSE RESTART OTHER CLIENTs SERVICEs
            # Now it can be used when deployments are on cliente server side
            command = str("service nginx restart  ")
            _logger.warning(command)
            stdin, stdout, stderr = ssh.exec_command(command)
            for line in iter(stdout.readline, ""):
                _logger.warning(line)
            for line in iter(stderr.readline, ""):
                _logger.warning(line)
            
            ssh.close()
    
    def create_domain_file(self, ssh, _repository, file_name, content, physical_server):  
        self.sudo().create_user_deploy_dir(ssh, _repository)
        _file = str("/home/kubernets/users/") + str(_repository.autor.id) + str("/") + str(_repository.id) + str("/") + str(file_name) + str(".domain")    
        file_stream = open(str(_file),"w+")
        file_stream.write(str(content))
        file_stream.close()
        if physical_server.ssh_host != '127.0.0.1' and physical_server.ssh_host != '172.17.0.1':
            _logger.warning(":::::::::NO SELF SH SERVER")
            sftp = ssh.open_sftp()
            sftp.put(_file,_file)
        return _file
    
    def get_domain_file(self, _repository, file_name):
        _file = str(_repository.autor.id) + str("/") + str(_repository.id) + str("/") + str(file_name) + str(".domain")   
        return _file
    
    def tags_replace_matches_tpl(self, content, params):
        content = self.replace_tpl_tag(content, "<SERVER_IP>", str(params['_ip']))  
        content = self.replace_tpl_tag(content, "<DOMAIN>", str(params['_domain']))        
        content = self.replace_tpl_tag(content, "<PORT>", str(params['_port']))                
        return content

    def replace_tpl_tag(self, content, find, replace):
        content = str(self.env['kuber.template'].replace_tag(content,find,replace))
        return content   

    def create_user_deploy_dir(self, ssh, _repository):
        # make sure file path exists
        self.env['kuber.deploy'].create_user_deploy_dir(ssh, _repository)
    
    def restart_domain_resolver(self):
        physical_servers = self.env['sh.physical_server'].search([])
        if(physical_servers):
            for physical_server in physical_servers:
                if(physical_server):
                    ssh = self.get_ssh(physical_server)
                    command = str("service nginx restart")
                    _logger.warning(command)
                    stdin, stdout, stderr = ssh.exec_command(command)
                    for line in iter(stdout.readline, ""):
                        _logger.warning(line)
                    for line in iter(stderr.readline, ""):
                        _logger.warning(line)
    
    def verify_domain(self, params):
        domain = params['domain']
        domain = domain if domain.startswith('http') else ('http://' + domain)

        try:
            response = requests.get(url=domain)
        except:
            return _('Can not resolve or not a valid domain.')
        
        if response.status_code >= 200 and response.status_code <= 299:
            return True
        elif response.status_code >= 100 and response.status_code <= 199:
            return _('Informational: indicates an interim response for communicating connection status or request progress prior to completing the requested action and sending a final response.')
        elif response.status_code >= 300 and response.status_code <= 399:
            return _('Redirection: indicates that further action needs to be taken by the user agent in order to fulfill the request.')
        elif response.status_code >= 400 and response.status_code <= 499:
            return _('Client Error:  indicates that the client seems to have erred.')
        elif response.status_code >= 400 and response.status_code <= 499:
            return _('Client Error:  indicates that the client seems to have erred.')


    def get_ssh(self, physical_server):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(str(physical_server.ssh_host), username=str(physical_server.user), password=str(physical_server.password), port=str(physical_server.port), look_for_keys=False, allow_agent=False)
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            return ssh
        except Exception as e:
            raise Warning(str("\n ID: ") + str(physical_server.id) + str("\n IP: ") + str(physical_server.ssh_host) + str("\n PORT: ") + str(physical_server.port) + str("\n USER: ") + str(physical_server.user) + str("\n MESSAGE: ") + getattr(e, 'message', repr(e)))
    