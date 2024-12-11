# -*- coding: utf-8 -*-
{
    'name': "SH Backups",
    'summary': "",
    'description': """Client Kube backups""",
    'author': "",
    'website': "",
    'category': 'Administration',
    'version': '18.0',
    'depends': ['base', 'sh_git', 'so_server','kuber_deployment',],
    'data': [
                'security/ir.model.access.csv',
                'views/sh_backups.xml',
                'crons/backups.xml',
            ],
}