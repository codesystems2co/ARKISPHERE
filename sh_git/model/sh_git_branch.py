#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging, sys
_logger = logging.getLogger(__name__)
from github import Github

class sh_git_branch(models.Model):

    _name = "sh.git_branch"
    _description = "sh.git_branch"

    name = fields.Char( required=True, string="Name",  help="")
    sha = fields.Char( string="Sha",  help="")
    node_id = fields.Char( string="Node",  help="")
    author = fields.Char( string="Author",  help="")
    
    repository = fields.Many2one(comodel_name="sh.git_repository",  inverse_name="branches",  string="Repository",  help="")
    collaborators = fields.Many2many(comodel_name="git.collaborator",  string="Collaborators", domain=[('is_collaborator', '=', True)],  help="")
    commits = fields.One2many(comodel_name="sh.git_commit",  inverse_name="branch",  string="Commits",  help="")        

    def create_git_repository_branch_from(self, params):
        _git_response = {"error":False, "message":"Branch "+str(params["_branch_to"])+" was created successful."}
        _autor = self.env['git.autor'].browse(self.env.user.partner_id.id)
        access_token = _autor.access_token
        _repository = self.env['sh.git_repository'].sudo().browse(int(params["_repository_id"]))

        _logger.warning("GIT REPOSITORY")
        _logger.warning(_repository.name)
        _logger.warning(_repository.full_name)

        _git_repository = None
        _branch_from = None

        try:
            gitClient = Github(access_token)
            git_user = gitClient.get_user()
        except Exception as e:
            _git_response = {"error":True, "message":"Could not login into your account \n\n " + getattr(e, 'message', repr(e))}
            return _git_response

        try:
            _git_repository = git_user.get_repo(name=self.format_name(str(_repository.name)))
        except Exception as e:
            _git_response = {"error":True, "message":"Could not find repository ("+str(_repository.name)+") \n\n " + getattr(e, 'message', repr(e))}
            return _git_response
        
        try:
            _branch_from = _git_repository.get_branch(str(params["_branch_from_label"]))            
        except Exception as e:
            _git_response = {"error":True, "message":"Could not get branch ("+str(params["_branch_from"])+") for repository ("+str(_repository["name"])+") \n\n " + getattr(e, 'message', repr(e))}
            return _git_response
        
        try:
            _branch_new = _git_repository.create_git_ref(ref='refs/heads/' + str(params["_branch_to"]), sha=_branch_from.commit.sha)  
            _branch_new = _git_repository.get_branch(str(params["_branch_to"]))
            _logger.warning("GIT BRANCH")
            _logger.warning("CREATE SH BRANCH")        
            _logger.warning(_branch_new)
            new_branch = self.create_sh_project_branch(_branch_new, _autor, _repository)
            _git_response['_branch'] = new_branch
        except Exception as e:
            _git_response = {"error":True, "message":"Could not create branch from ("+str(params["_branch_from_label"])+") to new reference ("+str(params["_branch_to"])+") \n\n " + getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno)}
            return _git_response
        return _git_response
    
    def create_sh_project_branch(self, _branch, _autor, _repository):
        try:
            _logger.warning("CREATE SH BRANCH")        
            values = {
                        'name': _branch.name,
                        'sha': str(_branch.commit.sha),
                        'repository': _repository.id,
                        'author': _branch.commit.author.login,
                     }
            _logger.warning(values)    
            new_branch = self.env['sh.git_branch'].sudo().create(values)
            branch_repository = self.env['sh.git_repository'].sudo().browse(_repository.id)
            branch_repository.sudo().write({'branches':[(4, new_branch.id)]})
            return new_branch
        except Exception as e:
            _git_response =  getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno)
            raise Warning(_git_response)
    
    def get_git_project_branch_commits(self, repository_id, branch_id, autor_id=None):
        _git_response = {"error":False, "message":"No records found.", "commits":[]}
        _repository = self.env['sh.git_repository'].sudo().browse(int(repository_id))

        if(autor_id):
            _autor = self.env['git.autor'].browse(int(_repository.autor.id))
        else:
            _autor = self.env['git.autor'].browse(self.env.user.partner_id.id)

        
        access_token = _autor.access_token
        _git_branch = None

        try:
            gitClient = Github(access_token)
            git_user = gitClient.get_user()
        except Exception as e:
            _git_response = {"error":True, "message":"Could not login into your account \n\n " + getattr(e, 'message', repr(e))}
            return _git_response
        
        try:
            _git_repository = git_user.get_repo(name=self.format_name(str(_repository.name)))    
            _logger.warning(_git_repository)         
        except Exception as e:
            _git_response = {"error":True, "message":"Could not find repository ("+str(_repository.name)+") \n\n " + getattr(e, 'message', repr(e))}
            return _git_response
        
        try:
            _branch = self.env["sh.git_branch"].sudo().browse(int(branch_id))
            _logger.warning(_branch.name)
            _git_branch = _git_repository.get_branch(str(_branch.name))   
            _logger.warning(_git_branch)         
        except Exception as e:
            _git_response = {"error":True, "message":"Could not get branch ("+str(_git_branch.name)+") for repository ("+str(_repository.name)+") \n\n " + getattr(e, 'message', repr(e))}
            return _git_response
        
        try:
            _git_commit = _git_branch.commit  
            _git_commits = _git_repository.get_commits(str(_git_commit.sha)) 
            commits_list = [] 
            for git_commit in _git_commits:
                commits_list.append({
                                        "author":git_commit.commit.author.name,
                                        "message":git_commit.commit.message,
                                        "sha":git_commit.commit.sha,
                                        "url":str("https://github.com/") + str(_repository.full_name) + str("/commit/") + str(git_commit.commit.sha),
                                    })
            _git_response['commits'] = commits_list
        except Exception as e:
            _git_response = {"error":True, "message":"Could not get branch ("+str(_branch.name)+") for repository ("+str(_repository.name)+") \n\n " + getattr(e, 'message', repr(e))}
            return _git_response

        return _git_response
    
    def get_branch_commits(self, params):
        _git_response = self.get_git_project_branch_commits(params['_repository_id'], params['_branch_id'], params['_autor_id'])
        return _git_response
    
    def unlink(self):
        try:
            if(self.repository):
                _autor = self.env['git.autor'].browse(self.repository.autor.id)
                access_token = _autor.access_token
                try:
                    gitClient = Github(access_token)
                    git_user = gitClient.get_user()
                except Exception as e:
                    git_response = {"error":True, "message":"Could not login into your account \n\n " + getattr(e, 'message', repr(e))}
                    raise Warning(git_response["message"])
                #try:
                #    git_repository = git_user.get_repo(name=self.format_name(str(self.repository.name)))
                #    git_repository.get_git_ref(f"heads/{self.format_name(str(self.name))}").delete()
                #except Exception as e:
                #    git_response = {"error":True, "message":"Could not delete branch "+str(self.name)+" in your account \n\n " + getattr(e, 'message', repr(e))}
                #    raise Warning(git_response["message"])
        except:
            pass

        return super(sh_git_branch, self).unlink()

    def format_name(self, _name):
        _name = str(_name).replace(" ","-")
        _name = str(_name).lower()
        return _name        