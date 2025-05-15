# -*- coding: utf-8 -*-
import odoo
from odoo import http, _
from odoo.http import request
from odoo.exceptions import UserError, AccessDenied

import secrets
from urllib.parse import quote # url_join is not here
from werkzeug.urls import url_join # Import url_join from werkzeug

# Assuming your BitbucketService is structured to be importable this way
# You might need to adjust this based on your exact project structure and __init__.py files
# For example, if sh_bitbucket is an addon in addons_path:
# from odoo.addons.sh_bitbucket.bitbucket.service import BitbucketService
# For now, let's assume it's directly importable as if it were in python path
# This path needs to be correct for Odoo to find your service classes.
# Consider placing BitbucketService in a standard 'models' or 'lib' directory within your addon.

# Placeholder for actual import - this needs to be correct in your Odoo environment
try:
    from bitbucket.service import BitbucketService, BitbucketAccount
except ImportError:
    # Fallback or raise an error if the import path is not standard for Odoo addons
    # This is a common way to structure imports in Odoo
    # If your 'bitbucket' folder is directly under 'sh_bitbucket', the above should work if 
    # sh_bitbucket/bitbucket/__init__.py and sh_bitbucket/bitbucket/bitbucket/__init__.py exist and are correct.
    BitbucketService = None # Define a fallback to avoid NameError during initial load
    BitbucketAccount = None # Added BitbucketAccount
    # In a real scenario, you'd want to ensure this import works or log an error.
    pass 

import logging
_logger = logging.getLogger(__name__)

# --- Bitbucket OAuth App Credentials --- 
# IMPORTANT: These should NOT be hardcoded in production.
# Store them in Odoo System Parameters or a configuration file.
BITBUCKET_CLIENT_ID = "YVW7qCHyF5YhERyfdh" # From your run.py
BITBUCKET_CLIENT_SECRET = "ynJp4KVEBMPyuPk5rHrpZqJFs7H9EHZd" # From your run.py

