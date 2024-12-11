# -*- coding: utf-8 -*-
from odoo import models, fields, _
import xmlrpc
import logging
import base64
from odoo.http import request
_logger = logging.getLogger(__name__)

class sh_backup_revision (models.Model):
    _name = 'sh.backup.revision'

    name = fields.Datetime(string='Date time', readonly=True)
    date = fields.Date(string='Date', readonly=True)
    branch = fields.Many2one(comodel_name="sh.git_branch", string="Branch",  help="", readonly=True)
    repository = fields.Many2one(comodel_name="sh.git_repository", string="Repository",  related="branch.repository")
    autor = fields.Many2one(comodel_name="git.autor",string="Autor",  related="repository.autor", readonly=True)
    username = fields.Char(string="Username",  related="autor.username", readonly=True)
    version = fields.Char(string="Version", readonly=True)
    revision = fields.Char(string="Revision", readonly=True)
    type = fields.Selection([('automatic','Automatic'),('manual','Manual')], string="Type", readonly=True)
    
    def get_branch_backup_revisions(self, branch_id):
        revisions = request.env['sh.backup.revision'].sudo().search_read([('branch','=',int(branch_id))],['id', 'name','version','type','revision','branch'],order='name desc')        
        return revisions
