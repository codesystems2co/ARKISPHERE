#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields
import logging
_logger = logging.getLogger(__name__)

class sh_sale_order_line(models.Model):
    _inherit = "sale.order.line"

    is_kube_core_installed = fields.Boolean(default=False)

    def kube_core_install(self):
        query = """
            SELECT sol.id, sol.so_server, so.name 
            FROM sale_order_line sol
            LEFT JOIN sale_order so ON sol.order_id = so.id
            WHERE sol.so_server IS NOT NULL AND sol.is_kube_core_installed = false;
        """
        
        # Execute the query using Odoo's cursor
        self.env.cr.execute(query)
        
        # Fetch all results
        order_lines_ids = self.env.cr.fetchall()
        
        # Convert the result tuples to a list of ids
        # fetchall returns list of tuples [(id1,), (id2,)], so we convert it to [id1, id2, ...]
        order_lines_ids = [record[0] for record in order_lines_ids]

        if order_lines_ids:
            for order_lines_id in order_lines_ids:                
                order_line = self.env["sale.order.line"].sudo().browse(int(order_lines_id))
                _logger.warning("order_line >>" + str(order_line.so_server.name))

                if order_line.so_server:
                    if order_line.so_server.physical_server:                        
                        ssh = self.env["sale.order"].sudo().get_ssh(order_line.so_server.physical_server)                        
                        
                        command = str("apt update -y")
                        stdin, stdout, stderr = ssh.exec_command(command)
                        for line in iter(stdout.readline, ""): pass
                        for line in iter(stderr.readline, ""): pass

                        command = str("apt install snapd -y")
                        stdin, stdout, stderr = ssh.exec_command(command)
                        for line in iter(stdout.readline, ""): pass
                        for line in iter(stderr.readline, ""): pass

                        command = str("snap install microk8s --classic --channel=1.25/stable")
                        stdin, stdout, stderr = ssh.exec_command(command)
                        for line in iter(stdout.readline, ""): pass
                        for line in iter(stderr.readline, ""): pass
                        
                        command = str("iptables -P FORWARD ACCEPT")
                        stdin, stdout, stderr = ssh.exec_command(command)
                        for line in iter(stdout.readline, ""): pass
                        for line in iter(stderr.readline, ""): pass

                        command = str("apt install nginx -y")
                        stdin, stdout, stderr = ssh.exec_command(command)
                        for line in iter(stdout.readline, ""): pass
                        for line in iter(stderr.readline, ""): pass

                        command = str("apt install certbot -y")
                        stdin, stdout, stderr = ssh.exec_command(command)
                        for line in iter(stdout.readline, ""): pass
                        for line in iter(stderr.readline, ""): pass

                        command = str("apt install certbot python3-certbot-nginx -y")
                        stdin, stdout, stderr = ssh.exec_command(command)
                        for line in iter(stdout.readline, ""): pass
                        for line in iter(stderr.readline, ""): pass

                        command = str("mkdir -m 777 /data")
                        stdin, stdout, stderr = ssh.exec_command(command)

                        command = str("mkdir -m 777 /home/kubernets")
                        stdin, stdout, stderr = ssh.exec_command(command)

                        command = str("/snap/bin/microk8s enable dns")
                        stdin, stdout, stderr = ssh.exec_command(command)
                        for line in iter(stdout.readline, ""): pass
                        for line in iter(stderr.readline, ""): pass

                        ssh.close()

                        order_line.sudo().update({'is_kube_core_installed':True})