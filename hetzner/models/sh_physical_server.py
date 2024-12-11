# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from hcloud import Client
from hcloud.images import Image
from hcloud.server_types import ServerType
import time
import logging
_logger = logging.getLogger(__name__)
class hetzner_server(models.Model):
    _inherit = "sh.physical_server"

    def create_hetzner_server(self, name, params, provider=None):

        if not provider:
            provider = self.env["sh.cloud.provider"].sudo().search_read([('_default','=',True)],['id'],limit=1)
            if provider:
                provider = self.env["sh.cloud.provider"].sudo().browse(int(provider[0]['id']))
            if not provider:
                return {'error':True, 'message':_('A default cloud provider must be selected.')}

        response = {'ip':None, 'password':None}
        _type = None
        _logger.warning('hetzner specification >>>')
        _logger.warning(int(params['processor_core']))
        _logger.warning(int(params['ram_size']))
        _logger.warning(int(params['disk_size']))

        if int(params['processor_core']) == 2 and int(params['ram_size']) == 4 and int(params['disk_size']) == 40:
            _type = 'cax11'
        
        if int(params['processor_core']) == 4 and int(params['ram_size']) == 8 and int(params['disk_size']) == 80:
            _type = 'cax21'

        if int(params['processor_core']) == 8 and int(params['ram_size']) == 16 and int(params['disk_size']) == 160:
            _type = 'cax31'
        
        if int(params['processor_core']) == 16 and int(params['ram_size']) == 32 and int(params['disk_size']) == 320:
            _type = 'cax41'

        _logger.warning("hetzner _type >>>")
        _logger.warning(_type)

        if _type:
            hetzner_server = self.create_server(name, _type, provider)
            response['ip'] = self.get_server_ipv4(hetzner_server['id'],provider)            
            time.sleep(40)
            response['password'] = self.reset_password(hetzner_server['id'],provider)
        else:
            return {'error':_('Hetzner Provider has not any server types with following specifications:\n Cores: '+str(params['processor_core'])+str('\n RAM: ')+str(params['ram_size']))+str('\n SSD: ')+str(params['disk_size'])}
        return response
    
    def get_client(self,provider):
        client = Client(token=provider.token)
        return client

    def create_server(self, name, type, provider):
        client = self.get_client(provider)
        response = client.servers.create(
                                            name=name,
                                            server_type = ServerType(name=type),
                                            image=Image(name="ubuntu-22.04"),
                                        )
        server = response.server
        _logger.warning('server details >>')
        _logger.warning(f"{server.id=} {server.name=} {server.status=}")
        _logger.warning(f"root password: {response.root_password}")
        
        return {'id':server.id,'password':response.root_password}
    
    def reset_password(self, server_id, provider):
        client = self.get_client(provider)
        server = client.servers.get_by_id(int(server_id))
        reset_password = client.servers.reset_password(server)
        _logger.warning('reseted password for server id >>')
        _logger.warning(server_id)
        _logger.warning(f"{server.id=} {server.name=} {server.status=}")
        _logger.warning(f"root password: {reset_password.root_password}")
        return reset_password.root_password
    
    def get_server_ipv4(self, server_id, provider):
        client = self.get_client(provider)
        server = client.servers.get_by_id(int(server_id))
        return server.public_net.primary_ipv4.ip
    

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