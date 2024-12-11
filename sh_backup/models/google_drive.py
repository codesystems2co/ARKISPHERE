# -*- coding: utf-8 -*-
# powered by google drive
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaFileUpload
import io
import base64
import os
import sys
import shutil
from googleapiclient.errors import HttpError

from odoo import models, fields, _
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)

class sh_backup (models.Model):
    _inherit = 'sh.backup'

    def cron_storage(self):
        #folders = self.env["sh.backup.revision"].sudo().list_folders()
        #for folder in folders:
        #    self.env["sh.backup.revision"].sudo().delete_folder(folder['id'])
        #    self.env["sh.backup.revision"].sudo().list_files(folder['id'])
        #return 
        filter = [('google_drive_folder_id','=', None),('google_drive_folder_id','=', None),('google_drive_file_id','=', None)]
        revisions = self.env["sh.backup.revision"].sudo().search_read(filter, ['id'])
        _logger.warning("google drive revisions")
        _logger.warning(revisions)        
        for revision in revisions:
            item = {}
            revision = self.env["sh.backup.revision"].sudo().browse(int(revision['id']))
            _logger.warning("google drive revision")
            _logger.warning(revision.revision) 
            response = {'error':False, 'base':None}
            file_path = '/var/lib/odoo/file-system-backups/' + str(revision.revision)
            if os.path.isdir(file_path):
                os.chmod(file_path, 0o0777)
                shutil.make_archive(file_path, 'zip', file_path)                    
                if os.path.isfile(file_path+'.zip'):
                    os.chmod(file_path + '.zip', 0o0777)
                    try:                   
                        _folder_id = self.env['sh.backup.revision'].sudo().create_folder(revision.revision)
                        if _folder_id:
                            item['google_drive_folder_id'] = _folder_id

                            _file_id = self.env['sh.backup.revision'].sudo().create_file(revision.revision, file_path+'.zip', _folder_id)                            
                            if _file_id:
                                item['google_drive_file_id'] = _file_id    

                                _sharable_file_link = self.env['sh.backup.revision'].sudo().sharable_file(_file_id)                            
                                if _sharable_file_link:
                                    item['google_drive_share_file_link'] = _sharable_file_link                                                        

                        revision.sudo().update(item)

                        _logger.warning('google drive sharable link >>')
                        _logger.warning(revision.google_drive_share_file_link)
                        
                    except Exception as e:
                        response['error'] = True
                        response['message'] = getattr(e, 'message', repr(e))
                        _logger.warning( response['message'])
                        line = " ON LINE " + format(sys.exc_info()[-1].tb_lineno)
                        _logger.warning(line)

                        if os.path.isfile(file_path+'.zip'):
                            os.remove(file_path+'.zip')

                if os.path.isfile(file_path+'.zip'):
                    os.remove(file_path+'.zip')
            else:
                response['error'] = True
                response['message'] = _('Revision does not exist in filesystem.')
                _logger.warning( response['message'] )
                if os.path.isfile(file_path+'.zip'):
                        os.remove(file_path+'.zip')
        #return response

    def unlink_from_services(self, revision):
        _super = super(sh_backup, self).unlink_from_services()
        if revision.google_drive_file_id:
            self.env['sh.backup.revision'].sudo().delete_file(revision.google_drive_file_id)
        if revision.google_drive_folder_id:
            self.env['sh.backup.revision'].sudo().delete_folder(revision.google_drive_folder_id)
        return _super
    
    def download_from_local(self, revision):
        response = super(sh_backup, self).download_from_local(revision)
        _revision = self.env['sh.backup.revision'].sudo().search_read([('revision','=',revision)], ['google_drive_share_file_link'])
        if _revision:
            response['error'] = False
            response['google_drive_share_file_link'] = _revision[0]['google_drive_share_file_link']
        return response