class BitbucketSignupController(http.Controller):

    def _get_bitbucket_redirect_uri(self):
        """Constructs the Bitbucket OAuth redirect URI for the callback."""
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return url_join(base_url, '/bitbucket/signup/callback')

    @http.route('/bitbucket/signup/initiate', type='http', auth='public', website=True, csrf=False, methods=['POST'])
    def bitbucket_signup_initiate(self, **kw):
        """
        Initiates the Bitbucket OAuth2 flow for signup.
        Expects 'password' (for Odoo account) and 'confirm_password' in kw.
        The Odoo 'name' and 'login' (email) should also be present from the standard signup form.
        """
        if not BitbucketService:
            _logger.error("BitbucketService not imported correctly. Bitbucket signup disabled.")
            raise UserError(_("Bitbucket signup is currently unavailable. Please contact support."))

        odoo_password = kw.get('password')
        odoo_confirm_password = kw.get('confirm_password')
        odoo_name = kw.get('name')
        odoo_login = kw.get('login') # This is typically the email

        if not odoo_password or not odoo_confirm_password:
            # This basic validation should ideally happen client-side too
            return request.render('auth_signup.signup', {
                'error': _('Password and confirmation are required.'), 
                **kw # Pass back other form values
            })
        if odoo_password != odoo_confirm_password:
            return request.render('auth_signup.signup', {
                'error': _('Passwords do not match.'),
                **kw
            })
        if not odoo_login:
             return request.render('auth_signup.signup', {
                'error': _('Email is required for signup.'),
                **kw
            })
        if not odoo_name:
             return request.render('auth_signup.signup', {
                'error': _('Name is required for signup.'),
                **kw
            })

        # Store Odoo user details in session for use after Bitbucket callback
        request.session['bitbucket_signup_odoo_password'] = odoo_password
        request.session['bitbucket_signup_odoo_name'] = odoo_name
        request.session['bitbucket_signup_odoo_login'] = odoo_login 
        # You might want to store other fields like company name, etc., if relevant

        # Initialize the Bitbucket service
        # In a real app, CLIENT_ID and CLIENT_SECRET should come from config
        service = BitbucketService(BITBUCKET_CLIENT_ID, BITBUCKET_CLIENT_SECRET)
        
        # Generate a secure state token to prevent CSRF and store it in session
        state = secrets.token_urlsafe(32)
        request.session['bitbucket_oauth_state'] = state
        
        redirect_uri = self._get_bitbucket_redirect_uri()

        # Scopes needed for signup (similar to run.py but ensure they are sufficient)
        # 'account' for basic profile, 'email' for email addresses.
        scopes = "account email repository pullrequest:write webhook" # Adjusted scopes based on run.py for consistency
        
        auth_url = (
            f"{service.oauth_base_url}/authorize?"
            f"client_id={service.client_id}&"
            f"response_type=code&"
            f"state={state}&"
            f"scope={quote(scopes)}&"
            f"redirect_uri={quote(redirect_uri)}"
        )
        
        _logger.info(f"Redirecting to Bitbucket for OAuth: {auth_url}")
        return request.redirect(auth_url)

    @http.route('/bitbucket/signup/callback', type='http', auth='public', website=True, csrf=False, methods=['GET'])
    def bitbucket_signup_callback(self, **kw):
        """
        Callback URL for Bitbucket OAuth2.
        Handles the authorization code, exchanges it for a token, fetches user info,
        and then creates or logs in the user in Odoo.
        """
        if not BitbucketService:
            _logger.error("BitbucketService not imported correctly. Bitbucket signup disabled.")
            # Proper error handling for the user
            return request.render('sh_website_client.oauth_error_page', # You'd need to create this template
                                {'error_message': _("Bitbucket signup is currently unavailable due to a configuration issue.")})

        auth_code = kw.get('code')
        returned_state = kw.get('state')
        original_state = request.session.pop('bitbucket_oauth_state', None)

        if not auth_code:
            error_description = kw.get('error_description', _("Authorization failed on Bitbucket."))
            _logger.warning(f"Bitbucket OAuth callback error: {kw.get('error')}, desc: {error_description}")
            return request.render('sh_website_client.oauth_error_page', {'error_message': error_description})

        if not original_state or original_state != returned_state:
            _logger.warning("Bitbucket OAuth CSRF detected: state mismatch.")
            return request.render('sh_website_client.oauth_error_page', {'error_message': _("Invalid security token. Please try signing up again.")})

        # Retrieve Odoo user details from session
        odoo_password = request.session.pop('bitbucket_signup_odoo_password', None)
        odoo_name = request.session.pop('bitbucket_signup_odoo_name', None)
        odoo_login = request.session.pop('bitbucket_signup_odoo_login', None)

        if not odoo_password or not odoo_login or not odoo_name:
            _logger.error("Odoo signup details not found in session after Bitbucket callback.")
            return request.render('sh_website_client.oauth_error_page', {'error_message': _("Your session has expired or is invalid. Please try signing up again.")})

        service = BitbucketService(BITBUCKET_CLIENT_ID, BITBUCKET_CLIENT_SECRET)
        redirect_uri = self._get_bitbucket_redirect_uri()

        try:
            _logger.info("Exchanging Bitbucket auth code for access token...")
            token_info = service.get_access_token(auth_code, redirect_uri)
            access_token = token_info['access_token']
            _logger.info("Bitbucket access token obtained successfully.")

            # --- Fetch Bitbucket User Details Dynamically ---
            _logger.info("Fetching Bitbucket user information dynamically...")
            if not BitbucketAccount:
                _logger.error("BitbucketAccount class not imported correctly. Cannot fetch user details.")
                raise UserError(_("Bitbucket signup configuration error. Please contact support."))
            
            account = BitbucketAccount(access_token, service) # Instantiate BitbucketAccount
            
            # Fetch user info (e.g., /2.0/user)
            bb_user_details = account.user_info # This uses the @property
            if not bb_user_details:
                _logger.error("Failed to fetch Bitbucket user details.")
                raise UserError(_("Could not retrieve your Bitbucket profile information."))
            
            # Fetch user emails (e.g., /2.0/user/emails)
            bb_user_emails_list = account.get_user_emails()
            # Extract primary email
            bb_primary_email = None
            if bb_user_emails_list:
                for email_info in bb_user_emails_list:
                    if email_info.get('is_primary') and email_info.get('is_confirmed'):
                        bb_primary_email = email_info.get('email')
                        break
                if not bb_primary_email: # Fallback to first confirmed email if no primary explicitly marked
                    for email_info in bb_user_emails_list:
                        if email_info.get('is_confirmed'):
                            bb_primary_email = email_info.get('email')
                            break
            
            if not bb_primary_email:
                _logger.warning("No primary or confirmed email found for Bitbucket user.")
                # Decide handling: error out, or proceed if odoo_login is sufficient and policy allows
                # For now, we will rely on the odoo_login (email from form) for the Odoo account.

            bb_username = bb_user_details.get('username')
            bb_display_name = bb_user_details.get('display_name', odoo_name) # Fallback to name from form
            bb_uuid = bb_user_details.get('uuid')
            # Ensure html_url is safely accessed
            bb_html_url = bb_user_details.get('links', {}).get('html', {}).get('href')
            bb_account_id = bb_user_details.get('account_id') # From your run.py output structure

            _logger.info(f"Dynamically fetched Bitbucket Username: {bb_username}")
            _logger.info(f"Dynamically fetched Bitbucket Display Name: {bb_display_name}")
            _logger.info(f"Dynamically fetched Bitbucket UUID: {bb_uuid}")
            _logger.info(f"Dynamically fetched Bitbucket Primary Email: {bb_primary_email}")
            # --- END DYNAMIC FETCHING ---

            User = request.env['res.users'].sudo()
            Partner = request.env['res.partner'].sudo()

            # 1. Check if this Bitbucket account is already linked to an Odoo user
            existing_linked_user = User.search([
                ('oauth_provider_id', '=', 'bitbucket'),
                ('oauth_uid', '=', bb_uuid)
            ], limit=1)

            if existing_linked_user:
                _logger.info(f"Bitbucket account {bb_uuid} already linked to Odoo user {existing_linked_user.login}. Updating and logging in.")
                # Prepare partner update values, ensuring not to nullify email/name if bb_display_name is empty
                partner_update_vals = {
                    'name': bb_display_name or existing_linked_user.partner_id.name,
                    'platform': 'bitbucket',
                    'username': bb_username,
                    'identifier': bb_uuid,
                    'html_url': bb_html_url,
                    'bitbucket_account_id': bb_account_id,
                }
                existing_linked_user.partner_id.write(partner_update_vals)
                existing_linked_user.write({'oauth_access_token': access_token}) # Update token
                request.session.login = existing_linked_user.login
                return request.redirect('/')

            # 2. If not linked, proceed with signup logic using odoo_login as the primary login.
            # This will attempt to create a new user. 
            # Odoo's res.users.signup will raise UserError if login (email) already exists.

            # Values for res.users.signup() method.
            # This method creates both res.users and res.partner.
            # login, name, password are used for res.users.
            # Other keys are passed to res.partner.create().
            signup_values = {
                'login': odoo_login,                    # For res.users.login and res.partner.email
                'password': odoo_password,
                'name': bb_display_name or odoo_name,  # For res.users.name and res.partner.name
                # Custom fields for res.partner, aligning with sh_git fields:
                'platform': 'bitbucket',
                'username': bb_username,               # Partner's Bitbucket username
                'identifier': bb_uuid,               # Partner's Bitbucket UUID
                'html_url': bb_html_url,               # Partner's Bitbucket profile URL
                'bitbucket_account_id': bb_account_id, # Partner's specific Bitbucket account ID
                # 'is_autor': True, # Default for new signups, if applicable
            }
            
            try:
                # Use Odoo's standard signup method for creating user and partner.
                # This handles unique login checks and default group assignments (e.g., portal user).
                # The token parameter is for email validation tokens, not OAuth tokens.
                request.env['res.users'].sudo().signup(signup_values, token=None)
                request.env.cr.commit() # Commit after user creation
                
                # Retrieve the newly created user
                user = User.search([('login', '=', odoo_login)], limit=1)
                if not user:
                    _logger.error(f"User {odoo_login} not found after supposed successful signup via Bitbucket.")
                    raise UserError(_("User creation succeeded but failed to retrieve the new user account."))

                # Update the new user with OAuth specific fields that signup() might not handle directly.
                user.write({
                    'oauth_provider_id': 'bitbucket',
                    'oauth_uid': bb_uuid, # This might already be set if 'identifier' on partner auto-links
                    'oauth_access_token': access_token,
                })
                
                _logger.info(f"New user {user.login} (ID: {user.id}) created and linked with Bitbucket UUID {bb_uuid}.")
                request.session.login = user.login
                return request.redirect('/')

            except UserError as e:
                # This typically catches "Login already exists" or other validation errors from signup()
                _logger.warning(f"Odoo signup via Bitbucket failed for {odoo_login}: {e}")
                # Provide the error to the signup page
                qcontext_error = {
                    'error': str(e),
                    'login': odoo_login, 
                    'name': odoo_name 
                    # Pass back other form values if necessary for pre-filling the form
                }
                # Add original form values back to qcontext if they were passed in kw to initiate
                # This depends on what `auth_signup.signup` template expects.
                return request.render('auth_signup.signup', qcontext_error)
            except Exception as e:
                _logger.exception(f"Unexpected error during Odoo user signup via Bitbucket for {odoo_login}:")
                return request.render('sh_website_client.oauth_error_page', {'error_message': _("An unexpected error occurred while creating your account.")})

        except UserError as e: # Catches UserErrors from token exchange or Bitbucket user info fetching
            _logger.error(f"Bitbucket signup UserError: {e}")
            return request.render('auth_signup.signup', {'error': str(e), **kw})
        except AccessDenied as e:
            _logger.error(f"Bitbucket signup AccessDenied: {e}")
            return request.render('sh_website_client.oauth_error_page', {'error_message': _("Access was denied.")})
        except Exception as e:
            _logger.exception("Bitbucket OAuth callback failed unexpectedly.")
            # Generic error for the user
            return request.render('sh_website_client.oauth_error_page', {'error_message': _("An unexpected error occurred during Bitbucket signup. Please try again later.")})