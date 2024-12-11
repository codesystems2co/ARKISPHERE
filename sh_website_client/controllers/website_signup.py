from odoo import http, _
from odoo.http import request
from odoo.exceptions import UserError
from odoo.addons.auth_signup.controllers.main import AuthSignupHome

import sys
import logging
_logger = logging.getLogger(__name__)

class AuthSignupHomeInerith(AuthSignupHome):
    def do_signup(self, qcontext):
        try:
            
            val = { key: qcontext.get(key) for key in ('login', 'name', 'password', 'username', 'vat', 'is_autor', 'is_collaborator', 'platform', 'identifier', '_gpassword', 'html_url', 'access_token') }
            values = { key: qcontext.get(key) for key in ('login', 'name', 'password') }

            contact = request.env['res.partner'].sudo().browse(int(request.env.user.partner_id.id))

            _logger.info(':: Contact...')
            _logger.info(contact)
            _logger.info(':: EOF >>')

            values['username'] = contact.username
            values['vat'] = contact.vat
            values['is_autor'] = contact.is_autor
            values['is_collaborator'] = contact.is_collaborator
            values['platform'] = contact.platform
            values['identifier'] = contact.identifier
            values['_gpassword'] = contact._gpassword
            values['html_url'] = contact.html_url
            values['access_token'] = contact.access_token
            values['country_id'] = int(contact.country_id.id)
            values['city'] = contact.city
            values['zip'] = contact.zip
            
            

            query = "UPDATE res_partner SET name='Public User', country_id=null, city=null, zip=null, email=null, is_autor='False', username=null, is_collaborator='False', platform=null, identifier=null, _gpassword=null, html_url=null, access_token=null WHERE id = "+str(request.env.user.partner_id.id)
            request.cr.execute(query)
            _logger.info(query)

            if not values:
                raise UserError(_("The form was not properly filled in."))
            if values.get('password') != qcontext.get('confirm_password'):
                raise UserError(_("Passwords do not match; please retype them."))
            
            supported_lang_codes = [code for code, _ in request.env['res.lang'].get_installed()]
            lang = request.context.get('lang', '').split('_')[0]

            if lang in supported_lang_codes:
                values['lang'] = lang
            
            _logger.info(':: Sign up minified and full values...')
            _logger.info(values)
            _logger.info(qcontext.get('token'))
            
            _logger.info(':: EOF >>')

            self._signup_with_values(qcontext.get('token'), values)
            request.env.cr.commit()            

        except Exception as e:
            error = getattr(e, 'message', repr(e))
            _logger.info(':: Could not sign up with github values...')
            _logger.warning(error)
            _logger.warning(str('LINE::: ') + str(format(sys.exc_info()[-1].tb_lineno)))