# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.exceptions import UserError
import werkzeug

class SecureAuthSignup(AuthSignupHome):

    def get_client_ip(self):
        """Get the client's IP address from the request"""
        if request.httprequest.environ.get('HTTP_X_FORWARDED_FOR'):
            return request.httprequest.environ['HTTP_X_FORWARDED_FOR'].split(',')[0]
        return request.httprequest.remote_addr

    def _check_blocked_ip(self):
        """Check if the current IP is blocked"""
        ip_address = self.get_client_ip()
        BlockedIP = request.env['sh.blocked.ip'].sudo()
        
        if BlockedIP.is_ip_blocked(ip_address):
            return werkzeug.utils.redirect('/web/login')
        return False

    def _signup_with_values(self, token, values):
        """Override to add IP blocking for suspicious signups"""
        ip_address = self.get_client_ip()
        BlockedIP = request.env['sh.blocked.ip'].sudo()

        # Check if IP is already blocked
        if BlockedIP.is_ip_blocked(ip_address):
            raise UserError(_("Access denied"))

        # Check if the data looks suspicious
        if BlockedIP.is_suspicious_data(values):
            BlockedIP.block_ip(ip_address, values)
            raise UserError(_("Access denied"))

        return super(SecureAuthSignup, self)._signup_with_values(token, values)

    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        """Override to check IP before allowing signup"""
        if self._check_blocked_ip():
            return self._check_blocked_ip()
        return super(SecureAuthSignup, self).web_auth_signup(*args, **kw) 