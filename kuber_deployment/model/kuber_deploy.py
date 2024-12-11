#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
from odoo import http
import paramiko
import logging
import os
import sys
import time
_logger = logging.getLogger(__name__)

class kuber_deploy(models.Model):

    _name = "kuber.deploy"
    _description = "Kuber Deployment"
    name = fields.Char( required=True, string="Name",  help="")
    identifier = fields.Char( string="Identifier",  help="")

    kuber_docker_image = fields.Many2one(comodel_name="kuber.docker_image",  inverse_name="kuber_deploy",  string="Built",  help="")
    kuber_template = fields.Many2many(comodel_name="kuber.template",  inverse_name="kuber_deploy",  string="Kuber template",  help="")
    git_repositories = fields.One2many(comodel_name="sh.git_repository",  inverse_name="kuber_deploy",  string="",  help="")
    product_template = fields.Many2one(comodel_name="product.template",  inverse_name="kuber_deployments",  string="Product Template",  help="")
    kuber_commands = fields.One2many(comodel_name="kuber.commands",  inverse_name="kuber_deployments",  string="Commands",  help="")

    def get_deployments(self, params=None):
        so_server_id = None
        if(params):
            if('_so_server' in  params):
                so_server_id = params['_so_server']
        response = {'error':'True', 'deployments':[]}
        _active_deployments = []
        uid = http.request.env.context.get('uid')
        partner_id = self.env['res.users'].browse(uid).partner_id.id
        _orders = self.env["sale.order"].search([('partner_id','=',partner_id)])
        for _order in _orders:
            _order_lines = request.env["sale.order.line"].sudo().search([
                                                                            ('order_id','=',_order.id)  ,
                                                                            ('is_kube_core_installed','=',True)              
                                                                        ])
            for _order_line in _order_lines:   
                _order_line = request.env["sale.order.line"].sudo().browse(_order_line.id)
                if _order_line.so_server:
                    product = request.env["product.product"].sudo().browse(_order_line.product_id.id)
                    product_template = request.env["product.template"].sudo().browse(product.product_tmpl_id.id)
                    if(product_template.kuber_deployments):
                        for kuber_deployment in product_template.kuber_deployments:
                            _kuber_deployment = self.sudo().browse(kuber_deployment.id)
                            already_deployed =_kuber_deployment.git_repositories.sudo().search([('so_server','=',int(_order_line.so_server.id))])
                            if not already_deployed:
                                if(so_server_id):
                                    if(int(_order_line.so_server.id) == int(so_server_id)):
                                        _active_deployments.append({"id":_kuber_deployment.id, "name":_kuber_deployment.name, "so_server":_order_line.so_server.name})
                                else:
                                    _active_deployments.append({"id":_kuber_deployment.id, "name":_kuber_deployment.name, "so_server":_order_line.so_server.name})
                            

        if(len(_active_deployments)>0):
            response['deployments'] = _active_deployments     
        return response

    def create_user_deploy_dir(self, ssh, _repository):
        try:
            # create deployment directory
            client_deployment_path = str("/home/kubernets/users/") + str(_repository.autor.id) + str("/") + str(_repository.id)
            _logger.warning("STEP 1")
            if (not os.path.isdir(str("/home/kubernets"))):
                os.mkdir(str("/home/kubernets"))
            command = str("mkdir ") + str("/home/kubernets")
            stdin, stdout, stderr = ssh.exec_command(command)
            _logger.warning(stdout)
            
            if (not os.path.isdir(str("/home/kubernets/users"))):
                os.mkdir(str("/home/kubernets/users"))

            command = str("mkdir -m 777 ") + str("/home/kubernets/users")
            stdin, stdout, stderr = ssh.exec_command(command)
            _logger.warning(stdout)

            if (not os.path.isdir(str(str("/home/kubernets/users/") + str(_repository.autor.id)))):
                try:
                    os.mkdir(str(str("/home/kubernets/users/") + str(_repository.autor.id)))
                except:
                    pass
            command = str("mkdir -m 777 ") + str(str("/home/kubernets/users/") + str(_repository.autor.id))
            stdin, stdout, stderr = ssh.exec_command(command)
            _logger.warning(stdout)

            if (not os.path.isdir(str(str("/home/kubernets/users/") + str(_repository.autor.id) + str("/") + str(_repository.id)))):
                try:
                    os.mkdir(str(client_deployment_path))
                except:
                    pass
            command = str("mkdir -m 777 ") + client_deployment_path
            stdin, stdout, stderr = ssh.exec_command(command)

            if (not os.path.isdir(str(str("/home/kubernets/users/") + str(_repository.autor.id) + str("/") + str(_repository.id) + str("/ssl")))):
                try:
                    os.mkdir(str(client_deployment_path))
                except:
                    pass
            command = str("mkdir -m 777 ") + client_deployment_path + str("/ssl")
            stdin, stdout, stderr = ssh.exec_command(command)
            _logger.warning(stdout)
            
        except Exception as e:
            _exception = {"error":True, "message":"Could not create deploy directory \n\n " + getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno)}
            _logger.warning(_exception)
    
    def create_deployment_file(self, ssh, _repository, file_name, content, physical_server, apply=False):
        try:
            # tags replacement on deployments templates
            content = self.tags_replace_matches_tpl(content, _repository)
            _dir = str("/home/kubernets/users/") + str(_repository.autor.id) + str("/") + str(_repository.id)
            ssh.exec_command("chmod -R 777 " + _dir)
            _file = str("/home/kubernets/users/") + str(_repository.autor.id) + str("/") + str(_repository.id) + str("/") + str(file_name) + str(".yaml")        
            file_stream = open(str(_file),"w+")
            file_stream.write(str(content))
            file_stream.close()
            
            if physical_server.ssh_host != '10.1.206.192' and physical_server.ssh_host != '172.17.0.1':
                _logger.warning(":::::::::NO SELF SH SERVER")
                _logger.warning(physical_server.ssh_host)
                sftp = ssh.open_sftp()
                sftp.put(_file,_file)
        except Exception as e:
            _exception = {"error":True, "message":"Could not create deploy file \n\n " + getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno)}
            _logger.warning(_exception)

    def apply_deployment_file(self, ssh, _repository, file_name):
        _file = str("/home/kubernets/users/") + str(_repository.autor.id) + str("/") + str(_repository.id) + str("/") + str(file_name) + str(".yaml")
        command = str("/snap/bin/microk8s.kubectl apply -f ") + str(_file)   
        _logger.warning(command)
        stdin, stdout, stderr = ssh.exec_command(command)
        for line in iter(stdout.readline, ""):
            _logger.warning(line)
        for line in iter(stderr.readline, ""):
            _logger.warning(line)        

    # selectors={'app':None,'branch':None}
    def get(self, ssh, _repository, selectors={'app':None}, _type='pod'):
        response = {'name':None,'ready': None, 'status': None, 'restarts': None, 'age': None}
        try:           
            _filter = str('')
            i = 0
            for selector in selectors:
                if(i==0):
                    _filter += str(selector) + str('=') + str(selectors[selector])
                else:  
                    _filter += str(',') + str(selector) + str('=') + str(selectors[selector])       
                i += 1
            time.sleep(5)
            command = str('/snap/bin/microk8s.kubectl get ') + str(_type) + str(' -l ') + str(_filter) + str(' -n ') + str(str(_repository.autor.username) + str(_repository.id))
            _logger.warning(command) 
            stdin, stdout, stderr = ssh.exec_command(command)

            #log errors
            _logger.warning("ERRORS")
            for line in iter(stderr.readline, ""):
                _logger.warning(line)

            i = 0
            _items = []
            _logger.warning("OUT")
            for line in iter(stdout.readline, ""):
                _logger.warning(line)
                _items.append(line)
                i += 1
            last_item = None    
            _logger.warning(_items) 
            if(len(_items)>0):
                last_item = str(_items[len(_items)-1]).split(" ")
                response['name'] = str(last_item[0]).strip()
                response['ready'] = str(last_item[1]).strip()
                response['status'] = str(last_item[2]).strip()
                response['restarts'] = str(last_item[3]).strip()
                response['age'] = str(last_item[4]).strip()   

            _logger.warning("POD RESPONSE") 
            _logger.warning(response)      
        except Exception as e:
            git_response = {"error":True, "message":"Could not get pod service\n\n " + getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno)}
            _logger.warning(git_response)
        return response

    def delete(self, ssh, _repository, selector, _type='pod'):
        command = str('/snap/bin/microk8s.kubectl delete ') + str(_type) + str(' ') + str(selector) + str(' -n ') + str(str(_repository.autor.username) + str(_repository.id))
        _logger.warning(command)    
        stdin, stdout, stderr = ssh.exec_command(command)
        for line in iter(stdout.readline, ""):
            _logger.warning(line)
        for line in iter(stderr.readline, ""):
            _logger.warning(line)
    
    def scale(self, ssh, _repository, selector, replicas, _type='pod'):
        command = str('/snap/bin/microk8s.kubectl scale --replicas=') + str(replicas) + str(' ') + str(_type) + str('/') + str(selector) + str(' ') + str(' -n ') + str(str(_repository.autor.username) + str(_repository.id))
        _logger.warning(command)    
        stdin, stdout, stderr = ssh.exec_command(command)
        for line in iter(stdout.readline, ""):
            _logger.warning(line)
        for line in iter(stderr.readline, ""):
            _logger.warning(line)
    
    # @param labels : branch=50, other_label=43
    def assing_label(self, ssh, _repository, selector, _type='pod', labels=None):
        command = str('/snap/bin/microk8s.kubectl label --overwrite ') + str(_type) + str(' ') + str(selector) + str(' ') + str(labels) + str(' -n ') + str(str(_repository.autor.username) + str(_repository.id))
        _logger.warning(command) 
        stdin, stdout, stderr = ssh.exec_command(command)
        for line in iter(stdout.readline, ""):
            _logger.warning(line)
        for line in iter(stderr.readline, ""):
            _logger.warning(line)

    def expose_public(self, ssh, _repository, selector, external_ip, port, tarjet_port=8069, _type='pod'):
        command = str('/snap/bin/microk8s.kubectl expose') + str(" ") + str(_type) + str(" ") + str(selector) + str(' --external-ip=') + str(external_ip) + str(" ") + str('--port=') + str(port) + str(' --target-port=') + str(tarjet_port) + str(' --type=LoadBalancer -n ') + str(str(_repository.autor.username) + str(_repository.id))
       
        _logger.warning("BG ::::::::: EXPOSING PUBLIC SERVICE >>>>>>>>>")
        _logger.warning(command)
        stdin, stdout, stderr = ssh.exec_command(command)
        for line in iter(stdout.readline, ""):
            _logger.warning(line)
        for line in iter(stderr.readline, ""):
            _logger.warning(line)
        _logger.warning("EOF ::::::::: EXPOSING PUBLIC SERVICE >>>>>>>>>")

        for line in iter(stdout.readline, ""):
            _logger.warning(line)
        for line in iter(stderr.readline, ""):
            _logger.warning(line)

    def get_app_logs(self, branch_id):
        _branch = self.env["sh.git_branch"].sudo().browse(int(branch_id))
        physical_server = _branch.repository.so_server.physical_server
        app_logs = str()
        if(physical_server):
            ssh = self.get_ssh(physical_server)   

            command = "ls /var/log/pods/" + str(str(_branch.repository.autor.username) + str(_branch.repository.id)) + str("_") + str(_branch.kuber_exposers.cluster_selector) + str("_*/odoo/")
            _logger.warning(command)
            last_log_file = str()
            stdin, stdout, stderr = ssh.exec_command(command)
            for line in iter(stdout.readline, ""):                
                last_log_file = str(line)

            command = "tail -n 100 /var/log/pods/" + str(str(_branch.repository.autor.username) + str(_branch.repository.id)) + str("_") + str(_branch.kuber_exposers.cluster_selector) + str("_*/odoo/") + str(last_log_file)
            _logger.warning(command)
            stdin, stdout, stderr = ssh.exec_command(command)
            for line in iter(stdout.readline, ""):                
                app_logs = str(app_logs) + str(line) + str('</br>')
            _logger.warning(app_logs)

            ssh.close()

        return app_logs


    def replace_tpl_tag(self, content, find, replace):
        content = str(self.env['kuber.template'].replace_tag(content,find,replace))
        return content   
        
    def execute_command(self, _command, _branch):
        _physical_server_id = _branch.repository.so_server.physical_server.id
        _logger.warning("_physical_server_id")
        _logger.warning(_physical_server_id)
        physical_server = self.env['sh.physical_server'].sudo().browse(_physical_server_id)
        if(physical_server):
            ssh = self.get_ssh(physical_server)    
            command = "/snap/bin/microk8s.kubectl exec -i " + str(_branch.kuber_exposers.cluster_selector) + " -n " + str(_branch.repository.autor.username) + str(_branch.repository.id) + " -- /bin/bash -c " + str(_command)
            _logger.warning(command)
            stdin, stdout, stderr = ssh.exec_command(command)
            for line in iter(stdout.readline, ""):
                _logger.warning(line)
            for line in iter(stderr.readline, ""):
                _logger.warning(line)     

    def tags_replace_matches_tpl(self, content, _repository):
        content = self.replace_tpl_tag(content, "<NAMESPACE>", str(_repository.autor.username) + str("") + str(_repository.id))
        # volumen on file system 1
        content = self.replace_tpl_tag(content, "<VOLUME-FILESYSTEM-1>", str(str(_repository.autor.username) + str("") + str(_repository.id) + str("v1")))
        # volumen on file system 2
        content = self.replace_tpl_tag(content, "<VOLUME-FILESYSTEM-2>", str(str(_repository.autor.username) + str("") + str(_repository.id) + str("v2")))
        # persistant volumen claim on file system 1
        content = self.replace_tpl_tag(content, "<VOLUMEN-CLAIM-1>", str(str(_repository.autor.username) + str("") + str(_repository.id) + str("pv1")))
        # persistant volumen claim on file system 2
        content = self.replace_tpl_tag(content, "<VOLUMEN-CLAIM-2>", str(str(_repository.autor.username) + str("") + str(_repository.id) + str("pv2")))
        # client
        content = self.replace_tpl_tag(content, "<CLIENT>", str("uid")+str(_repository.autor.id))

        content = self.replace_tpl_tag(content, "<CLIENT-USERNAME>", str(_repository.autor.username))
        
        content = self.replace_tpl_tag(content, "<CLIENT-PASSWORD>", str(_repository.autor._gpassword))

        ssd = str(_repository.so_server.disk_size_gb).replace('GB','') + str('Gi')
        content = self.replace_tpl_tag(content, "<SSD>", str(ssd))
        
        return content
    
    def get_ssh(self, physical_server):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(str(physical_server.ssh_host), username=str(physical_server.user), password=str(physical_server.password), port=str(physical_server.port), look_for_keys=False, allow_agent=False)
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            return ssh
        except Exception as e:
            raise Warning(str("\n ID: ") + str(physical_server.id) + str("\n IP: ") + str(physical_server.ssh_host) + str("\n PORT: ") + str(physical_server.port) + str("\n USER: ") + str(physical_server.user) + str("\n MESSAGE: ") + getattr(e, 'message', repr(e)))