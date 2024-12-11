#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
import sys
import logging
import paramiko
import time
_logger = logging.getLogger(__name__)

class kuber_commands(models.Model):

    _name = "kuber.commands"
    _description = "Kuber Commands"

    name = fields.Char( required=True, string="Command",  help="")
    is_private = fields.Boolean( string="Is Private",  help="", default=False)
    branch = fields.Many2one(comodel_name="sh.git_branch",  inverse_name="kuber_commands",  string="Branch",  help="")
    executed_on_init = fields.Boolean(default=False)
    kuber_deployments = fields.Many2one(comodel_name="kuber.deploy",  inverse_name="kuber_commands",  string="Deployments",  help="")

    def save_command(self, params):
        commands = []
        response = {'error':False, 'message':None, 'commands':commands}  
        try:
            branch = self.env['sh.git_branch'].sudo().browse(int(params['_branch_id']))
            branch
            kuber_command = self.sudo().create({'name':str(params['_command']),'branch':int(params['_branch_id'])})           
            branch.sudo().update({'kuber_commands':[(4,kuber_command.id)]})
            response['message'] = str('Command added to branch (') + str(branch.name) + str(")")
            branch = self.env['sh.git_branch'].sudo().browse(int(params['_branch_id']))
            for command in branch.kuber_commands:
                commands.append([command.id, command.name])
            response['commands'] = commands
        except Exception as e:
            response = {"error":True, "message":"Could not create command for branch selected. \n\n " + getattr(e, 'message', repr(e)) } # +" ON LINE "+format(sys.exc_info()[-1].tb_lineno)
            return response
        return response        
    
    def delete_command(self, params):
        commands = []
        response = {'error':False, 'message':None, 'commands':commands}  
        try: 
            branch = self.env['sh.git_branch'].sudo().browse(int(params['_branch_id']))
            branch.sudo().update({'kuber_commands':[(2,str(params['_command_id']))]})

            request.cr.execute(str("DELETE from kuber_commands_sh_git_branch_rel ") + str("WHERE kuber_commands_id=") + str(params['_command_id']) + str(" AND ") + str("sh_git_branch_id=") + str(params['_branch_id']))
            
            response_commands = self.get_commands(params)
            _logger.warning(response_commands)
            response['commands'] = response_commands['commands']
        except Exception as e:
            response = {"error":True, "message":"Could not delete command for branch selected. \n\n " + getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno) }
            return response
        return response
    
    def get_commands(self, params):
        commands = []
        response = {'error':False, 'message':None, 'commands':commands}  
        try:       
            _logger.warning(str("SELECT * from kuber_commands_sh_git_branch_rel ") + str("WHERE")+ str(" sh_git_branch_id=") + str(params['_branch_id']))     
            request.cr.execute(str("SELECT * from kuber_commands_sh_git_branch_rel ") + str("WHERE")+ str(" sh_git_branch_id=") + str(params['_branch_id']))
            _commands = request.cr.dictfetchall()
            if(len(_commands)>0):
                for command in _commands:
                    _logger.warning(command)
                    if('kuber_commands_id' in command):
                        _command = self.env['kuber.commands'].sudo().browse(int(command['kuber_commands_id']))
                        commands.append([_command.id, _command.name])
                response['commands'] = commands
        except Exception as e:
            response = {"error":True, "message":"Could not get commands for branch selected. \n\n " + getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno) } # +" ON LINE "+format(sys.exc_info()[-1].tb_lineno)
            return response
        return response
    
    def web_execute_command(self, params):
        response = {'error':False, 'message':"Executed successful."}  
        try:  
            _branch = self.env['sh.git_branch'].sudo().browse(int(params['_branch_id']))
            #_command_id = self.env['kuber.commands'].sudo().browse(int(params['_command']))
            self.execute_command(str(params['_command']), _branch)
        except Exception as e:
            response = {"error":True, "message":"Could not execute commands for branch selected. \n\n " + getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno) } # +" ON LINE "+format(sys.exc_info()[-1].tb_lineno)
        return response
    
    def execute_command_on_deploy(self, _kuber_deployment, _branch, executed_on_init=False): 
        _logger.warning('execute_command_on_deploy >>>>')
        try:       
            so_server = self.env['so.server'].browse(int(_branch.repository.so_server.id))
            _physical_server_id = int(so_server.physical_server.id)
            physical_server = self.env['sh.physical_server'].browse(_physical_server_id)   
            if(physical_server):
                ssh = self.get_ssh(physical_server)

                filter = [['kuber_deployments','=',int(_kuber_deployment.id)]]
                _kuber_commands = self.env['kuber.commands'].search_read(filter)
                _logger.warning('commands >>')
                _logger.warning(_kuber_commands)
                if _kuber_commands:
                    is_ready = False
                    while is_ready==False:
                        command = "/snap/bin/microk8s.kubectl get pod " + str(_branch.kuber_exposers.cluster_selector) + "  -o jsonpath='{.status.phase}' -n " + str(_branch.repository.autor.username) + str(_branch.repository.id)
                        _logger.warning('exec_command >>')
                        _logger.warning(command)
                        stdin, stdout, stderr = ssh.exec_command(command)
                        for line in iter(stdout.readline, ""):
                            _logger.warning('exec_command line >>')
                            _logger.warning(line)
                            if line == 'Running':
                                is_ready = True                    
                                for _kuber_command in _kuber_commands:
                                    try:
                                        _kuber_command = self.env['kuber.commands'].browse(int(_kuber_command['id']))
                                        
                                        command = "/snap/bin/microk8s.kubectl exec -i " + str(_branch.kuber_exposers.cluster_selector) + " -n " + str(_branch.repository.autor.username) + str(_branch.repository.id) + " -- /bin/bash -c '" + str(_kuber_command.name) + str("'")
                                        _logger.warning('ready command line >>')
                                        _logger.warning(command)
                                        
                                        stdin, stdout, stderr = ssh.exec_command(command)
                                        for line in iter(stdout.readline, ""):
                                            _logger.warning(line)
                                    
                                        for line in iter(stderr.readline, ""):
                                            _logger.warning(line)
                                        

                                    except Exception as e:
                                        _logger.warning("execute_command_on_deploy")
                                        _logger.warning(getattr(e, 'message', repr(e)))
        except Exception as e:
            _logger.warning("execute_command_on_deploy")
            _logger.warning(getattr(e, 'message', repr(e)))
    
    def execute_command(self, _command, _branch):
        _logger.warning("_physical_server_id")
        _logger.warning(_branch.repository.so_server.physical_server)
        _physical_server_id = _branch.repository.so_server.physical_server.id
        _logger.warning("_physical_server_id")
        _logger.warning(_physical_server_id)
        physical_server = self.env['sh.physical_server'].browse(_physical_server_id)
        if(physical_server):
            ssh = self.get_ssh(physical_server)    
            command = "/snap/bin/microk8s.kubectl exec -i " + str(_branch.kuber_exposers.cluster_selector) + " -n " + str(_branch.repository.autor.username) + str(_branch.repository.id) + " -- /bin/bash -c '" + str(_command) + str("'")
            _logger.warning(command)
            stdin, stdout, stderr = ssh.exec_command(command)
            for line in iter(stdout.readline, ""):
                _logger.warning(line)
            for line in iter(stderr.readline, ""):
                _logger.warning(line)
    
    def get_ssh(self, physical_server):
        try: 
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(str(physical_server.ssh_host), username=str(physical_server.user), password=str(physical_server.password), port=str(physical_server.port), look_for_keys=False, allow_agent=False, timeout=10)
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            return ssh
        except Exception as e:
            raise Warning(str("\n ID: ") + str(physical_server.id) + str("\n IP: ") + str(physical_server.ssh_host) + str("\n PORT: ") + str(physical_server.port) + str("\n USER: ") + str(physical_server.user) + str("\n MESSAGE: ") + getattr(e, 'message', repr(e)))
        

    
    def exec_commands(self):
        _logger.info('starting cron exec_commands...')
        so_servers = self.env['so.server'].sudo().search_read([],['id', 'git_repositories'])
        if so_servers:
            for so_server in so_servers:
                if so_server['git_repositories']:
                    if len(so_server['git_repositories']) > 0:
                        repository_id  = self.env['sh.git_repository'].sudo().browse(int(so_server['git_repositories'][0]))
                        so_server  = self.env['so.server'].sudo().browse(int(so_server['id']))  

                        _logger.info('virtual server '+str(so_server.name)+' ready for commands...')
                        try:
                            ssh = self.get_ssh(so_server.physical_server)            
                            if repository_id.branches:
                                for branch in repository_id.branches:
                                        _logger.info('branch '+str(branch.name)+' ready for commands...')
                                        if repository_id.branches.kuber_commands:
                                            for command in repository_id.branches.kuber_commands:
                                                try:
                                                    command = "/snap/bin/microk8s.kubectl exec -i " + str(branch.kuber_exposers.cluster_selector) + " -n " + str(branch.repository.autor.username) + str(branch.repository.id) + " -- /bin/bash -c '" + str(command.name) + str("'")
                                                    stdin, stdout, stderr = ssh.exec_command(command)
                                                    _logger.info('branch command executed...')
                                                    for line in iter(stdout.readline, ""):
                                                        _logger.info(line)
                                                    for line in iter(stderr.readline, ""):
                                                        _logger.info(line)
                                                except:
                                                    _logger.info('Could no execute branch command')
                                        else:
                                            
                                            _commands = self.env["kuber.commands"].sudo().search_read([
                                                                                                        ('kuber_deployments','=',int(repository_id.kuber_deploy.id)),
                                                                                                        ('is_private','=',True)
                                                                                                      ]
                                                                                                      ,
                                                                                                      ['id']
                                                                                                     )
                                            if _commands:
                                                for _command in _commands:
                                                    _command  = self.env["kuber.commands"].sudo().browse(int(_command['id']))  
                                                    try:
                                                        command = "/snap/bin/microk8s.kubectl exec -i " + str(branch.kuber_exposers.cluster_selector) + " -n " + str(branch.repository.autor.username) + str(branch.repository.id) + " -- /bin/bash -c '" + str(_command.name) + str("'")
                                                        stdin, stdout, stderr = ssh.exec_command(command)
                                                        _logger.info('private command executed...')
                                                        for line in iter(stdout.readline, ""):
                                                            _logger.info(line)
                                                        for line in iter(stderr.readline, ""):
                                                            _logger.info(line)
                                                    except Exception as e:
                                                        _logger.info('Could no execute repository command')
                                                        _logger.warning(getattr(e, 'message', repr(e)))

                                                    
                            ssh.close()
                                    
                        except:
                            _logger.info('Could not connect to server')