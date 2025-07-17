#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
import sys
import logging
import paramiko
import time
import os
import base64
_logger = logging.getLogger(__name__)

class kuber_domains_ssl(models.Model):

    _name = "kuber.domains_ssl"
    _description = "Kuber Domains SSL"

    name = fields.Many2one( comodel_name="kuber.domains", required=True, string="Domain",  help="")
    ssl_cert = fields.Binary(  string="Certificate")
    ssl_cert_key = fields.Binary( string="Certificate Key")
    ssl_type = fields.Selection( selection=[("internal","Self-Signed"),("external","3rd Party")], string="Type")
    filename_crt = fields.Char(  string="")
    filename_key = fields.Char(  string="")

    def create_ssl_internal(self, params):
        ssl_domains = []
        response = {'error':False, 'message':None, 'ssl_domains':ssl_domains}
        _repository = self.env['sh.git_repository'].sudo().browse(int(params['_repository_id']))
        _physical_server_id = _repository.so_server.physical_server.id
        physical_server = self.env['sh.physical_server'].sudo().browse(_physical_server_id)
        if(physical_server):
            ssh = self.get_ssh(physical_server)
            _repository = self.env['sh.git_repository'].sudo().browse(int(params['_repository_id']))
            _domain = self.env['kuber.domains'].sudo().browse(int(params['_domain']))
            command = str("certbot --nginx --all --non-interactive --agree-tos --register-unsafely-without-email -d ") + str(_domain.name)
            stdin, stdout, stderr = ssh.exec_command(command)

            _logger.warning(':: Creating Self Signed')

            for line in iter(stdout.readline, ""):
                _logger.warning(line)

            errors = str()
            for line in iter(stderr.readline, ""):
                errors += (str(line)+str('\n\n'))
                _logger.warning(line)

            _logger.warning(':: EOF')             

            if len(errors)>0:
                ssh.close()
                response['ssl_domains'] = self.get_domains_ssl(params)
                response["message"] = errors
                return response

            _domain_ssl = self.sudo().search([("name","=",int(_domain.id))], limit=1)
            if(not _domain_ssl):
                ssl_type = str("internal")
                new_ssl = self.sudo().create({
                                                "name": int(_domain.id),
                                                "ssl_cert":None,
                                                "ssl_cert_key":None,
                                                "ssl_type":ssl_type,
                                                "filename_crt":str(_domain.name) + str(".crt"),
                                                "filename_key":str(_domain.name) + str(".key")
                                            })
                _domain.sudo().update({"domain_ssl":new_ssl.id})
            ssh.close()
            response['ssl_domains'] = self.get_domains_ssl(params)
            response["message"] = "SSL was created and assigned successful for domain " + str(_domain.name)
            return response

    # it was not work without certbot but generates files inside OK
    # invalid certification because it is not verified by
    def create_ssl_external(self, params):
        ssl_domains = []
        response = {'error':False, 'message':None, 'ssl_domains':ssl_domains}
        _repository = self.env['sh.git_repository'].sudo().browse(int(params['_repository_id']))
        _physical_server_id = _repository.so_server.physical_server.id
        _logger.warning("_physical_server_id")
        _logger.warning(_physical_server_id)
        physical_server = self.env['sh.physical_server'].sudo().browse(_physical_server_id)      
        if(physical_server):
            ssh = self.get_ssh(physical_server)            
            self.env['kuber.deploy'].create_user_deploy_dir(ssh, _repository)
            client_deployment_path = str(str("/home/kubernets/users/") + str(_repository.autor.id) + str("/") + str(_repository.id) + str("/ssl/"))
            command = str("mkdir -p ") + client_deployment_path
            stdin, stdout, stderr = ssh.exec_command(command)
            
            kuber_template = self.env['kuber.template'].search([('name','=','nginx.internal.domain.ssl.resolver')], limit=1)
            if(not kuber_template):
                raise Warning("Template does not exist: nginx.internal.domain.ssl.resolver")

            _domain = self.env['kuber.domains'].sudo().browse(int(params['_domain']))

            self.env['kuber.deploy'].create_user_deploy_dir(ssh, _repository)
            ssl_type = str("external")
            if(params['type']=="external"):
                try:
                    _, cert_encoded = str(params['ssl_cert']).split(",", 1)
                    cert_encoded += '=' * (-len(cert_encoded) % 4)
                    cert_decoded = base64.b64decode(cert_encoded)
                    
                    _, key_encoded = str(params['ssl_cert_key']).split(",", 1)
                    key_encoded += '=' * (-len(key_encoded) % 4)
                    key_decoded = base64.b64decode(key_encoded)
                except Exception as e:
                    _logger.error("Could not decode base64 certificate data: %s", e)
                    raise Warning("The uploaded certificate or key file is not in a valid format.")

                self.upload_external_certificates(ssh, cert_decoded, str(client_deployment_path) + str(_domain.name) + str(".crt")) 
                self.upload_external_certificates(ssh, key_decoded, str(client_deployment_path) + str(_domain.name) + str(".key"))      
                
                _domain_ssl = self.sudo().search([("name","=",int(_domain.id))], limit=1)

                if(not _domain_ssl):
                    new_ssl = self.sudo().create({
                                                    "name": int(_domain.id),
                                                    "ssl_cert": cert_decoded,
                                                    "ssl_cert_key": key_decoded,
                                                    "ssl_type":ssl_type,
                                                    "filename_crt":str(_domain.name) + str(".crt"),
                                                    "filename_key":str(_domain.name) + str(".key")
                                                })
                else:
                    _domain_ssl.sudo().update({
                                                "ssl_cert": cert_decoded,
                                                "ssl_cert_key": key_decoded,
                                                "ssl_type":ssl_type,
                                                "filename_crt":str(_domain.name) + str(".crt"),
                                                "filename_key":str(_domain.name) + str(".key")
                                              })
            else:
                pass
            
            template_content = kuber_template.content.replace("listen      443 default;", "listen 443 ssl default;")
            template_content = template_content.replace("ssl on;", "")

            template_tagged = self.tags_replace_matches_tpl(template_content, {"crt_file":str(client_deployment_path) + str(_domain.name) + str(".crt"), "key_file":str(client_deployment_path) + str(_domain.name) + str(".key"), "domain":_domain.name})
            _file = self.create_domain_ssl_file(ssh, _repository, str(_domain.name), str(template_tagged), physical_server)   
            self.upstream_ssl_service(_file, ssh)
            response['ssl_domains'] = self.get_domains_ssl(params)
            response["message"] = "SSL was created and assigned successful for domain " + str(_domain.name)
            return response
        pass

    def qweb_get_domains_ssl(self, params):
        response = {'error':False, 'message':None, 'domains':[]}
        response['domains'] = self.get_domains_ssl(params)
        return response        

    def get_domains_ssl(self, params):
        domains_ssl = []
        _domains = self.get_domains_ids(params)
        _logger.warning("DOMAINS SSL")
        _logger.warning(_domains['domains'])
        if(_domains):
            _domains_ssl = self.sudo().search([("name","in",_domains['domains'])])
            if(len(_domains_ssl)>0):
                for _domain_ssl in _domains_ssl:
                    _domain = self.env['kuber.domains'].sudo().browse(int(_domain_ssl.name))
                    domains_ssl.append([_domain_ssl.id, _domain.name])
        return domains_ssl

    def get_domains_ids(self, params):
        domains = []
        response = {'error':False, 'message':None, 'domains':domains}
        try:
            request.cr.execute(str("SELECT * from kuber_domains_sh_git_branch_rel ") + str("WHERE")+ str(" sh_git_branch_id=") + str(params['_branch_id']))
            _domains = request.cr.dictfetchall()
            if(len(_domains)>0):
                for domain in _domains:
                    _logger.warning(domain)
                    if('kuber_domains_id' in domain):
                        _domain = self.env['kuber.domains'].sudo().browse(int(domain['kuber_domains_id']))
                        domains.append(_domain.id)
                response['domains'] = domains
        except Exception as e:
            response = {"error":True, "message":"Could not get domains for branch. \n\n " + getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno) } # +" ON LINE "+format(sys.exc_info()[-1].tb_lineno)
            return response
        return response
            
    
    
    def create_domain_ssl_file(self, ssh, _repository, file_name, content, physical_server):
        _file = str("/home/kubernets/users/") + str(_repository.autor.id) + str("/") + str(_repository.id) + str("/ssl/") + str(file_name) + str(".ssl")    
        file_stream = open(str(_file),"w+")
        file_stream.write(str(content))
        file_stream.close()
        sftp = ssh.open_sftp()
        sftp.put(_file,_file)
        return _file
    
    def upstream_ssl_service(self, _file, ssh):
        command = str("cp -rf  ") + str(_file) + str(" /etc/nginx/sites-enabled")
        _logger.warning(command)
        stdin, stdout, stderr = ssh.exec_command(command)
        for line in iter(stdout.readline, ""):
            _logger.warning(line)
        for line in iter(stderr.readline, ""):
            _logger.warning(line)

        command = str("service nginx reload")
        _logger.warning(command)
        stdin, stdout, stderr = ssh.exec_command(command)
        for line in iter(stdout.readline, ""):
            _logger.warning(line)
        for line in iter(stderr.readline, ""):
            _logger.warning(line)

    def create_self_signed(self, _file_path, domain, ssh, callback_cert_path=""):
        crt_file = str(_file_path) + str("/") + str(domain.name) + str(".crt")
        key_file = str(_file_path) + str("/") + str(domain.name) + str(".key")

        command = str("echo 'CO' | openssl req -x509 -nodes -days 3650 -newkey rsa:2048 -keyout ") + str(key_file) + str(" -out ") + str(crt_file) + str(" -subj '/O=ROCKSCRIPTS/CN=sh.co'")        
        _logger.warning(':: Self Signed hostname')
        stdin, stdout, stderr = ssh.exec_command(command)
        for line in iter(stdout.readline, ""):
            _logger.warning(line)
        for line in iter(stderr.readline, ""):
            _logger.warning(line)
        _logger.warning(':: EOF')

        command = str("chmod 600 ") + str(key_file)
        stdin, stdout, stderr = ssh.exec_command(command)

        command = str("chmod 600 ") + str(crt_file)
        stdin, stdout, stderr = ssh.exec_command(command)

        physical_server = domain.branch.repository.so_server.physical_server
        if physical_server.ssh_host != '10.1.206.192' and physical_server.ssh_host != '172.17.0.1':
            _logger.warning(":::::::::NO SELF SH SERVER")
            sftp = ssh.open_sftp()
            sftp.get(str(crt_file), str(callback_cert_path) + str("/") + str(str(domain.name) + str(".crt")))
            sftp.get(str(crt_file), str(callback_cert_path) + str("/") + str(str(domain.name) + str(".key")))    
        else:
            _logger.warning(":::::::::SELF SH SERVER [SFTP Ignoring...]")  

        return {"crt_file":crt_file, "key_file":key_file}

    def upload_external_certificates(self, ssh, file_bytes, _file_path):
        _logger.warning("Writing certificate data to " + _file_path)
        try:
            sftp = ssh.open_sftp()
            with sftp.file(_file_path, 'wb') as file_to_save:
                file_to_save.write(file_bytes)
            sftp.close()
        except Exception as e:
            _logger.error("Failed to write certificate to path %s: %s", _file_path, e)
            raise Warning("Could not save uploaded file to path: " + _file_path)
        pass
    
    def tags_replace_matches_tpl(self, content, params):
        content = self.replace_tpl_tag(content, "<DOMAIN>", str(params['domain']))        
        content = self.replace_tpl_tag(content, "<CERTIFICATE>", str(params['crt_file']))  
        content = self.replace_tpl_tag(content, "<CERTIFICATE_KEY>", str(params['key_file']))
        return content

    def replace_tpl_tag(self, content, find, replace):
        content = str(self.env['kuber.template'].sudo().replace_tag(content,find,replace))
        return content
    
    def delete_domain_ssl(self, params):
        domains = []
        response = {'error':False, 'message':None, 'domains':domains}  
        try: 
            _branch = self.env["sh.git_branch"].sudo().browse(int(params['_branch_id'])) 
            _physical_server_id = _branch.repository.so_server.physical_server.id
            physical_server = self.env['sh.physical_server'].browse(_physical_server_id) 
            if(physical_server):
                ssh = self.get_ssh(physical_server)                
                _ssl_domain = self.sudo().browse(int(params['_domain_ssl_id']))                
                _domain = self.env['kuber.domains'].sudo().browse(int(_ssl_domain.name))
                _domain.update({"domain_ssl":None})
                _ssl_domain.sudo().unlink()
                _ssl_domains = self.qweb_get_domains_ssl(params)
                response['domains'] = _ssl_domains  
                self.delete_self_signed_certificate(ssh, str(_domain.name))       
                response["message"] = "SSL was removed for domain " + str(_domain.name) 
                ssh.close()
        except Exception as e:
            response = {"error":True, "message":"Could not delete ssl domain for branch selected. \n\n " + getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno) }
            return response
        return response
    
    def delete_self_signed_certificate(self, ssh, domain_name):
        command = str("certbot delete --cert-name ") + str(domain_name)
        _logger.warning(':: Removing Security Layer [SSL]')
        stdin, stdout, stderr = ssh.exec_command(command)
        for line in iter(stdout.readline, ""):
            _logger.warning(line)
        for line in iter(stderr.readline, ""):
            _logger.warning(line)
        _logger.warning(':: EOF SSL')


    def get_ssh(self, physical_server):
        try: 
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(str(physical_server.ssh_host), username=str(physical_server.user), password=str(physical_server.password), port=str(physical_server.port), look_for_keys=False, allow_agent=False)
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            return ssh
        except Exception as e:
            raise Warning(str("\n ID: ") + str(physical_server.id) + str("\n IP: ") + str(physical_server.ssh_host) + str("\n PORT: ") + str(physical_server.port) + str("\n USER: ") + str(physical_server.user) + str("\n MESSAGE: ") + getattr(e, 'message', repr(e)))
    