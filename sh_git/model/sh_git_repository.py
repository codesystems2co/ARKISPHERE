#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
from odoo import http
from github import Github
import sys
import logging
import time
import os
_logger = logging.getLogger(__name__)


class sh_git_repository(models.Model):

    _name = "sh.git_repository"
    _description = "sh.git_repository"

    identifier = fields.Char( string="Identifier",  help="")
    name = fields.Char( required=True, string="Name",  help="")
    full_name = fields.Char( string="Full name",  help="") 
    
    branches = fields.Many2many(comodel_name="sh.git_branch",  inverse_name="repository",  string="Branches",  help="", ondelete="cascade")

    autor = fields.Many2one(comodel_name="git.autor",  string="Autor", domain=[('is_autor', '=', True)],  help="")    

    def repository_link(self):
        self.url = str("https://github.com/") + str(self.full_name)
        return self.url    
    
    def open_repository(self):
        return {
                    'type': 'ir.actions.act_url',
                    'url': self.repository_link(),
                    'target': 'new', # open in a new tab
                }

    url = fields.Char( string="Url",  help="", compute=repository_link)  

    def create_git_repository(self, params):
        _autor = self.env['git.autor'].browse(self.env.user.partner_id.id)
        access_token = _autor.access_token
        gitClient = None
        git_response = {"error":False, "message":"Repository was created successful." + str(" -> ") + str(_autor.platform)}

        _logger.warning("Autor >>")
        _logger.warning(str(_autor.id) + str(" -> ") + str(_autor.platform))
        _logger.warning(_autor.platform)

        if(_autor.platform == "github"):

            try:
                gitClient = Github(access_token)
                git_user = gitClient.get_user()
            except Exception as e:
                git_response = {"error":True, "message":"Could not login into your account \n\n " + getattr(e, 'message', repr(e))}
            
            _visibility = False
            if(str(params['_visibility'])==str("true")):
                _visibility = True
            
            # repository from github
            try:
                git_repository = None
                if params['restore_way'] == 'standar':
                    try:
                        git_repository = git_user.create_repo(name=str(params['_name']), private=_visibility, license_template='bsd-2-clause', auto_init=True) 
                        _logger.warning("Github Repository >>")
                        _logger.warning(git_repository)               
                    except Exception as e:  
                        _logger.warning("Github Repository >>")
                        _logger.warning(git_repository)
                        return {'error':True, 'message':_("It seems your access token was expired or changed. Also make sure repository name does not exist on Github.")}
                else:
                    try:
                        git_repository = git_user.get_repo(name=str(params['_name'])) 
                        _logger.warning("Github Existing Repository >>")
                        _logger.warning(git_repository)               
                    except Exception as e:  
                        _logger.warning("Github Existing Repository Error >>")
                        _logger.warning(git_repository)
                        _logger.warning(getattr(e, 'message', repr(e)))
                        return {'error':True, 'message':_("It seems your access token was expired or changed. Also make sure repository name does not exist on Github.")}
                    
                _repository = self.create_sh_project(git_repository, _autor, str(params['_server_id']))                
                git_response['_repository'] = _repository
                # branch from github
                _branch = None
                if params['restore_way'] == 'standar':
                    _branch = self.create_git_project_branch(git_repository, 'main')
                else:
                    try:                        
                        _logger.warning('search _branch name >>')
                        _logger.warning(str(params['main_branch']['name']))
                        _branch = git_repository.get_branch(str(params['main_branch']['name']))
                        _logger.warning('_branch >>')
                        _logger.warning(_branch)
                        if _branch.name != 'main':
                            try:
                                was_renamed = git_repository.rename_branch(params['main_branch']['name'],'main')
                                if was_renamed:
                                    _branch = git_repository.get_branch(str(params['main_branch']['name']))
                                else:
                                   return {'error':True, 'message':_("Cant rename branch: ") + str(params['main_branch']['name'])}  
                            except Exception as e:
                                _logger.warning('Exception: cant rename branch >>') 
                                _logger.warning(getattr(e, 'message', repr(e)))
                                return {'error':True, 'message':_("Cant rename branch: ") + str(params['main_branch']['name'])}  
                    except Exception as e:
                        _logger.warning('Exception: cant get branch >>') 
                        _logger.warning(getattr(e, 'message', repr(e)))
                        return {'error':True, 'message':_("Cant get existing branch.")}                                      

                #for odoo backend  
                git_response['_branch'] = self.create_sh_project_branch( _branch, _autor, _repository, params)
            except Exception as e:                
                git_response = {"error":True, "message":"Could not create repository"}
                _logger.warning(git_response)
                _logger.warning(getattr(e, 'message', repr(e)))
                _logger.warning(format(sys.exc_info()[-1].tb_lineno))            
            return git_response
        return git_response
    
    def create_sh_project(self, git_repository, _autor, _server_id):
        
        values = {
                    'identifier': str(git_repository.id),
                    'name': str(git_repository.name),
                    'full_name': str(git_repository.full_name),
                    'autor': int(_autor.id),
                    'so_server': int(_server_id),
                 }
        
        repository = self.env['sh.git_repository'].sudo().create(values)

        return repository
    
    def create_sh_project_branch(self, _branch, _autor, _repository, params={}):   
        _logger.warning('create_sh_project values >>')  
        _logger.warning(_repository)
        _logger.warning(_branch)
        values = {
                    'name': _branch.name,
                    'sha': str(_branch.commit.sha),
                    'repository': _repository.id,
                    'author': _branch.commit.author.login,
                 }
        _logger.warning(values)
        new_branch = self.env['sh.git_branch'].sudo().create(values)
        _logger.warning('create_sh_project created >>')  
        branch_repository = self.env['sh.git_repository'].browse(_repository.id)
        branch_repository.sudo().update({'branches':new_branch})
        return new_branch
    
    def create_git_project_branch(self, git_repository, _name):
        _branch = None
        _branch_commits = None
        if(_name == "main"):
            time.sleep(1)
            _branch = git_repository.get_branch(_name)
            _logger.warning(_branch)
            _branch_commits = _branch.commit
            _logger.warning(_branch_commits)        
        return _branch
    
    def get_repositories(self, **kw):
        so_server_id = None
        if('server' in http.request.params):
            so_server_id = http.request.params['server']
        if(so_server_id):
            if(int(so_server_id)>0):                
                repositories = self.search([
                                                ('so_server','=',int(so_server_id)),
                                                ('autor','=',self.env.user.partner_id.id)
                                            ])
                return repositories
            else:
                return self.search([('autor','=',self.env.user.partner_id.id)])
        else:
            return self.search([('autor','=',self.env.user.partner_id.id)])
    
    def _get_repositories(self, so_server_id):             
        repositories = self.search([
                                        ('so_server','=',int(so_server_id)),
                                        ('autor','=',self.env.user.partner_id.id)
                                    ])
        return repositories
    
    def get_foreing_repositories(self, **kw):
        branches = self.env['sh.git_branch'].search([('collaborators','=',self.env.user.partner_id.id)])
        repositories_ids = []
        for branch in branches:
            repositories_ids.append(branch.repository.id)

        repositories = self.env['sh.git_repository'].search([('id','in',repositories_ids)])
        _logger.warning(repositories)
        return repositories
    
    def get_repository_branch(self, repository_id, branch_name="main"):
        _branch = None
        request.cr.execute("SELECT id FROM sh_git_branch WHERE (repository = %s) AND (name = %s)", (repository_id, branch_name))
        _sh_git_branch = request.cr.dictfetchone()
        if('id' in _sh_git_branch):
            _branch = self.sudo().browse(_sh_git_branch['id'])
        return _branch
    
    def get_repository_branches(self, repository_id, _filter="all_development"):
        _sh_git_branches = None
        if(_filter=="all_development"):
            request.cr.execute("SELECT id, name FROM sh_git_branch WHERE (repository = %s) AND (name != %s)", (repository_id, 'main'))
            _sh_git_branches = request.cr.dictfetchall()  
        if(_filter=="all"):
            request.cr.execute("SELECT id, name FROM sh_git_branch WHERE (repository = " + str(repository_id) + ")")
            _sh_git_branches = request.cr.dictfetchall()     
            _logger.warning(_sh_git_branches)      
        return _sh_git_branches
        
    def get_current_project(self):
        project_id = None # means repository
        if('project' in http.request.params):
            project_id = http.request.params['project']
        if(project_id):
            return project_id
    
    def get_current_project_name(self):
        project_id = None # means repository
        if('project' in http.request.params):
            project_id = http.request.params['project']
        if(project_id):
            project_id = request.env['sh.git_repository'].sudo().browse(int(project_id))
            return project_id.name

    def autor_and_collaborators_control(self, params):
        if(int(self.env.user.partner_id.id) == int(params['_autor_id'])):
            return {'error':False, '_type':'autor'}
        else:
            return {'error':False, '_type':'collaborator'}
    
    def unlink(self):
        for record in self:

            _autor = self.env['git.autor'].browse(record.autor.id)
            access_token = _autor.access_token            
            try:
                gitClient = Github(access_token)
                git_user = gitClient.get_user()
            except Exception as e:
                git_response = {"error":True, "message":"Could not login into your account \n\n " + getattr(e, 'message', repr(e))}
                raise Warning(git_response["message"])            
            
            _branches = record.get_repository_branches(record.id, _filter="all")            
            for _branch in _branches:
                try:                
                    _branch.unlink()
                except Exception as e:
                    git_response = {"error":True, "message":"Could not delete branch in odoo \n\n " + getattr(e, 'message', repr(e))}
                    _logger.warning(git_response)

            # delete in github
            #try:
            #    git_user.get_repo(name=self.format_name(str(record.name))).delete()
            #except Exception as e:
            #    git_response = {"error":True, "message":"Could not delete repository "+str(record.name)+" in your account \n\n " + getattr(e, 'message', repr(e))}
            #    raise Warning(git_response["message"])

        return super(sh_git_repository, self).unlink()    
    
    def delete_repository(self, _autor, _repository_name):

        _autor = self.env['git.autor'].browse(_autor)
        access_token = _autor.access_token     
        # auth login
        try:
            gitClient = Github(access_token)
            git_user = gitClient.get_user()
        except Exception as e:
            git_response = {"error":True, "message":"Could not login into your account \n\n " + getattr(e, 'message', repr(e))}
            raise Warning(git_response["message"])       
        
        # delete in github
        try:
            git_user.get_repo(name=self.format_name(str(_repository_name))).delete()
        except Exception as e:
            git_response = {"error":True, "message":"Could not delete repository "+str(_repository_name)+" in your account \n\n " + getattr(e, 'message', repr(e))}
            raise Warning(git_response["message"])
    
    def get_github_project(self):
        message = str()
        response = {'error':False, 'message':message, 'data':[]}
        _autor = self.env['git.autor'].browse(self.env.user.partner_id.id)
        access_token = _autor.access_token   
        git_user = None  
        git_repositories = None
        # auth login
        try:
            gitClient = Github(access_token)
            git_user = gitClient.get_user()
        except Exception as e:
            message = _("Could not login into your account \n\n ") + str(getattr(e, 'message', repr(e)))
            response =  {'error':True, 'message':message}
            return response
        # get all repositories
        try:
            git_repositories = git_user.get_repos()
        except Exception as e:
            message = _("Could not get repositories \n\n ") + str(getattr(e, 'message', repr(e)))
            response = {"error":True, "message":message}   
        
        try:
            if git_repositories:
                
                for repository in git_repositories:
                    item = [{'repository':{'name':repository.name}}, {'branches':[]}]
                           
                    # get all branches
                    branches = None
                    try:
                        branches = repository.get_branches()
                    except Exception as e:
                        message = _("Could not get branches \n\n ") + str(getattr(e, 'message', repr(e)))
                        response = {"error":True, "message":message} 

                    if branches:
                        for branch in branches:
                           sub_item = {'name':branch.name,'sha':str(branch.commit.sha)}
                           (item[1]['branches']).append(sub_item) 
                    (response['data']).append(item)
                            
        except Exception as e:
            message = _("Could not get repositories \n\n ") + str(getattr(e, 'message', repr(e)))
            response = {"error":True, "message":message + format(sys.exc_info()[-1].tb_lineno)} 

        return response

    def format_name(self, _name):
        _name = str(_name).replace(" ","-")
        _name = str(_name).lower()
        return _name