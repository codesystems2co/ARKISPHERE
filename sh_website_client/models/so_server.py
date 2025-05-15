#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
from odoo import http
import logging
import inspect

_logger = logging.getLogger(__name__)

class so_server(models.Model):

    _inherit = "so.server"

    order_line = fields.One2many('sale.order.line', 'so_server', string="Sale Order Line", help="")
    sale_order = fields.Many2one('sale.order', related="order_line.order_id", string="Sale Order", help="")

    def get_current_server(self):
        """
        Unified method to get server information including ID, hardware resources, and physical server info
        Returns a dictionary with all server details or server ID if only ID is requested
        """
        try:
            so_server_id = None
            if('server' in http.request.params):
                so_server_id = http.request.params['server']
                
                # If no server ID, return None
                if not so_server_id:
                    return None
                    
                # If called from a place that only needs the ID, return just the ID
                # This maintains backward compatibility
                caller_frame = inspect.currentframe().f_back
                if caller_frame and 'self' in caller_frame.f_locals:
                    caller = caller_frame.f_locals['self']
                    if hasattr(caller, '_name') and caller._name == 'so.server':
                        return so_server_id
                
                # Otherwise, return complete server information
                try:
                    server_id = int(so_server_id)
                    server = self.env['so.server'].sudo().browse(server_id)
                    
                    if not server.exists():
                        return so_server_id  # Fallback to just returning ID
                    
                    # Get hardware resources
                    resources = {}
                    try:
                        resources['ram'] = server.ram_size_gb or "0 GB"
                    except:
                        resources['ram'] = "0 GB"
                    
                    try:
                        resources['disk'] = server.disk_size_gb or "0 GB"
                    except:
                        resources['disk'] = "0 GB"
                    
                    try:
                        resources['cpu'] = server.processor_core_gb or "0 cores"
                    except:
                        resources['cpu'] = "0 cores"
                    
                    # Get physical server info
                    physical_info = {}
                    try:
                        # Try different possible relation field names
                        domain = ['|', '|', '|',
                            ('so_server_id', '=', server_id),
                            ('so_server', '=', server_id),
                            ('server_id', '=', server_id),
                            ('server', '=', server_id)
                        ]
                        
                        physical_server = self.env['sh.physical_server'].sudo().search(domain, limit=1)
                        if physical_server:
                            physical_info = {
                                'name': physical_server.name or "N/A",
                                'ip': physical_server.ip or "N/A",
                                'ssh_host': physical_server.ssh_host or "N/A"
                            }
                    except Exception as e:
                        _logger.error(f"Error finding physical server: {e}")
                    
                    # Return combined information
                    return {
                        'id': so_server_id,
                        'resources': resources,
                        'physical': physical_info
                    }
                    
                except Exception as e:
                    _logger.error(f"Error getting server details: {e}")
                    return so_server_id  # Fallback to just returning ID
                    
        except Exception as e:
            # Log the error but don't crash
            _logger.error(f"Error in get_current_server: {e}")
            return None