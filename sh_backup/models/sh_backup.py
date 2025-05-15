# -*- coding: utf-8 -*-
from odoo import models, fields, _
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from datetime import datetime
from datetime import date
import shutil
import xmlrpc
import base64
import uuid
import random
import os
import logging
import sys
_logger = logging.getLogger(__name__)

class sh_backup (models.Model):
    _name = 'sh.backup'

    name = fields.Datetime(string='Name')

    def restore_from_local(self, branch_id, revision):
        response = {'error':False}
        file_path = '/var/lib/odoo/file-system-backups/' + str(revision)
        if os.path.isdir(file_path):
            branch = self.env['sh.git_branch'].sudo().browse(int(branch_id))
            _logger.warning(branch.kuber_exposers.ip )
            _logger.warning(branch.kuber_exposers.domain )
            hostname = branch.kuber_exposers.domain if branch.kuber_exposers.domain else branch.kuber_exposers.ip
            service_hostname = str('http://') + str(hostname) + str(':')+ str(branch.kuber_exposers.port)
            db_files = os.listdir(file_path)

            ssh = self.env["kuber.deploy"].sudo().get_ssh(branch.repository.so_server.physical_server)
            odoo_conf = '/data/uid' + str(branch.repository.autor.id) + str('/')  + str(branch.repository.autor.username) + str(branch.repository.id) + str('v1/odoo.conf')
            admin_password = self.env["sh.git_repository"].sudo().get_admin_password(odoo_conf, ssh)
            if len(db_files) > 0 :
                for db_file in db_files:                    
                    db_name = str(db_file).replace('.zip','')
                    db_file = file_path + str('/') + db_file
                    with open(db_file, "rb") as f:
                        bytes = f.read()
                        database64 = base64.b64encode(bytes).decode()
                        _logger.warning("Dropping database >>")
                        _logger.warning(db_name)
                        self.drop_database(admin_password, db_name, service_hostname)
                        _response = self.env["sh.git_repository"].sudo().restore_database(admin_password, db_name, database64, service_hostname)
                        if _response['error'] == True:
                            response['error'] = True
                            response['message'] = _response['message']
                    
        else:
            response['error'] = True
            response['message'] = _('Revision does not exist in filesystem.')
        return response


    def download_from_local(self, revision):
        response = {'error':False, 'base':None}
        file_path = '/var/lib/odoo/file-system-backups/' + str(revision)
        if os.path.isdir(file_path):
            try:
                shutil.make_archive(file_path, 'zip', file_path)
                filename = revision+str('.zip')
                with open(file_path+str('.zip'), 'rb') as binary_file:
                    binary_file_data = binary_file.read()
                    base64_encoded_data = base64.b64encode(binary_file_data)
                    base64_output = base64_encoded_data.decode('utf-8')
                    response['base'] = base64_output
                    response['filename'] = filename

                if os.path.isfile(file_path+'.zip'):
                    os.remove(file_path+'.zip')

            except Exception as e:
                response['error'] = True
                response['message'] = getattr(e, 'message', repr(e))
        else:
            response['error'] = True
            response['message'] = _('Revision does not exist in filesystem.')
        return response

    def download_database(self, admin_password, db_name, revision, kube_service):        
        try:
            server_proxy = xmlrpc.client.ServerProxy(str(kube_service)+str('/xmlrpc/db'))
            base64_encoded = server_proxy.dump(admin_password, db_name, 'zip')
            os.umask(0)
            if (not os.path.isdir(str("/var/lib/odoo/file-system-backups"))):
                os.mkdir(str("/var/lib/odoo/file-system-backups"),mode=0o777)
            os.umask(0)
            if (not os.path.isdir(str("/var/lib/odoo/file-system-backups/" + str(revision)))):
                os.mkdir(str("/var/lib/odoo/file-system-backups/") + str(revision),mode=0o777)                
            with open('/var/lib/odoo/file-system-backups/' + str(revision) + '/' + str(db_name) + str('.zip'), 'wb') as backup_file:
                decode = base64.b64decode(base64_encoded)
                backup_file.write(decode)
        except Exception as e:
            message = getattr(e, 'message', repr(e))
            line = " ON LINE " + format(sys.exc_info()[-1].tb_lineno)
            _logger.warning(message)
            _logger.warning(line)
            if '<Fault' in message:
                try:
                    message = str(message).split(':')[0]
                except:
                    pass
            return {'error':True, 'message':message}
        return {'error':False}
    
    def drop_database(self, admin_password, db_name, kube_service):        
        try:
            server_proxy = xmlrpc.client.ServerProxy(str(kube_service)+str('/xmlrpc/db'))
            response = server_proxy.drop(admin_password, db_name)
            _logger.warning('drop_database response >>')
            _logger.warning(response)
        except Exception as e:
            message = getattr(e, 'message', repr(e))
            _logger.warning(message)
            if '<Fault' in message:
                try:
                    message = str(message).split(':')[0]
                except:
                    pass
            return {'error':True, 'message':message}
        return {'error':False}
    
    def get_databases(self, kube_service):        
        try:
            server_proxy = xmlrpc.client.ServerProxy(str(kube_service)+str('/xmlrpc/db'))
            databases = server_proxy.list()
            _logger.warning('get_databases databases >>')
            _logger.warning(databases)
            return {'error':False, 'databases':databases}
        except Exception as e:
            message = getattr(e, 'message', repr(e))
            _logger.warning(message)
            if '<Fault' in message:
                try:
                    message = str(message).split(':')[0]
                except:
                    pass
            return {'error':True, 'message':message}
        return {'error':False}
    
    def backup_database(self):
        repositories = self.env["sh.git_repository"].sudo().search_read([],['id'])
        if repositories:
            for repository in repositories:
                repository = self.env["sh.git_repository"].sudo().browse(int(repository['id']))
                if repository.branches:
                    for branch in repository.branches:
                        self.create_revision(branch)
    
    def manual_backup_database(self, branch_id):
        branch = self.env["sh.git_branch"].sudo().browse(int(branch_id))
        self.create_revision(branch,'manual')
    
    def create_revision(self, branch, _type="automatic"):
        kube_service = str('http://') + str(branch.kuber_exposers.ip) + str(':') + str(branch.kuber_exposers.port)
        _response = self.get_databases(kube_service)
        if not _response['error']:
            if _response['databases']:
                
                for db_name in _response['databases']:
                    if db_name:
                        _logger.warning('backup_database params >>')
                        _logger.warning(branch.repository)
                        ssh = self.env["kuber.deploy"].sudo().get_ssh(branch.repository.so_server.physical_server)
                        odoo_conf = '/data/uid' + str(branch.repository.autor.id) + str('/')  + str(branch.repository.autor.username) + str(branch.repository.id) + str('v1/odoo.conf')
                        rnd = random.Random()
                        revision = uuid.UUID(int=rnd.getrandbits(128), version=4)
                        admin_password = self.env["sh.git_repository"].sudo().get_admin_password(odoo_conf, ssh)                        

                        _logger.warning('backup_database params >>')
                        _logger.warning(revision)
                        _logger.warning(admin_password)
                        _logger.warning(kube_service)
                        
                        response = self.download_database(admin_password, db_name, revision, kube_service)
                        if response['error'] == False:
                            item = {
                                        'name': fields.Datetime.now(),
                                        'date': fields.Date.today(),
                                        'revision': revision,
                                        'type': _type,
                                        'version': branch.repository.kuber_deploy.kuber_docker_image.version,
                                        'branch': int(branch.id),
                                    }

                            backup_revision = self.env['sh.backup.revision'].sudo().create(item)
                            _logger.warning('backup_revision >>')
                            _logger.warning(backup_revision)

    def clean_interval_tree(self):
        repositories = self.env["sh.git_repository"].sudo().search_read([],['id'])
        if repositories:
            for repository in repositories:
                repository = self.env["sh.git_repository"].sudo().browse(int(repository['id']))
                if repository.branches:
                    for branch in repository.branches:
                        branch_backup_revisions = self.env["sh.backup.revision"].sudo().search_read([('branch','=',int(branch.id))],['id'])
                        if branch_backup_revisions:
                            for revision in branch_backup_revisions:
                                revision = self.env["sh.backup.revision"].sudo().browse(int(revision['id']))
                                drop = True
                                begin = date.today()
                                # applies first week
                                last_weekdays = self.get_last_weekdays(begin)
                                # applies second week for current month
                                last_day_weekdays = self.get_last_day_weekdays(begin)
                                # applies current year
                                last_day_months = self.get_last_day_months(begin)

                                for last_day_month in last_day_months:
                                    if revision.date == last_day_month:
                                        drop = False
                                        break

                                if drop:
                                    for last_day_week in last_day_weekdays:                                            
                                            if revision.date == last_day_week:
                                                drop = False
                                                break
                                            else:
                                                drop = True
                                if drop:
                                    if revision.date >= last_weekdays[1] and revision.date <= last_weekdays[0] :
                                        drop = False

                                _logger.warning('drop >>')
                                _logger.warning(drop)
                                if drop:
                                    path = '/var/lib/odoo/file-system-backups/' + str(revision.revision)
                                    _logger.warning(path)
                                    if os.path.isdir(path):
                                        shutil.rmtree(path)
                                        self.unlink_from_services(revision)
                                        revision.unlink()
                                    else:
                                        _logger.warning('no path >>')

    def get_last_weekdays(self, begin):
        end = begin + timedelta(days=-7)
        return [begin, end]        
    
    #exludes last week
    def get_last_day_weekdays(self, begin):
        begin = begin + timedelta(days=-7)
        dates = []
        for i in range(1,5):
            last_day_week = begin - timedelta(days=(7*i))
            if last_day_week.month == begin.month:
                dates.append(last_day_week)
        return dates

    #exludes last month
    def get_last_day_months(self, begin):
        dates = []
        for month in range(1, 13):
            begin = date.today() - relativedelta(months=month)
            next_month = begin.replace(day=28) + timedelta(days=4)
            last_day_of_month = next_month - timedelta(days=next_month.day)
            dates.append(last_day_of_month)
        return dates
    
    def unlink_from_services(self):
        return