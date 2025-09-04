#-*- coding: utf-8 -*-

{
	"name": "Sh Github",
	"version": "1.0", 
	"depends": [
		'base','contacts','website'
	],
	"author": "Alex Grisales Rivera",
	"category": "Utility",
	"website": "",
	
	"price": "10",
	"license": "OPL-1",
	"currency": "USD",
	"summary": "",
	"description": """

Information
======================================================================

* created menus
* created objects
* created views
* logics

""",
	"data": [
                "security/ir.model.access.csv",
				"view/sh_git_repository.xml",
                "view/sh_git_autor.xml",				
				"view/sh_git_collaborator.xml",
				"view/sh_git_permission.xml",
				"view/sh_git_branch.xml",
				"view/sh_git_commit.xml",
				"view/res_partner_github_org.xml",

				"report/sh_git_autor.xml",
				"report/sh_git_repository.xml",
				"report/sh_git_collaborator.xml",
				"report/sh_git_permission.xml",
				"report/sh_git_branch.xml",
				"report/sh_git_commit.xml",
				
				# Crons
				"crons/github_organizations.xml",
	        ],
	#"external_dependencies":['PyGithub', 'xmlrpclib'],
    'assets': {
    'web.assets_backend': [
        'sh_git/static/src/css/backend.css',
    ],
},
	"installable": True,
	"auto_install": False,
	"application": True,
}