# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from hcloud import Client
from hcloud.images import Image
from hcloud.server_types import ServerType
from hcloud.locations import Location
from hcloud.servers.client import BoundServer
from hcloud._exceptions import APIException
import time
import logging
_logger = logging.getLogger(__name__)

class hetzner_server(models.Model):
    _inherit = "sh.physical_server"

    def create_hetzner_server(self, name, params, provider=None):
        try:
            location = None
            if not provider:
                provider = self.env["sh.cloud.provider"].sudo().search_read([('_default','=',True)],['id'],limit=1)
                if provider:
                    provider = self.env["sh.cloud.provider"].sudo().browse(int(provider[0]['id']))
                if not provider:
                    return {'error':True, 'message':_('A default cloud provider must be selected.')}

            response = {'ip':None, 'password':None}
            _type = None
            _logger.info('Creating Hetzner server with specifications:')
            _logger.info(f"Type: {params.get('type', 'N/A')}")
            _logger.info(f"Cores: {params.get('processor_core', 'N/A')}")
            _logger.info(f"RAM: {params.get('ram_size', 'N/A')} GB")
            _logger.info(f"Disk: {params.get('disk_size', 'N/A')} GB")

            _type = params.get('type')
            if _type:
                _type = _type.lower()  # Ensure server type is lowercase for Hetzner API
            location = 'fsn1'

            if _type:
                hetzner_server = self.create_server(name, _type, provider, location)
                if 'error' in hetzner_server:
                    return hetzner_server
                    
                response['ip'] = self.get_server_ipv4(hetzner_server['id'], provider)            
                time.sleep(40)
                response['password'] = self.reset_password(hetzner_server['id'], provider)
            else:
                return {'error': True, 'message': _('Server type not specified in parameters.')}
                
            return response
            
        except Exception as e:
            _logger.error(f"Unexpected error in create_hetzner_server: {str(e)}")
            return {'error': True, 'message': _('An unexpected error occurred while creating the server. Please contact support.')}
    
    def get_client(self, provider):
        try:
            if not provider or not provider.token:
                raise UserError(_('No valid cloud provider or API token configured.'))
                
            client = Client(token=provider.token)
            return client
            
        except Exception as e:
            _logger.error(f"Failed to create Hetzner client: {str(e)}")
            raise UserError(_('Failed to connect to Hetzner Cloud. Please check your API credentials.'))

    def create_server(self, name, type, provider, location):
        try:
            client = self.get_client(provider)
            
            # Ensure server type is lowercase for Hetzner API
            type = type.lower() if type else type
            
            _logger.info(f"Creating server '{name}' with type '{type}' in location '{location}'")
            
            if location:
                response = client.servers.create(
                    name=name,
                    server_type=ServerType(name=type),
                    image=Image(name="ubuntu-24.04"),
                    location=Location(name=location)
                )
            else:
                response = client.servers.create(
                    name=name,
                    server_type=ServerType(name=type),
                    image=Image(name="ubuntu-24.04")
                )
                
            server = response.server
            _logger.info(f"Server created successfully: {server.id} - {server.name} - {server.status}")
            
            return {'id': server.id, 'password': response.root_password}
            
        except APIException as e:
            _logger.error(f"Hetzner API error while creating server: {str(e)}")
            
            # Handle specific Hetzner API errors with user-friendly messages
            error_message = str(e).lower()
            
            if 'resource_unavailable' in error_message:
                return {'error': True, 'message': _(
                    f'The requested server type "{type}" is temporarily unavailable in location "{location}". '
                    'Please try again later or contact support for alternative options.'
                )}
            elif 'server_type not found' in error_message or 'not_found' in error_message:
                return {'error': True, 'message': _(
                    f'The server type "{type}" does not exist. Please check the server configuration.'
                )}
            elif 'limit_exceeded' in error_message or 'quota' in error_message:
                return {'error': True, 'message': _(
                    'Account limit exceeded. You have reached the maximum number of servers allowed. '
                    'Please contact support to increase your quota.'
                )}
            elif 'payment' in error_message or 'billing' in error_message:
                return {'error': True, 'message': _(
                    'Payment issue detected. Please check your billing information and try again.'
                )}
            elif 'unauthorized' in error_message or 'forbidden' in error_message:
                return {'error': True, 'message': _(
                    'Authentication failed. Please check your Hetzner API credentials.'
                )}
            else:
                return {'error': True, 'message': _(
                    f'Server creation failed: {str(e)}. Please contact support if this problem persists.'
                )}
                
        except Exception as e:
            _logger.error(f"Unexpected error in create_server: {str(e)}")
            return {'error': True, 'message': _(
                'An unexpected error occurred while creating the server. Please contact support.'
            )}
    
    def reset_password(self, server_id, provider):
        try:
            client = self.get_client(provider)
            server = client.servers.get_by_id(int(server_id))
            reset_password = client.servers.reset_password(server)
            _logger.info(f"Password reset successfully for server {server_id}")
            return reset_password.root_password
            
        except APIException as e:
            _logger.error(f"Hetzner API error while resetting password: {str(e)}")
            raise UserError(_('Failed to reset server password. Please try again or contact support.'))
            
        except Exception as e:
            _logger.error(f"Unexpected error in reset_password: {str(e)}")
            raise UserError(_('An unexpected error occurred while resetting the password.'))
    
    def get_server_ipv4(self, server_id, provider):
        try:
            client = self.get_client(provider)
            server = client.servers.get_by_id(int(server_id))
            ip = server.public_net.primary_ipv4.ip
            _logger.info(f"Retrieved IP {ip} for server {server_id}")
            return ip
            
        except APIException as e:
            _logger.error(f"Hetzner API error while getting server IP: {str(e)}")
            raise UserError(_('Failed to retrieve server IP address. Please try again or contact support.'))
            
        except Exception as e:
            _logger.error(f"Unexpected error in get_server_ipv4: {str(e)}")
            raise UserError(_('An unexpected error occurred while retrieving the server IP.'))
    

    # >>>>>> not used
    def get_servers(self):
        client = self.get_client()
        _logger.warning("hetzner client >>")
        _logger.warning(client)
        servers = client.servers.get_all()
        _logger.warning("hetzner servers >>")
        _logger.warning(servers)
        for server in servers:
            _logger.warning(f"{server.id=} {server.name=} {server.public_net.primary_ipv4.ip=}")
            try:
                server.delete()
                pass
            except:
                pass  

    def get_primary_ips(self):
        client = self.get_client()
        _logger.warning("hetzner client >>")
        _logger.warning(client)
        primary_ips = client.primary_ips.get_all()
        _logger.warning("hetzner servers >>")
        _logger.warning(primary_ips)
        for primary_ip in primary_ips:
            _logger.warning(f"{primary_ip.id=}  {primary_ip.ip=} {primary_ip.type=} {primary_ip.datacenter.id=}")
    
    def get_actions(self):
        client = self.get_client()
        _logger.warning("hetzner action >>")
        _logger.warning(client)
        actions = client.actions.get_all()
        _logger.warning("hetzner actions >>")
        _logger.warning(actions)
        for action in actions:
            _logger.warning(f"{action.id=}  {action.resources=}")