class sh_backup_revision(models.Model):
    _inherit = 'sh.backup.revision'

    google_drive_folder_id = fields.Char(string="Folder", help="Folder as backup revision")
    google_drive_file_id = fields.Char(string="File", help="File as backup revision")
    google_drive_share_file_link = fields.Char(string="Share File", help="Compressed file as backup revision")
    
    def connect(self):
        try:
            provider = self.env["sh.cloud.provider"].sudo().search_read([('_type','=','goo_drive'), ('_default','=',True)], limit=1)
            if provider:
                provider = self.env["sh.cloud.provider"].sudo().browse(int(provider[0]['id']))
                if provider.credentials:
                    file_google_credentials = os.path.dirname(os.path.abspath(__file__)) + str('/service_account.json')
                    _logger.warning('file_google_credentials >>')
                    _logger.warning(file_google_credentials)
                    with open(file_google_credentials,'wb+') as f:
                        f.write(base64.b64decode(provider.credentials))

                    scope = ['https://www.googleapis.com/auth/drive']                
                    credentials = service_account.Credentials.from_service_account_file(
                                                filename=file_google_credentials, 
                                                scopes=scope)
                    service = build('drive', 'v3', credentials=credentials)
                    return service
                else:
                    _logger.warning("Google: No credentials")
                    return None 
            else:
                _logger.warning("Google: No no default provider")
                return None
        except HttpError as error:
            _logger.warning(f"An error occurred connecting: {error}")
            return None
    
    def create_folder(self, fname):
        try:
            service = self.connect()
            file_metadata = {
                "name": fname,
                "mimeType": "application/vnd.google-apps.folder",
            }
            folder = service.files().create(body=file_metadata, fields="id").execute()
            _logger.warning('drive folders >>>')
            _logger.warning(folder)
            return folder.get("id")

        except HttpError as error:
            _logger.warning(f"An error occurred creating a folder: {error}")
            return None
        
    def create_file(self, fname, file_path, fd_id):
        try:
            service = self.connect()
            file_metadata = {
                "name": fname,
                "parents": [fd_id],
            }
            media = MediaFileUpload(file_path ,mimetype='application/zip')
            file = service.files().create(body=file_metadata, media_body=media).execute()            
            _logger.warning('drive media file >>>')
            _logger.warning(file)
            return file.get("id")

        except HttpError as error:
            _logger.warning(f"An error occurred creating a folder: {error}")
            return None
        
    def list_folders(self):
        try:
            service = self.connect()
            page_token = None
            results = (
                service.files()
                .list(q="mimeType = 'application/vnd.google-apps.folder'",
                    spaces="drive",
                    fields="nextPageToken, files(id, name)",
                    pageToken = page_token)
                .execute()
            )
            folders = results.get("files", [])
            _logger.warning('drive folders >>>')
            _logger.warning(folders)
            return folders
        except HttpError as error:
            _logger.warning(f"An error occurred creating file: {error}")
            return None
    
    def list_files(self, fd_id):
        try:
            service = self.connect()
            results = service.files().list(q=f"'{fd_id}' in parents", fields="files(name)").execute()
            files = results.get('files', [])
            _logger.warning('drive files >>>')
            _logger.warning(files)
            return files
        except HttpError as error:
            _logger.warning(f"An error occurred creating file: {error}")
            return None
        
    def delete_file(self, file_id):
        try:
            service = self.connect()
            service.files().delete(fileId=file_id).execute()
            return True
        except HttpError as error:
            _logger.warning(f"An error occurred deleting file: {error}")
            return None
    
    def delete_folder(self, folder_id):
        try:
            service = self.connect()
            service.files().delete(fileId=folder_id).execute()
            return True
        except HttpError as error:
            _logger.warning(f"An error occurred deleting folder: {error}")
            return None

    def sharable_file(self, file_id):
        try:
            service = self.connect()
            flink = service.permissions().create(body={"role":"reader", "type":"anyone"}, fileId=file_id).execute()
            _logger.warning('drive files sharable >>>')
            _logger.warning(flink)
            link = str('https://drive.google.com/file/d/') + str(file_id)
            return link
        except HttpError as error:
            _logger.warning(f"An error occurred sharing file: {error}")
            return None
    
    def cron_upload(self):
        filter = [('google_drive_folder_id','=', None),('google_drive_folder_id','=', None),('google_drive_file_id','=', None)]
        revisions = self.env["sh.backup.revision"].sudo().search_read(filter, ['id'])
        for revision in revisions:
            item = {}
            revision = self.env["sh.backup.revision"].sudo().browse(int(revision['id']))
            response = {'error':False, 'base':None}
            file_path = '/var/lib/odoo/file-system-backups/' + str(revision)
            if os.path.isdir(file_path):
                try:
                    shutil.make_archive(file_path, 'zip', file_path)
                    if os.path.isfile(file_path+'.zip'):
                        _folder_id = self.env['sh.backup.revision'].sudo().create_folder(revision)
                        if _folder_id:
                            item['google_drive_folder_id'] = _folder_id

                            _file_id = self.env['sh.backup.revision'].sudo().create_file(revision, file_path, _folder_id)                            
                            if _file_id:
                                item['google_drive_file_id'] = _file_id    

                                _sharable_file_link = self.env['sh.backup.revision'].sudo().sharable_file(_file_id)                            
                                if _sharable_file_link:
                                    item['google_drive_share_file_link'] = _sharable_file_link                                                        

                        backup_revision = self.env['sh.backup.revision'].sudo().create(item)

                        _logger.warning('backup_revision >>')
                        _logger.warning(backup_revision)
                        
                except Exception as e:
                    response['error'] = True
                    response['message'] = getattr(e, 'message', repr(e))
                    _logger.warning( response['message'])
            else:
                response['error'] = True
                response['message'] = _('Revision does not exist in filesystem.')
                _logger.warning( response['message'] )
        return response