#!/usr/bin/python
#-*- coding: utf-8 -*-

import logging
from github import Github, Auth

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

class sh_res_partner(models.Model):

    _inherit = "res.partner"
    # autor fields
    access_token = fields.Char( string="Access Token",  help="https://github.com/settings/tokens")
    is_autor = fields.Boolean( string="Is autor",  help="", default=True)
    is_collaborator = fields.Boolean( string="Is collaborator",  help="")
    platform = fields.Selection( [('github','Github'), ('gitlab','Gitlab'), ('odoo','Odoo')], string="Platform",  help="")
    identifier = fields.Char( string="Identifier",  help="")
    name = fields.Char( string="Autor",  help="")
    username = fields.Char( string="Username",  help="")
    _gpassword = fields.Char( string="Git Password",  help="")
    html_url = fields.Char( string="Html url",  help="")

    #collabrator fields
    name = fields.Char( string="Collaborator",  help="")
    is_collaborator = fields.Boolean( string="Is collaborator",  help="", default=True)    
    permission = fields.One2many(comodel_name="sh.git_permissions",  inverse_name="collaborator",  string="Permission",  help="")
    
    # GitHub organization fields
    is_organization = fields.Boolean(string="Is Organization", help="Marks this partner as a GitHub organization", default=False)
    github_org_id = fields.Char(string="GitHub Org ID", help="GitHub organization ID")

    def get_current_autor_id(self):
        return self.env.user.partner_id.id

    def _sync_partner_github_organizations(self, partner, is_manual=False):
        """
        Core logic to sync GitHub organizations for a single partner
        Returns (created_count, updated_count)
        """
        log_prefix = "   " if not is_manual else ""
        
        try:
            # Authenticate to GitHub
            _logger.info('%s🔐 Creating GitHub authentication...' % log_prefix)
            auth = Auth.Token(partner.access_token)
            github_client = Github(auth=auth)
            
            _logger.info('%s👤 Getting GitHub user...' % log_prefix)
            github_user = github_client.get_user()
            _logger.info('%sGitHub user login: %s' % (log_prefix, github_user.login))
            
            _logger.info('%s🏢 Fetching organizations...' % log_prefix)
            organizations = github_user.get_orgs()
            org_list = list(organizations)
            _logger.info('%s📊 Found %d organizations' % (log_prefix, len(org_list)))
            
            created_count = 0
            updated_count = 0
            
            for i, org in enumerate(org_list):
                _logger.info('%s--- Processing org %d/%d: %s (ID: %s) ---' % 
                           (log_prefix, i+1, len(org_list), org.name or org.login, org.id))
                
                # Check if organization partner already exists
                existing_org_partner = self.env['res.partner'].search([
                    ('github_org_id', '=', str(org.id)),
                    ('parent_id', '=', partner.id),
                    ('is_organization', '=', True)
                ])
                _logger.info('%sExisting partner found: %s' % (log_prefix, bool(existing_org_partner)))
                
                if not existing_org_partner:
                    _logger.info('%s✨ Creating new organization partner...' % log_prefix)
                    org_partner_vals = {
                        'name': org.name or org.login,
                        'parent_id': partner.id,
                        'email': partner.email,
                        'phone': partner.phone,
                        'street': partner.street,
                        'city': partner.city,
                        'zip': partner.zip,
                        'country_id': partner.country_id.id if partner.country_id else False,
                        'state_id': partner.state_id.id if partner.state_id else False,
                        'is_organization': True,
                        'github_org_id': str(org.id),
                        'is_company': False,
                        'supplier_rank': 0,
                        'customer_rank': 0,
                        'type': 'invoice',
                        'platform': 'github',
                        'html_url': org.html_url if hasattr(org, 'html_url') else '',
                    }
                    new_partner = self.env['res.partner'].create(org_partner_vals)
                    _logger.info('%s✅ Created partner ID: %s' % (log_prefix, new_partner.id))
                    created_count += 1
                else:
                    _logger.info('%s🔄 Checking if update needed...' % log_prefix)
                    
                    update_vals = {}
                    # Check all fields that need to stay in sync
                    fields_to_sync = {
                        'name': org.name or org.login,
                        'email': partner.email,
                        'phone': partner.phone,
                        'street': partner.street,
                        'city': partner.city,
                        'zip': partner.zip,
                        'country_id': partner.country_id.id if partner.country_id else False,
                        'state_id': partner.state_id.id if partner.state_id else False,
                        'type': 'invoice'
                    }
                    
                    for field, new_value in fields_to_sync.items():
                        current_value = getattr(existing_org_partner, field)
                        if field in ['country_id', 'state_id']:
                            current_value = current_value.id if current_value else False
                        
                        if current_value != new_value:
                            _logger.info('%s📝 Updating organization %s...' % (log_prefix, field))
                            update_vals[field] = new_value
                    
                    if update_vals:
                        existing_org_partner.write(update_vals)
                        _logger.info('%s✅ Updated partner: %s' % (log_prefix, list(update_vals.keys())))
                        updated_count += 1
                    else:
                        _logger.info('%s⏭️ No update needed' % log_prefix)
            
            return created_count, updated_count
            
        except Exception as e:
            _logger.error('%s❌ Error syncing organizations for partner %s: %s' % (log_prefix, partner.name, str(e)))
            raise e

    def action_sync_github_organizations(self):
        """
        Manual action to sync GitHub organizations for current partner
        """
        _logger.info("=== MANUAL GITHUB SYNC DEBUG START ===")
        _logger.info("Partner: %s (ID: %s)" % (self.name, self.id))
        _logger.info("Access token exists: %s" % bool(self.access_token))
        _logger.info("Platform: %s" % self.platform)
        _logger.info("Is autor: %s" % self.is_autor)
        
        if self.access_token and self.platform == 'github' and self.is_autor:
            _logger.info("✅ Conditions met - proceeding with sync")
            try:
                created_count, updated_count = self._sync_partner_github_organizations(self, is_manual=True)
                
                _logger.info("🎯 SYNC COMPLETE!")
                _logger.info("📊 FINAL RESULTS:")
                _logger.info("   - Created: %d organizations" % created_count)
                _logger.info("   - Updated: %d organizations" % updated_count)
                _logger.info("=== MANUAL GITHUB SYNC DEBUG END ===")
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'GitHub Sync Complete',
                        'message': f'Created {created_count} new organizations, updated {updated_count} existing ones.',
                        'type': 'success',
                    }
                }
            except Exception as e:
                _logger.error("❌ GITHUB SYNC ERROR!")
                _logger.error("Error type: %s" % type(e).__name__)
                _logger.error("Error message: %s" % str(e))
                _logger.error("=== MANUAL GITHUB SYNC DEBUG END (ERROR) ===")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'GitHub Sync Error',
                        'message': f'Error: {str(e)}',
                        'type': 'danger',
                    }
                }
        else:
            _logger.warning("❌ SYNC CONDITIONS NOT MET!")
            _logger.warning("   - Access token: %s" % bool(self.access_token))
            _logger.warning("   - Platform is github: %s" % (self.platform == 'github'))
            _logger.warning("   - Is autor: %s" % self.is_autor)
            _logger.warning("=== MANUAL GITHUB SYNC DEBUG END (SKIPPED) ===")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Sync Not Available',
                    'message': 'GitHub sync is only available for partners with GitHub credentials.',
                    'type': 'warning',
                }
            }

    def sync_github_organizations(self):
        """
        Cron method to sync GitHub organizations for all partners with GitHub credentials
        """
        _logger.info('=== CRON GITHUB ORGANIZATIONS SYNC START ===')
        
        # 1. Fetch all partners with GitHub credentials
        _logger.info('🔍 Searching for partners with GitHub credentials...')
        partners_with_github = self.search([
            ('access_token', '!=', False),
            ('platform', '=', 'github'),
            ('is_autor', '=', True)
        ])
        
        _logger.info('📊 Found %d partners with GitHub credentials' % len(partners_with_github))
        for partner in partners_with_github:
            _logger.info('   - Partner: %s (ID: %s)' % (partner.name, partner.id))
        
        total_created = 0
        total_updated = 0
        
        for i, partner in enumerate(partners_with_github):
            _logger.info('--- Processing partner %d/%d: %s ---' % (i+1, len(partners_with_github), partner.name))
            try:
                partner_created, partner_updated = self._sync_partner_github_organizations(partner, is_manual=False)
                total_created += partner_created
                total_updated += partner_updated
                _logger.info('✅ Completed partner %s: created %d, updated %d' % (partner.name, partner_created, partner_updated))
                        
            except Exception as e:
                _logger.error('❌ Error syncing organizations for partner %s: %s' % (partner.name, str(e)))
                continue
        
        _logger.info('GitHub organizations sync completed')
        return True