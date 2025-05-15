#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _

class sh_res_partner(models.Model):

    _inherit = "res.partner"

    # Ensure 'bitbucket' is an option in the existing 'platform' field from sh_git.
    # If 'platform' is defined in sh_git.sh_res_partner, this will add to it.
    # If 'platform' is not yet in this model, this will define it.
    platform = fields.Selection(selection_add=[('bitbucket', 'Bitbucket')], ondelete={'bitbucket': 'set null'})

    # --- Bitbucket to res.partner Field Mapping Suggestions ---
    # This model inherits from sh_git.sh_res_partner, so we try to reuse its fields.

    # Bitbucket 'display_name' (e.g., "Alex Grisales Rivera")
    # Odoo Standard: 'name' (res.partner.name) - This should be the primary field for the person's full name.
    #   -> maps to res.partner.name

    # Bitbucket primary 'email' (e.g., "codesystems.co@gmail.com")
    # Odoo Standard: 'email' (res.partner.email) - This should be the primary field for the person's email.
    #   -> maps to res.partner.email

    # Bitbucket 'username' (e.g., "arkiphere-admin")
    # Reuses: 'username' from sh_git.sh_res_partner (fields.Char(string="Username"))
    #   -> maps to self.username (which should be the field from sh_git)

    # Bitbucket 'uuid' (e.g., "{9669b6e5-23fd-44c1-aa93-5e7e90f3e14f}")
    # Reuses: 'identifier' from sh_git.sh_res_partner (fields.Char(string="Identifier"))
    #   -> maps to self.identifier

    # Bitbucket profile URL ('links.html.href')
    # Reuses: 'html_url' from sh_git.sh_res_partner (fields.Char(string="Html url"))
    #   -> maps to self.html_url

    # Bitbucket 'account_id' (e.g., "712020:f912c59b-d860-490c-a56f-d33be87ff473")
    # This is a Bitbucket-specific internal ID. It might be useful for deeper integration or logging.
    # Suggesting a new field if no generic 'external_account_id' exists in sh_git.
    bitbucket_account_id = fields.Char(string="Bitbucket Account ID", readonly=True, copy=False,
                                     help="Bitbucket's internal account_id for the user.")

    # Bitbucket OAuth Access Token (if you need to store it for future API calls by this module)
    # The 'access_token' field in sh_git.sh_res_partner seems intended for PATs/App Passwords.
    # For OAuth, if storing, it might need a different name or careful consideration of its use.
    # For now, we assume the signup controller might store it on res.users.oauth_access_token.
    # If a partner-level OAuth token for Bitbucket is needed, define a new field:
    # bitbucket_oauth_token = fields.Char(string="Bitbucket OAuth Token", copy=False)

    # Other fields from sh_git.sh_res_partner like 'is_autor', 'is_collaborator'
    # can be set based on your application's logic after Bitbucket signup/linking.