#-*- coding: utf-8 -*-

{
	"name": "Sh stages for Github",
	"version": "1.0", 
	"depends": [
		'base','sh_git'
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
		"view/sh_stage.xml",
		"view/sh_development.xml",
		"view/sh_production.xml",
		"view/sh_git_commit.xml",
	],
	"installable": True,
	"auto_install": False,
	"application": True,
}