#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
from odoo import http
from github import Github
import sys
import logging
import paramiko
import time
_logger = logging.getLogger(__name__)

class sh_git_branch(models.Model):

    _inherit = "sh.git_branch"
    _description = "Branch"

    kuber_exposers = fields.Many2one(comodel_name="kuber.exposer",  inverse_name="git_branch",  string="Exposer",  help="")
    kuber_identifier_name = fields.Char(string='Kuber Identifier Name')
    kuber_commands = fields.Many2many(comodel_name="kuber.commands",  inverse_name="branch",  string="Commands",  help="", ondelete="cascade")
    kuber_domains = fields.Many2many(comodel_name="kuber.domains",  inverse_name="branch",  string="Domains",  help="", ondelete="cascade")

    # set branch id to front end deployment
    def create_sh_project_branch(self, _branch, _autor, _repository):
        _logger.warning("KUBER BRANCH FROM")
        new_branch =  super(sh_git_branch, self).create_sh_project_branch(_branch, _autor, _repository)
        # just applyes for developments stages created directly from a branch
        _logger.warning(new_branch)
        _logger.warning("KUBER BRANCH FROM CONDITION")
        
        try:
            so_server = self.env['so.server'].sudo().browse(int(_repository.so_server.id))
            _logger.warning(so_server)
            physical_server_id = int(so_server.physical_server.id)
            physical_server = self.env['sh.physical_server'].sudo().browse(physical_server_id)   
            ssh = self.get_ssh(physical_server)
            _logger.warning('new_branch')
            _logger.warning(new_branch)
            if(new_branch):
                last_deployment = self.env['kuber.deploy'].sudo().get(ssh, _repository, selectors={'app':_repository.kuber_deploy.kuber_docker_image.name, 'tier':'frontend'}, _type='deployment')
                _logger.warning("last_deployment")
                _logger.warning(last_deployment)
                self.env['kuber.deploy'].sudo().scale(ssh, _repository, last_deployment['name'] ,str(int(_repository.replicas)+int(1)), _type='deployment')
                _repository.sudo().update({'replicas': (int(_repository.replicas)+int(1))})

                _kuber_deployment = self.env['kuber.deploy'].sudo().browse(_repository.kuber_deploy.id)
                _logger.warning(_kuber_deployment)        
                _kuber_docker_image = self.env['kuber.docker_image'].sudo().browse(_kuber_deployment.kuber_docker_image.id)
                _logger.warning(_kuber_docker_image)  
                time.sleep(5)  
                last_pod = self.env['kuber.deploy'].sudo().get(ssh, _repository, selectors={'app':_kuber_docker_image.name, 'tier':'frontend'}, _type='pod')
                _logger.warning("last_pod")
                _logger.warning(last_pod)
                new_branch.sudo().update({'kuber_identifier_name':last_pod['name']})
                time.sleep(3)
                self.env['kuber.deploy'].sudo().assing_label(ssh, _repository, last_pod['name'], _type='pod', labels=str('branch=')+str(new_branch.id))
                time.sleep(3)
                self.env['kuber.deploy'].sudo().assing_label(ssh, _repository, last_pod['name'], _type='pod', labels=str('branch_name=')+str(new_branch.name))
                kuber_exposer = self.env['kuber.exposer'].sudo().search([('git_branch','=',None)],limit=1)
                if(kuber_exposer):
                    time.sleep(3)
                    self.env['kuber.deploy'].sudo().expose_public(ssh, _repository, last_pod['name'], kuber_exposer.ip, kuber_exposer.port, tarjet_port=8069, _type='pod')                
                    new_branch.sudo().update({'kuber_exposers':kuber_exposer.id})
                    # ,'cluster_selector_type':_type,'cluster_selector':identifier
                    kuber_exposer.sudo().update({'git_branch':new_branch.id,'cluster_selector_type':'pod','cluster_selector':last_pod['name'],'selector_label':str('frontend')})                   

                _logger.warning("DEBUGGER")
                _logger.warning(last_pod)
        except Exception as e:
            _logger.warning("DEBUGGER 3")
            git_response = {"error":True, "message":"Could not create branch \n\n " + getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno)}
            _logger.warning(git_response)
        return new_branch

    def create_git_repository_branch_from(self, params):
        _git_response =  super(sh_git_branch, self).create_git_repository_branch_from(params)   
        _logger.warning("_git_response::")
        _logger.warning(_git_response)
        new_branch = _git_response['_branch']
        self.env['sh.git_repository'].sudo().expose_cluster(new_branch, new_branch.repository.autor, new_branch.repository, new_branch.repository.kuber_deploy.id, True)
        self.env['kuber.commands'].sudo().execute_command_on_deploy(new_branch.repository.kuber_deploy, new_branch)
        return _git_response
    
    def restore_external_project(self, branch, ssh):
        addons_path = str('/data/uid') + str(branch.repository.autor.id) + str('/') + str(branch.repository.autor.username) + str(branch.repository.id) + str('v1/addons/') 
        addons_version = str(branch.repository.kuber_deploy.kuber_docker_image.version)
        clone_command = str('cd ') + str(addons_path) + str(' && ') + str(' git clone -b ') + str(branch.name) + str(' https://') + str(branch.repository.autor.access_token) + str('@github.com/') + str(branch.repository.autor.username) + str('/') + str(branch.repository.name) + str('.git')
        remove_command = str('rm -rf ') + str(addons_path) + str(addons_version)
        set_command = str('mv -f ') + str(addons_path) + str(branch.repository.name) + str(' ') + str(addons_path) + str(addons_version)
                
        _logger.warning('exec_command clone_command>>')
        _logger.warning(clone_command)
        stdin, stdout, stderr = ssh.exec_command(clone_command)
        for line in iter(stdout.readline, ""):
            _logger.warning('clone_command line success>>')
            _logger.warning(line)
        for line in iter(stderr.readline, ""):
            _logger.warning('clone_command line error>>')
            _logger.warning(line)
        
        _logger.warning('exec_command remove_command>>')
        _logger.warning(remove_command)
        stdin, stdout, stderr = ssh.exec_command(remove_command)
        for line in iter(stdout.readline, ""):
            _logger.warning('remove_command line success>>')
            _logger.warning(line)
        for line in iter(stderr.readline, ""):
            _logger.warning('remove_command line error>>')
            _logger.warning(line)
        
        _logger.warning('exec_command set_command>>')
        _logger.warning(set_command)
        stdin, stdout, stderr = ssh.exec_command(set_command)
        for line in iter(stdout.readline, ""):
            _logger.warning('set_command line success>>')
            _logger.warning(line)
        for line in iter(stderr.readline, ""):
            _logger.warning('set_command line error>>')
            _logger.warning(line)


    def get_sh_physical_server(self, so_id):
        self._cr.execute('select * from so_server where id = ' + str(so_id))
        _so_server = self._cr.dictfetchone()
        return _so_server['physical_server']

    def get_ssh(self, physical_server):
        try: 
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(str(physical_server.ssh_host), username=str(physical_server.user), password=str(physical_server.password), port=str(physical_server.port), look_for_keys=False, allow_agent=False)
            return ssh
        except Exception as e:
            raise Warning(str("\n ID: ") + str(physical_server.id) + str("\n IP: ") + str(physical_server.ssh_host) + str("\n PORT: ") + str(physical_server.port) + str("\n USER: ") + str(physical_server.user) + str("\n MESSAGE: ") + getattr(e, 'message', repr(e)))
    
    def assign_collaborator(self, params):    
        collaborators = [] 
        response = {'error':False, 'message':None, 'collaborators':collaborators}  
        try:        
                
            branch = self.env['sh.git_branch'].sudo().browse(int(params['_branch_id']))
            invited_autor = self.env['res.partner'].sudo().search([('username','=',str(params['_autor_name']))], limit=1)
            if invited_autor:
                invited_autor.sudo().update({'is_collaborator':True})
                branch.sudo().update({'collaborators':[(4,invited_autor.id)]})
                response['message'] = str('Collaborator added to branch (') + str(branch.name) + str(")")
                for collaborator in branch.collaborators:
                    collaborators.append([collaborator.id, collaborator.username])
                response['collaborators'] = collaborators
            else:
                response = {"error":True, "message": _("Collaborator does not exist in our records. \n\n Kindly, invite to sign up with github account.")}
                return response  
        except Exception as e:
            response = {"error":True, "message":"Could not assign collaborator to branch. \n\n " + getattr(e, 'message', repr(e)) } # +" ON LINE "+format(sys.exc_info()[-1].tb_lineno)
            return response
        return response

    def get_collaborators(self, params):
        collaborators = [] 
        response = {'error':False, 'message':None, 'collaborators':collaborators}  
        try:
            request.cr.execute(str("SELECT * from res_partner_sh_git_branch_rel ") + str("WHERE")+ str(" sh_git_branch_id=") + str(params['_branch_id']))
            _collaborators = request.cr.dictfetchall()
            if(len(_collaborators)>0):
                for collaborator in _collaborators:
                    _logger.warning(collaborator)
                    if('res_partner_id' in collaborator):
                        autor = self.env['res.partner'].sudo().browse(int(collaborator['res_partner_id']))
                        collaborators.append([autor.id, autor.username])
                response['collaborators'] = collaborators
        except Exception as e:
            response = {"error":True, "message":"Could not assign collaborator to branch. \n\n " + getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno) } # +" ON LINE "+format(sys.exc_info()[-1].tb_lineno)
            return response
        return response

    def unssign_collaborator(self, params):
        collaborators = [] 
        response = {'error':False, 'message':None, 'collaborators':collaborators}  
        try: 
            branch = self.env['sh.git_branch'].sudo().browse(int(params['_branch_id']))
            branch.sudo().update({'collaborators':[(4,str(params['_autor_id']))]})

            request.cr.execute(str("DELETE from res_partner_sh_git_branch_rel ") + str("WHERE res_partner_id=") + str(params['_autor_id']) + str(" AND ") + str("sh_git_branch_id=") + str(params['_branch_id']))
            
            response_collaborators = self.get_collaborators(params)
            _logger.warning(response_collaborators)
            response['collaborators'] = response_collaborators['collaborators']
        except Exception as e:
            response = {"error":True, "message":"Could not unassign collaborator to branch. \n\n " + getattr(e, 'message', repr(e)) }
            return response
        return response

    def restart_branch(self, params):
        response = {'error':False, 'message':"Service was restarted successful."}  
        try:
            _repository = self.env['sh.git_repository'].sudo().browse(int(params["_repository_id"]))
            branch = self.env['sh.git_branch'].sudo().browse(int(params['_branch_id']))

            physical_server_id = _repository.so_server.physical_server.id
            physical_server = self.env['sh.physical_server'].sudo().browse(physical_server_id)                
            ssh = self.get_ssh(physical_server)

            _service = params['_service']
            _database = params['_database']

            if(str(_service) != "" and str(_database) != ""):
                command = str('/snap/bin/microk8s.kubectl exec -i ') + str(branch.kuber_exposers.cluster_selector) + str(' -n ') + str(str(_repository.autor.username) + str(_repository.id)) + str(' -- /bin/bash -c  "odoo --stop-after-init -c /var/lib/odoo/odoo.conf --db_host=postgres -w password -r odoo  -d '+ str(_database) +' -i '+ str(_service) +'"')
                _logger.warning(command)
                stdin, stdout, stderr = ssh.exec_command(command)
                for line in iter(stdout.readline, ""):
                    _logger.warning(line)
                for line in iter(stderr.readline, ""):
                    _logger.warning(line)

            command = str('/snap/bin/microk8s.kubectl exec -i ') + str(branch.kuber_exposers.cluster_selector) + str(' -n ') + str(str(_repository.autor.username) + str(_repository.id)) + str(' -- /bin/bash -c  "kill -HUP 1"')
            _logger.warning(command)
            stdin, stdout, stderr = ssh.exec_command(command)
            for line in iter(stdout.readline, ""):
                _logger.warning(line)
            for line in iter(stderr.readline, ""):
                _logger.warning(line)
        except Exception as e:
            response = {"error":True, "message":"Could not restart service for current branch. \n\n " + getattr(e, 'message', repr(e)) }
            return response
        return response
    
    def delete_branch(self, branch_id):
        message = str("Branch was deleted successful.")
        response = {'state':'ok', 'message':message}
        branch = self.sudo().browse(int(branch_id))
        ssh = self.get_ssh(branch.repository.so_server.physical_server)
        services_published = self.env['kuber.exposer'].sudo().search([('git_branch','=',int(branch.id))])
        if services_published:
            for svc in services_published:
                self.env["kuber.deploy"].sudo().delete(ssh, branch.repository, branch.kuber_identifier_name, 'service')
                svc.unlink()

        # queue structure: deletes pod and remove last one
        self.env["kuber.deploy"].sudo().delete(ssh, branch.repository, branch.kuber_identifier_name, 'pod')
        self.env["kuber.deploy"].sudo().scale(ssh, branch.repository, branch.kuber_identifier_name, (int(branch.repository.replicas)-int(1)) )

        _autor = self.env['git.autor'].browse(self.env.user.partner_id.id)
        access_token = _autor.access_token
        git_user = None
        gitClient = None
        try:
            gitClient = Github(access_token)
            git_user = gitClient.get_user()
        except Exception as e:
            message = "Could not connect to Github account \n\n" + getattr(e, 'message', repr(e))
            response['state'] = 'error'
            response['message'] = message
            return response
        try:
            github_repository = git_user.get_repo(name=self.format_name(str(branch.repository.name)))
            github_branch = github_repository.get_git_ref(f"heads/{branch.name}")
            github_branch.delete()
        except Exception as e:
            message = "Could not delete branch in Github \n\n" + getattr(e, 'message', repr(e))
            response['state'] = 'error'
            response['message'] = message
            return response
        branch.sudo().unlink()
        return response

    def execute_command(self,_kuber_deployment, _branch):
        for command in _kuber_deployment.kuber_commands:
            _command = self.env['kuber.commands'].sudo().browse(command.id)
            _command.sudo().execute_command(_command.name, _branch)
            self.assign_command_to_branch(_command.name, _branch)
    
    def assign_command_to_branch(self, command_name, _branch):
        params = {'_command': str(command_name), '_branch_id':_branch.id}
        self.env['kuber.commands'].sudo().save_command(params)
    
    def assign_domain(self, params):    
        return self.env['kuber.domains'].sudo().assign_domain(params)

    def get_domains(self, params):
        return self.env['kuber.domains'].sudo().get_domains(params)

    def format_name(self, _name):
        _name = str(_name).replace(" ","-")
        _name = str(_name).lower()
        return _name