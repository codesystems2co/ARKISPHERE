# -*- coding: utf-8 -*-
{
    'name': 'Contact Security',
    'version': '18.0.1.0.0',
    'category': 'Security',
    'summary': 'Block suspicious contact creation attempts',
    'description': """
        This module adds security features to prevent automated contact creation:
        * IP-based blocking
        * Suspicious pattern detection
        * Automated blocking rules
    """,
    'author': 'Alex Grisales Rivera',
    'website': '',
    'depends': [
        'base',
        'contacts',
        'web',
        'auth_signup',
        'mail',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/blocked_ip_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
} 