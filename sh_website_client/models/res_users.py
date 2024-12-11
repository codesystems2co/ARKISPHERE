#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, _
from ast import literal_eval
from odoo.addons.auth_signup.models.res_partner import SignupError
import logging
_logger = logging.getLogger(__name__)

class res_users(models.Model):

    _inherit = 'res.users'

    def _create_user_from_template(self, values):
        template_user_id = literal_eval(self.env['ir.config_parameter'].sudo().get_param('base.template_portal_user_id', 'False'))
        template_user = self.browse(template_user_id)
        if not template_user.exists():
            raise ValueError(_('Signup: invalid template user'))

        if not values.get('login'):
            raise ValueError(_('Signup: no login given for new user'))
        if not values.get('partner_id') and not values.get('name'):
            raise ValueError(_('Signup: no name or partner given for new user'))

        # create a copy of the template user (attached to a specific partner_id if given)
        values['active'] = True
        try:
            with self.env.cr.savepoint():
                values['partner_id'] = int(template_user.partner_id.id)
                return template_user.with_context(no_reset_password=True).copy(values)
        except Exception as e:
            # copy may failed if asked login is not available.
            raise SignupError(str(e))