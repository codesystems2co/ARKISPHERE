# -*- coding: utf-8 -*-
{
    'name': "SH Website Client",
    'summary': """""",
    'description': """""",
    'author': "Alex Grisales Rivera",
    'website': "",
    'category': 'Administrator',
    'version': '0.1',
    'depends': ['base', 'web', 'website', 'portal', 'so_server', 'kuber_deployment', 'sh_git', 'sh_backup','auth_signup'],
    'data': [
                'views/website_account.xml',
                'views/website_account_details.xml',
                'views/so_server.xml',
                'data/menu.xml',
                'data/page_my_servers.xml',
                'data/page_my_projects.xml',
                'data/page_project_stages.xml',
                'data/page_foreing_projects.xml',                
            ],
    'assets': {
                'web.assets_frontend': [
                                            'sh_website_client/static/src/css/frontend.css',
                                            'sh_website_client/static/src/js/git_auth.js',
                                            'sh_website_client/static/src/js/sh_stages.js',
                                        ],
                },
}