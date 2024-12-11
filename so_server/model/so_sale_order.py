#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, MissingError
from odoo import http
from odoo.http import request
from uuid import uuid4
from dateutil.relativedelta import *
from datetime import datetime
from datetime import date
import sys
import os
import paramiko
import time
import re

import logging
_logger = logging.getLogger(__name__)

class sh_sale_order(models.Model):
    _inherit = "sale.order"

    cloud_provider = fields.Many2one(string='Cloud Provider', comodel_name='sh.cloud.provider')

    def action_confirm(self):
        response =  super(sh_sale_order, self).action_confirm()
        _order_lines = request.env["sale.order.line"].search([
                                                                ('order_id','=',self.id) 
                                                             ])        
        if(_order_lines):
            for _order_line in _order_lines:
                _order_line = request.env["sale.order.line"].browse(_order_line.id)
                values = None
                try:
                    name = _order_line.name
                    attributes_values = str(re.findall(r'\(.*?\)', name)[0]).replace('(','').replace(')','').split(',')
                    values = []
                    for value in attributes_values:
                        values.append(str(value).replace('GB','').replace('Gi','').replace('Cores','').strip())

                    # Attributes change in order how display in view
                    values = {'workers':values[0],'period':values[1],'cores':values[2],'ram':values[3],'disk':values[4],'customisation':values[5]}
                except:
                    pass
                
                if values:

                    _params = {
                                    'ram_size':float(values['ram']),
                                    'ram_size_gb':str(values['ram'])+str('GB'),

                                    'disk_size':float(values['disk']),                               
                                    'disk_size_gb':str(values['disk'])+str('GB'),

                                    'processor_core':str(values['cores']),                                                                        
                                    'processor_core_gb':str(values['cores'])+str('GB'),

                                    'order_line':_order_line,
                                    'order_name': self.name,
                                    'partner_id': self.partner_id.id
                            }
                    provider = None
                    if self.cloud_provider:
                        provider = self.cloud_provider
                    else:
                        provider = self.env["sh.cloud.provider"].sudo().search_read([('_default','=',True)],['id'],limit=1)
                        if provider:
                            provider = self.env["sh.cloud.provider"].sudo().browse(int(provider[0]['id']))

                    # BG ---- PRECREATED LOCAHOST SEARCH >>>>
                        ## get physical server with specification by client
                        #filter  = [('is_busy','=',False)]
                        #filter.append(('ram_size','=',str(values['ram']+str('GB'))))
                        #filter.append(('disk_size','=',str(values['disk']+str('GB'))))
                        #filter.append(('processor_core','=',str(values['cores'])))                    
                        #physical_server = self.env['sh.physical_server'].search(filter, limit=1)
                    # EOF
                        
                    _logger.warning('creating hetzner >>')
                    unique = str(str(uuid4())[7:-18]).replace('-','').upper()
                    name = str(self.name +str('-')+ str(values['cores']) +str('-')+ str(values['ram'])) +str('-')+ str(values['disk']) + str(_order_line.id)
                    _logger.warning('_order_line >>')
                    _logger.warning(_order_line)
                    
                    hetzner_server = self.env['sh.physical_server'].create_hetzner_server(name, _params, provider)
                    #hetzner_server = {'ip':'654645','password':'5555'}

                    if 'error' in hetzner_server:
                        raise ValidationError(_(hetzner_server['error']))
                    
                    _logger.warning('hetzner server>>')
                    _logger.warning(hetzner_server)

                    new_params_physical_server = {}
                    new_params_physical_server['name'] = name
                    new_params_physical_server['label'] = 'Ubuntu Server'
                    new_params_physical_server['ip'] = hetzner_server['ip']
                    new_params_physical_server['ssh_host'] = hetzner_server['ip']
                    new_params_physical_server['port'] = str('22')
                    new_params_physical_server['user'] = str('root')
                    new_params_physical_server['password'] = str(hetzner_server['password'])
                    new_params_physical_server['is_busy'] = False

                    # hardware
                    new_params_physical_server['ram_size'] = _params['ram_size_gb'] 
                    new_params_physical_server['disk_size'] = _params['disk_size_gb'] 
                    new_params_physical_server['processor_core'] = _params['processor_core'] 
                    new_params_physical_server['provider'] = int(provider.id)

                    physical_server = self.env['sh.physical_server'].sudo().create(new_params_physical_server)

                    _logger.info('Getting physical server with...')
                    _logger.info(filter)

                    _logger.info('Server Enviroment')
                    _logger.info(physical_server)

                    if not physical_server:
                        raise MissingError(_('It seems no server available to create enviroment'),)
                    
                    if(physical_server):
                        so_server = self.create_so_server(physical_server,self.partner_id.id,_params)

                        if(so_server):
                            _order_line.sudo().update({'so_server':so_server})

                            if not self.cloud_provider:
                            so_server.sale_order.sudo().update({'cloud_provider':int(provider.id)})

        return response

    def create_so_server(self,physical_server, _partner_id, _params, is_custom=False):
        try:
            if(physical_server):
                _name = str(physical_server.label)                
                so_server = request.env['so.server'].sudo().create({
                                                                        'name':str(_name) + str(" - ") + str(_partner_id) + str(" - ") + str(_params["order_name"]),
                                                                        'brand':str('Linux'),
                                                                        'ram_size':float(_params['ram_size']),

                                                                        'disk_size':float(_params['disk_size']),
                                                                        'disk_size_gb':str(_params['disk_size_gb']),

                                                                        'ram_size_gb':str(_params['ram_size_gb']),
                                                                        'disk_size_gb':str(_params['disk_size_gb']),
                                                                        
                                                                        'processor_core':str(_params['processor_core']),
                                                                        'processor_core_gb':str(_params['processor_core_gb']),
                                                                        
                                                                        'order_line':int(_params['order_line'].id),
                                                                        'physical_server': int(physical_server.id),
                                                                        'owner': [(4,_partner_id)],
                                                                    })
                physical_server.update({'is_busy':True, 'so_server':int(so_server.id)})
                return so_server
        except Exception as e:
            _logger.ValidationError(format(sys.exc_info()[-1].tb_lineno))
            raise ValidationError( str("\n Name: ") + str(physical_server.so_server.name) + str("\n Brand: ") + str(physical_server.so_server.brand) + str("\n Ram: ") + str(physical_server.so_server.ram_size) + str("\n Disk: ") + str(physical_server.so_server.disk_size) + str("\n MESSAGE: ") + getattr(e, 'message', repr(e)))
            
    
    def create_physical_server(self,_order_line, _params):
        try:
            if(_order_line):
                _order_line = request.env["sale.order.line"].browse(_order_line.id)
                _description = str(_order_line.name)
                if('(Outside):' in _description):
                    _description_parts = str(_description).split("(Outside):")
                    _ssh_variant = str(_description_parts[1]).strip()
                    ssh_parts = str(_ssh_variant).split(",")
                    has_error = False
                    try:
                        user = str(ssh_parts[0]).strip()
                    except:
                        message = message + "User not provided. \n"
                        has_error = True
                    try:
                        password = str(ssh_parts[1]).strip()
                    except:
                        message = message + "Password not provided. \n"
                        has_error = True
                    try:
                        host = str(ssh_parts[2]).strip()
                    except:
                        message = message + "Host not provided. \n"
                        has_error = True
                    try:
                        port = str(ssh_parts[3]).strip()
                    except:
                        message = message + "Port not provided. \n"
                        has_error = True

                    if(has_error==False):
                        _user_id = self.env['res.users'].search([('partner_id','=',_params['partner_id'])], limit=1)
                        data = {
                                    'name':str("VPS") + str(" - ") + str(_params['order_name']),
                                    'ram_size':str(1),
                                    'disk_size':str(1),     
                                    'user': user,
                                    'password': password,
                                    'ip': host,
                                    'ssh_host': host,
                                    'port': port,
                                    'owner':[(4, _user_id.id)]
                                }
                        
                        physical_server = request.env['sh.physical_server'].sudo().create(data)
                        if(physical_server):
                            so_server = self.sudo().create_so_server(physical_server, _params['partner_id'], _params, True)
                            if(so_server):
                                _order_line.sudo().update({'so_server':so_server.id})
                                physical_server.sudo().update({'so_server':so_server.id})  
                    else:
                        pass
        except Exception as e:
            raise ValidationError( str("\n MESSAGE: ") + getattr(e, 'message', repr(e)))

    def get_partner(self, _id):
        self._cr.execute('select username from res_partner where id = ' + str(_id))
        _partner = self._cr.dictfetchone()
        return _partner

    def get_ssh(self, physical_server):
        try: 
            os.system('ssh-keygen -f "/root/.ssh/known_hosts" -R "'+str(physical_server.ssh_host)+'"')
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(str(physical_server.ssh_host), username=str(physical_server.user), password=str(physical_server.password), port=str(physical_server.port), look_for_keys=False, allow_agent=False)
            return ssh
        except Exception as e:
            raise ValidationError(str("\n Password: ") + str(physical_server.password) + str("\n ID: ") + str(physical_server.id) + str("\n IP: ") + str(physical_server.ssh_host) + str("\n PORT: ") + str(physical_server.port) + str("\n USER: ") + str(physical_server.user) + str("\n MESSAGE: ") + getattr(e, 'message', repr(e)))