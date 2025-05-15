# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.http import request
import re

class BlockedIP(models.Model):
    _name = 'sh.blocked.ip'
    _description = 'Blocked IP Addresses'
    _order = 'create_date desc'

    name = fields.Char(string='IP Address', required=True, index=True)
    reason = fields.Text(string='Blocking Reason')
    blocked_date = fields.Datetime(string='Blocked Date', default=fields.Datetime.now)
    attempt_count = fields.Integer(string='Attempt Count', default=1)
    last_attempt = fields.Datetime(string='Last Attempt', default=fields.Datetime.now)
    suspicious_data = fields.Text(string='Suspicious Data')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('unique_ip', 'unique(name)', 'This IP is already blocked!')
    ]

    def _is_suspicious_email(self, email):
        """Check if email looks suspicious"""
        if not email:
            return False

        suspicious_patterns = [
            r'\d{2,}@',  # Multiple numbers in local part
            r'vq\d{2,}',  # Common spam pattern 'vq' followed by numbers
            r'(miller|dave|smith|john)\d{2,}',  # Common names with numbers
            r'[a-z]{2,}[A-Z]{2,}',  # Mixed case patterns
            r'[A-Z]{2,}[a-z]{2,}',  # Mixed case patterns
            r'\d+.*\d+@',  # Multiple number groups
        ]
        
        return any(re.search(pattern, email.lower()) for pattern in suspicious_patterns)

    def _is_suspicious_name(self, name):
        """Check if name looks suspicious"""
        if not name:
            return False

        suspicious_patterns = [
            r'[A-Z][a-z]+[A-Z][a-z]+',  # CamelCase without spaces
            r'[a-zA-Z]{3,}[0-9]{2,}',    # Letters followed by numbers
            r'[0-9]{2,}[a-zA-Z]{3,}',    # Numbers followed by letters
            r'^[^a-zA-Z\s]',             # Doesn't start with letter or space
            r'[^a-zA-Z0-9\s\'-]',        # Contains special characters except hyphen and apostrophe
            r'([a-zA-Z])\1{2,}',         # Repeated characters
            r'[A-Z]{3,}',                # Multiple uppercase letters in sequence
            r'[a-z]{8,}',                # Very long lowercase sequence
            r'[A-Za-z]{2,}[0-9]{2,}[A-Za-z]{2,}',  # Letters-numbers-letters pattern
        ]
        
        return any(re.search(pattern, str(name)) for pattern in suspicious_patterns)

    @api.model
    def is_suspicious_data(self, data):
        """Check if the contact data looks suspicious"""
        if not data:
            return False

        # If it's a legitimate platform signup, allow it
        if data.get('platform') in ['github'] and all([
            data.get('identifier'),
            data.get('access_token'),
            data.get('html_url'),
            data.get('username'),
            data.get('name')
        ]):
            return False

        # Check for missing essential data
        if not data.get('name') or not data.get('login'):
            return True

        # Check for suspicious patterns
        checks = [
            # Email checks
            lambda d: self._is_suspicious_email(d.get('login')),
            
            # Name checks
            lambda d: self._is_suspicious_name(d.get('name')),
            
            # Missing data patterns
            lambda d: not d.get('platform') and all([
                not d.get('country_id') or d.get('country_id') == 0,
                not d.get('city'),
                not d.get('zip')
            ]),

            # Suspicious combinations
            lambda d: len(str(d.get('name', ''))) >= 10 and str(d.get('name', '')).count(str(d.get('login', '')).split('@')[0]) > 0,
            
            # Known spam patterns
            lambda d: 'captaindave' in str(d.get('login', '')).lower(),
            lambda d: 'miller' in str(d.get('login', '')).lower() and any(x in str(d.get('login', '')).lower() for x in ['vq', 'qq', 'zz']),
            lambda d: bool(re.match(r'^[A-Z][a-z]+[A-Z][a-z]+\d+', str(d.get('name', '')))),
            
            # Password complexity vs username simplicity check
            lambda d: d.get('password') and d.get('name') and (
                len(d.get('password')) > 12 and  # Complex password
                len(d.get('name')) < 8 and       # But simple name
                any(c.isupper() for c in d.get('password')) and
                any(c.islower() for c in d.get('password')) and
                any(c.isdigit() for c in d.get('password'))
            )
        ]

        return any(check(data) for check in checks)

    @api.model
    def block_ip(self, ip_address, data=None):
        """Block an IP address with the related suspicious data"""
        existing = self.search([('name', '=', ip_address)], limit=1)
        
        if existing:
            existing.write({
                'attempt_count': existing.attempt_count + 1,
                'last_attempt': fields.Datetime.now(),
                'suspicious_data': str(data) if data else existing.suspicious_data
            })
        else:
            reason = 'Automated blocking - '
            if data:
                if self._is_suspicious_email(data.get('login')):
                    reason += 'Suspicious email pattern'
                elif self._is_suspicious_name(data.get('name')):
                    reason += 'Suspicious name pattern'
                else:
                    reason += 'Suspicious signup data'
            
            self.create({
                'name': ip_address,
                'reason': reason,
                'suspicious_data': str(data) if data else False
            })

    @api.model
    def is_ip_blocked(self, ip_address):
        """Check if an IP address is blocked"""
        return bool(self.search_count([('name', '=', ip_address), ('active', '=', True)])) 