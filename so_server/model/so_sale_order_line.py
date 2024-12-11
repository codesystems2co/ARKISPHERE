#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields

import logging
_logger = logging.getLogger(__name__)

class sh_sale_order_line(models.Model):
    _inherit = "sale.order.line"

    is_kube_core_installed = fields.Boolean(default=False)

    def kube_core_install(self):
        order_lines_ids = self.env["sale.order.line"].sudo().search_read([('is_kube_core_installed','=',True)],['id'])
        if order_lines_ids:
            for order_lines_id in order_lines_ids:
                order_line = self.env["sale.order.line"].sudo().browse(int(order_lines_id['id']))
                if not order_line.so_server.git_repositories:
                    order_line.sudo().update({'is_kube_core_installed':False})

        order_lines_ids = self.env["sale.order.line"].sudo().search_read([('is_kube_core_installed','=',False)],['id'])
        if order_lines_ids:
            for order_lines_id in order_lines_ids:
                order_line = self.env["sale.order.line"].sudo().browse(int(order_lines_id['id']))
                if order_line.so_server:
                    if order_line.so_server.physical_server:                        
                        ssh = self.env["sale.order"].sudo().get_ssh(order_line.so_server.physical_server)                        
                        _logger.info(':: Updating server')
                        command = str("apt update -y")
                        stdin, stdout, stderr = ssh.exec_command(command)
                        for line in iter(stdout.readline, ""):
                            _logger.warning(line)
                        for line in iter(stderr.readline, ""):
                            _logger.warning(line)

                        _logger.info(':: Installing snapd')
                        command = str("apt install snapd")
                        stdin, stdout, stderr = ssh.exec_command(command)
                        for line in iter(stdout.readline, ""):
                            _logger.warning(line)
                        for line in iter(stderr.readline, ""):
                            _logger.warning(line)

                        _logger.info(':: Installing kubernets')
                        command = str("snap install microk8s --classic --channel=1.25/stable")
                        stdin, stdout, stderr = ssh.exec_command(command)
                        for line in iter(stdout.readline, ""):
                            _logger.warning(line)
                        for line in iter(stderr.readline, ""):
                            _logger.warning(line)                       
                        
                        
                        _logger.info(':: ACCEPT Forward')
                        command = str("iptables -P FORWARD ACCEPT")
                        stdin, stdout, stderr = ssh.exec_command(command)
                        for line in iter(stdout.readline, ""):
                            _logger.warning(line)
                        for line in iter(stderr.readline, ""):
                            _logger.warning(line)
                            

                        _logger.info(':: Installing nginx')
                        command = str("apt install nginx -y")
                        stdin, stdout, stderr = ssh.exec_command(command)
                        for line in iter(stdout.readline, ""):
                            _logger.warning(line)
                        for line in iter(stderr.readline, ""):
                            _logger.warning(line)

                        _logger.info(':: Installing certbot')
                        command = str("apt install certbot -y")
                        stdin, stdout, stderr = ssh.exec_command(command)
                        for line in iter(stdout.readline, ""):
                            _logger.warning(line)
                        for line in iter(stderr.readline, ""):
                            _logger.warning(line)

                        _logger.info(':: Installing certbot nginx plugin')
                        command = str("apt install certbot python3-certbot-nginx -y")
                        stdin, stdout, stderr = ssh.exec_command(command)
                        for line in iter(stdout.readline, ""):
                            _logger.warning(line)
                        for line in iter(stderr.readline, ""):
                            _logger.warning(line)

                        command = str("mkdir -m 777 /data")
                        stdin, stdout, stderr = ssh.exec_command(command)

                        command = str("mkdir -m 777 /home/kubernets")
                        stdin, stdout, stderr = ssh.exec_command(command)

                        _logger.info(':: Enable DNS')
                        command = str("/snap/bin/microk8s enable dns")
                        stdin, stdout, stderr = ssh.exec_command(command)
                        for line in iter(stdout.readline, ""):
                            _logger.warning(line)
                        for line in iter(stderr.readline, ""):
                            _logger.warning(line)

                        ssh.close()

                        order_line.sudo().update({'is_kube_core_installed':True})