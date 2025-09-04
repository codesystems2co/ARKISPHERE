#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
from odoo import http
from random import randint
import xmlrpc.client
from github import Github
import sys
import logging
import paramiko
import time
import base64
_logger = logging.getLogger(__name__)

class sh_git_repository(models.Model):

    _inherit = "sh.git_repository"
    _description = "Repository"

    replicas = fields.Integer(string="Replicas", default=1)    
    kuber_deploy = fields.Many2one(comodel_name="kuber.deploy",  inverse_name="git_repository",  string="Kuber Deployment",  help="")
    kuber_dashboard_token = fields.Char(string="Dashboard Token")

    def restore_database(self, master_password, new_db_name, dbase64, hostname):
        server_proxy = xmlrpc.client.ServerProxy(str(hostname)+str('/xmlrpc/db'))
        try:
            server_proxy.restore(master_password, new_db_name, dbase64)
        except Exception as e:
            message = getattr(e, 'message', repr(e))
            _logger.warning(message)
            if '<Fault' in message:
                try:
                    message = str(message).split(':')[0]
                except:
                    pass
            return {'error':True, 'message':message}
        return {'error':False}
    
    def create_git_repository(self, params):        
        so_server = None
        if('_server_id' in params):
            so_server = request.env['so.server'].sudo().browse(int(params['_server_id']))            
            physical_server = request.env['sh.physical_server'].sudo().browse(int(so_server.physical_server.id))            
        else:
            physical_server = request.env['sh.physical_server'].sudo().search([], limit=1) 
        
        # validate if server credentials are correct for first experience
        ssh = None
        try:
            ssh = self.get_ssh(physical_server)
        except:
            # send mail report for crashing
            return {'error':True, 'message':_('Kindly, try in some minutes.')}
        
        _logger.info(':: Cheking Core Software')

        command = str("microk8s version")
        
        stdin, stdout, stderr = ssh.exec_command(command)

        for line in iter(stderr.readline, ""):
            return {'error':True, 'message':_('Kindly, We are installing core software in your server. try over 5-10 minutes')} 
        
        try:
            git_response =  super(sh_git_repository, self).create_git_repository(params)
            _logger.warning("_kuber_deployment >>>>")
            _logger.warning(params['_kuber_deployment'])
            _kuber_deployment = self.env['kuber.deploy'].sudo().browse(int(params['_kuber_deployment']))            
            _kuber_templates = self.env['kuber.template'].sudo().search([('kuber_deploy','=',int(params['_kuber_deployment']))], order='priority asc')
            _autor = self.env['git.autor'].sudo().browse(self.env.user.partner_id.id)
           
            if('_repository' in git_response): 
                _repository = git_response["_repository"]
                
                if so_server:
                    so_server.sudo().update({'git_repositories':int(_repository.id)})
                    _repository.sudo().update({'so_server':int(so_server.id)})

                _logger.warning("_kuber_deployment >>")
                _logger.warning(_kuber_deployment)

                self.env['sh.git_repository'].browse(_repository.id).sudo().update({'kuber_deploy':int(_kuber_deployment.id)})                
                # create deployment directory
                self.env['kuber.deploy'].sudo().create_user_deploy_dir(ssh, _repository)
                for _template in _kuber_templates:                    
                    self.env['kuber.deploy'].sudo().create_deployment_file(ssh, _repository, _template.name, _template.content, physical_server, apply=True)                        
                    self.env['kuber.deploy'].sudo().apply_deployment_file(ssh, _repository, _template.name)
                    if(_template.expose_public):                            
                        last_pod = self.env['kuber.deploy'].sudo().get(ssh, _repository, selectors={'app':_template.expose_selector}, _type=_template._type)
                        self.env['kuber.deploy'].sudo().delete(ssh, _repository, _template.expose_selector, _type='svc')                            
                        self.expose_cluster_custom(ssh, git_response['_branch'], _autor, _repository, last_pod['name'], _template._type, _template.app_port)                                            
                self.expose_cluster(git_response['_branch'], _autor, _repository, params['_kuber_deployment'])    
                
                # custom commands for a branch, then replicate                    
                self.env['kuber.commands'].sudo().execute_command_on_deploy(_kuber_deployment, git_response['_branch'])
                # restore from outsource
                if 'database64' in params:
                    is_ready = False
                    while is_ready==False:
                        command = "/snap/bin/microk8s.kubectl get pod " + str(git_response['_branch'].kuber_exposers.cluster_selector) + "  -o jsonpath='{.status.phase}' -n " + str(git_response['_branch'].repository.autor.username) + str(git_response['_branch'].repository.id)
                        _logger.warning('exec_command >>')
                        _logger.warning(command)
                        stdin, stdout, stderr = ssh.exec_command(command)
                        for line in iter(stdout.readline, ""):
                            _logger.warning('exec_command line >>')
                            _logger.warning(line)
                            if line == 'Running':
                                is_ready = True  
                                # upload database from external client source      
                                database = str(git_response['_branch'].repository.autor.username) + str(git_response['_branch'].repository.id)            
                                hostname = git_response['_branch'].kuber_exposers.domain if git_response['_branch'].kuber_exposers.domain else git_response['_branch'].kuber_exposers.ip
                                service_hostname = str('http://') + str(hostname) + str(':')+ str(git_response['_branch'].kuber_exposers.port)
                                odoo_conf = '/data/uid' + str(git_response['_branch'].repository.autor.id) + str('/')  + str(git_response['_branch'].repository.autor.username) + str(git_response['_branch'].repository.id) + str('v1/odoo.conf')            
                                admin_password = self.get_admin_password(odoo_conf, ssh)
                                self.restore_database(admin_password,database, str((params['database64'])).replace('data:application/zip;base64,',''), service_hostname)
                                # clone repository main branch sha to deploy pod 
                                self.env["sh.git_branch"].sudo().restore_external_project(git_response['_branch'],ssh)
            ssh.close()
            return git_response
        except Exception as e:
            git_response = {"error":True, "message":"Could not expose branch \n\n " + getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno)}
            _logger.warning(git_response)
    
    def expose_cluster_custom(self, ssh , _branch, _autor, _repository, identifier, _type='pod', tarjet_port=8080):
        kuber_exposer = self.env['kuber.exposer'].sudo().search([('git_branch','=',None)],limit=1)
        if(not kuber_exposer):
            so_server = self.env['so.server'].sudo().browse(int(_repository.so_server.id))
            _physical_server_id = int(so_server.physical_server.id)
            physical_server = self.env['sh.physical_server'].browse(_physical_server_id)
            next_exposer = self.get_next_exposer()
            kuber_exposer = self.env['kuber.exposer'].create({
                                                                "name": next_exposer['name'],
                                                                "ip": physical_server.ssh_host, 
                                                                "port": next_exposer['port'], 
                                                                "physical_server": physical_server.id,
                                                                "git_branch": _branch.id,
                                                             })
        kuber_exposer.sudo().update({'git_branch':_branch.id,'cluster_selector_type':_type,'cluster_selector':identifier})
        command = str("/snap/bin/microk8s.kubectl expose ") + str(_type) + str(" ") + str(identifier) + str(' --external-ip=') + str(kuber_exposer.ip) + str(" --target-port=")+ str(tarjet_port)+ str(' --port=') + str(kuber_exposer.port) + str(' --type=LoadBalancer -n ') + str(str(_autor.username) + str(_repository.id))        
        stdin, stdout, stderr = ssh.exec_command(command)
        for line in iter(stdout.readline, ""):
            _logger.warning(line)
        for line in iter(stderr.readline, ""):
            _logger.warning(line)
    # just work for odoo on 8069 port
    def expose_cluster(self, _branch, _autor, _repository, kuber_deploy_id, new_branch=False):
        try:            
            so_server = self.env['so.server'].sudo().browse(int(_repository.so_server.id))
            physical_server_id = int(so_server.physical_server.id)
            physical_server = self.env['sh.physical_server'].sudo().browse(physical_server_id)
            ssh = self.get_ssh(physical_server)
            if(_branch):
                _kuber_docker_image = _repository.kuber_deploy.kuber_docker_image
                time.sleep(5)                
                last_pod = self.env['kuber.deploy'].sudo().get(ssh, _repository, selectors={'app':_kuber_docker_image.name, 'tier':'frontend'}, _type='pod')
                last_pod_name = last_pod['name']
                if new_branch:
                    last_pod_name = _branch.kuber_identifier_name
                
                    
                _branch.sudo().update({'kuber_identifier_name':last_pod_name})
                self.env['kuber.deploy'].sudo().assing_label(ssh, _repository, last_pod_name, _type='pod', labels=str('branch=')+str(_branch.id))
                self.env['kuber.deploy'].sudo().assing_label(ssh, _repository, last_pod_name, _type='pod', labels=str('branch_name=')+str(_branch.name))
                
                so_server = self.env['so.server'].browse(int(_branch.repository.so_server.id))
                _physical_server_id = int(so_server.physical_server.id)
                physical_server = self.env['sh.physical_server'].browse(_physical_server_id) 
                next_exposer = self.get_next_exposer()
                kuber_exposer = self.env['kuber.exposer'].sudo().create({
                                                                            "name": next_exposer['name'],
                                                                            "ip": physical_server.ssh_host,
                                                                            "port": next_exposer['port'],
                                                                            "physical_server": physical_server.id,
                                                                            "git_branch": _branch.id,
                                                                        })
                if(kuber_exposer):
                    time.sleep(3)
                    self.env['kuber.deploy'].sudo().expose_public(ssh, _repository, last_pod_name, kuber_exposer.ip, kuber_exposer.port, tarjet_port=8069, _type='pod')                                    
                    _branch.sudo().update({'kuber_exposers':kuber_exposer.id})
                    kuber_exposer.sudo().update({'git_branch':_branch.id,'cluster_selector_type':'pod','cluster_selector':last_pod_name,'selector_label':str('frontend')})
            ssh.close()
        except Exception as e:
            git_response = {"error":True, "message":"Could not expose branch \n\n " + getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno)}
            _logger.warning(git_response)

    def get_sh_physical_server(self, so_id):
        self._cr.execute('select * from so_server where id = ' + str(so_id))
        _so_server = self._cr.dictfetchone()
        return _so_server['physical_server']

    def get_next_exposer(self):
        exposer = None
        try: 
            random_port = randint(1000, 9999)
            exposer = {"name": str("Service-") + str(random_port), "port":random_port}
        except Exception as e:
            error = {"error":True, "message":"Could not generate random port \n\n " + getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno)}
            _logger.warning(error)
        return exposer
    
    def kb_open_dashboard(self):
        response = self.env["sh.git_repository"].sudo().open_dashboard({'id':self.id})
        self.kuber_dashboard_token = response['token']
        time.sleep(5)
        return {
                'type':'ir.actions.act_url',
                'url': 'https:'+str(response['hostname']),
                'target': 'new'
               }
    
    def open_dashboard(self, params = None):
        
        if params:
            self = request.env["sh.git_repository"].sudo().browse(int(params['id']))

        so_server = self.env['so.server'].sudo().browse(int(self.so_server.id))
        physical_server_id = int(so_server.physical_server.id)
        physical_server = self.env['sh.physical_server'].sudo().browse(physical_server_id)
        ssh = self.get_ssh(physical_server)

        _logger.info(':: Installing kubernetes dashboard >>')
        command = str("/snap/bin/microk8s.enable dashboard")
        stdin, stdout, stderr = ssh.exec_command(command)
        for line in iter(stdout.readline, ""):
            _logger.warning(line)
        for line in iter(stderr.readline, ""):
            _logger.warning(line)

        _logger.info(':: Installing get secret token to login >>')
        command = str("/snap/bin/microk8s.kubectl describe secret -n kube-system microk8s-dashboard-token")
        stdin, stdout, stderr = ssh.exec_command(command)
        for line in iter(stdout.readline, ""):
            if 'token:' in str(line):
                self.kuber_dashboard_token = str(str(line).split(':')[1]).strip()
                _logger.warning(self.kuber_dashboard_token)
        for line in iter(stderr.readline, ""):
            _logger.warning(line)  

        _logger.info(':: Publishing for internal ip >>')

        command = str("/snap/bin/microk8s kubectl delete svc admin -n kube-system")
        stdin, stdout, stderr = ssh.exec_command(command)

        command = str("/snap/bin/microk8s.kubectl expose svc kubernetes-dashboard -n kube-system --type=LoadBalancer --name=admin --port=8443 --target-port=8443 --external-ip="+str(physical_server.ip))
        stdin, stdout, stderr = ssh.exec_command(command)
        for line in iter(stdout.readline, ""):
            _logger.warning(line)
        for line in iter(stderr.readline, ""):
            _logger.warning(line)        

        return {'token':self.kuber_dashboard_token, 'hostname':str(physical_server.ip) + str(':8443/#/workloads?namespace=')+str(self.autor.username)+str(self.id)}
        
    def init_portfoward(self, params = None):
        if params:
            self = request.env["sh.git_repository"].sudo().browse(int(params['id']))
            so_server = self.env['so.server'].sudo().browse(int(self.so_server.id))
            physical_server_id = int(so_server.physical_server.id)
            physical_server = self.env['sh.physical_server'].sudo().browse(physical_server_id)
            ssh = self.get_ssh(physical_server)
            try:            
                _logger.info(':: publishing dashboard  port-forward >>')
                command = str("kill -9 $(lsof -t -i:1443)")
                stdin, stdout, stderr = ssh.exec_command(command)
                for line in iter(stdout.readline, ""):
                    _logger.warning(line)
                for line in iter(stderr.readline, ""):
                    _logger.warning(line)
            except:
                pass

            try:
                command = str("/snap/bin/microk8s.kubectl delete svc admin  -n kube-system")
                stdin, stdout, stderr = ssh.exec_command(command)
                for line in iter(stdout.readline, ""):
                    _logger.warning(line)
                for line in iter(stderr.readline, ""):
                    _logger.warning(line)
            except:
                pass
            
            try:
                command = str("/snap/bin/microk8s.kubectl port-forward -n kube-system service/kubernetes-dashboard 1443:443 --address 0.0.0.0")
                stdin, stdout, stderr = ssh.exec_command(command)
                for line in iter(stdout.readline, ""):
                    _logger.warning(line)
                for line in iter(stderr.readline, ""):
                    _logger.warning(line)
            except:
                pass
    
    def get_admin_password(self, odoo_conf, ssh):
        admin_password = None

        command = "test -e " + str(odoo_conf) + " && echo exist || echo noExist"
        _logger.warning('exist odoo.conf command >>')
        _logger.warning(command)
        stdin, stdout, stderr = ssh.exec_command(command)
        for line in iter(stdout.readline, ""):
            if line == 'noExist':
                return None
    
        command = "grep -r 'admin' " + str(odoo_conf) + " | awk -F= '{print $2}'"
        _logger.warning('get_admin_password command >>')
        _logger.warning(command)
        stdin, stdout, stderr = ssh.exec_command(command)
        for line in iter(stdout.readline, ""):
            admin_password = line
        return str(admin_password).strip()

    def get_ssh(self, physical_server):
        try: 
            ssh = paramiko.SSHClient()
            _logger.warning(str('SSH credentials:'))
            _logger.warning(str(physical_server.ssh_host))
            _logger.warning(str(physical_server.user))
            _logger.warning(str(physical_server.password))
            _logger.warning(str(physical_server.port))

            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(str(physical_server.ssh_host), username=str(physical_server.user), password=str(physical_server.password), port=str(physical_server.port), look_for_keys=False, allow_agent=False)
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            return ssh
        except Exception as e:
            raise Warning(str("\n ID: ") + str(physical_server.id) + str("\n IP: ") + str(physical_server.ssh_host) + str("\n PORT: ") + str(physical_server.port) + str("\n USER: ") + str(physical_server.user) + str("\n MESSAGE: ") + getattr(e, 'message', repr(e)))