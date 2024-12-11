# -*- coding: utf-8 -*-
from odoo import http
from odoo import _
from http import cookies
import requests
from odoo.http import request
import sys, os, base64
from github import Github
from github.Auth import Login
import logging
_logger = logging.getLogger(__name__)

class SH_Client(http.Controller):

    @http.route('/git/auth_connect', methods=['POST'], type='json', auth="public", website=True)
    def auth_connect(self, **kw):
        
        platform = kw.get('platform')
        username = kw.get('username')
        password = kw.get('password')
        access_token = kw.get('access_token')

        query = "UPDATE res_partner SET name='Public User', country_id=null, city=null, zip=null, email=null, is_autor='False', username=null, is_collaborator='False', platform=null, identifier=null, _gpassword=null, html_url=null, access_token=null WHERE id = "+str(request.env.user.partner_id.id)
        request.cr.execute(query)

        if('github' in platform):
            _logger.info('::Connecting with github >>')
            # 1th step: test token before sign up
            # when login does not has sign up
            if access_token:
                _logger.info('::Sign up with github >>')
                # sign up
                gitClient = Github(access_token)
                try:
                    gitClient.get_user(username).id
                    _login = Login(username,password)
                    gitClient = Github(auth=_login)
                    try:
                        identifier = gitClient.get_user(username).id
                        html_url = gitClient.get_user(username).html_url
                        # well.. seems credentials are correct. lets start...
                        fullname = gitClient.get_user(username).name if(gitClient.get_user(username).name) else username           
                        email = username if not gitClient.get_user(username).email else gitClient.get_user(username).email
                        geo = requests.get('http://ipinfo.io/json').json()

                        try:
                            country = request.env['res.country'].sudo().search_read([('code','=',str(geo['country']))], ['id'])[0]['id']
                        except:
                            country = None

                        response = {
                                        'status':'success',
                                        'id':identifier,
                                        'username':username,
                                        'password':password,
                                        'name':fullname,
                                        'email':email, 
                                        'full_name':fullname,
                                        'html_url':html_url,
                                        'access_token':access_token
                                    } 
                        
                        query = "UPDATE res_partner SET name='"+str(fullname)+"', country_id="+str(country)+", city='"+str(geo['city'])+"', zip='"+str(geo['postal'])+"', email='"+str(email)+"', is_autor='True', username='"+str(username)+"', is_collaborator='True', platform='github', identifier='"+str(identifier)+"', _gpassword='"+str(password)+"', html_url='"+str(html_url)+"', access_token='"+str(access_token)+"' WHERE id = "+str(request.env.user.partner_id.id)
                        request.cr.execute(query)
                        return response

                    except Exception as e:
                        _logger.info(':: Username Invalid')
                        return {'status':"error", "message":_('Username does not match with your github account.')}
                except Exception as e:
                    _logger.info(':: Token Invalid')
                    return {'status':"error", "message":_('Token does not appear to be valid o was expired. \n Kindly generate one without expiration time')}
            else:
                # just sign in
                _logger.info('::Sign in with github >>')
                _login = Login(username,password)
                gitClient = Github(auth=_login)
                try:
                    identifier = gitClient.get_user(username).id
                    if not identifier:
                        return {'status':"error", "message":_('Username does not match with your github account.')}
                    try:
                        request.env['res.partner'].sudo().search_read([('username','=',str(username))], ['id','access_token'], limit=1)[0]['id']
                    except:
                        return {'status':"error",'message':_('Username ') + str(username) + _(' does not exist. \n Kindly, try to sign up.')}
                    
                    author = self.get_autor(username)
                    if author:
                        if '_gpassword' in author:
                            if password == author['_gpassword']:
                                #self.set_cookie("gitClient", gitClient)
                                return {'status':"success",'id':identifier,'email':author['email'],'username':author['username']}
                            else:
                                return {'status':"error", "message":_('Password does not match with your github account.')}
                        else:
                            return {'status':"error", "message":_('Password does not match with your github account.')}
                    else:
                        return {'status':"error", "message":_('Password does not match with your github account.')}
                    
                    return {'status':"success",'id':identifier}
                
                except Exception as e:
                    error = getattr(e, 'message', repr(e))
                    _logger.warning(error)
                    _logger.info(':: Username Invalid')
                    return {'status':"error", "message":_('Username does not match with your github account.')}
            
        return response

    def set_cookie(self, key, value):
        cookies_manager = cookies.SimpleCookie()
        cookies_manager[key] = value
    
    def get_cookie(self, key):
        cookievalue = cookies.SimpleCookie(os.environ["HTTP_COOKIE"])
        return cookievalue[key].value
    
    def get_autor(self, username):
        query = "select access_token, _gpassword, email, username from res_partner where username = '"+str(username)+"'"
        request.cr.execute(query)
        autor = request.cr.dictfetchone()
        return autor