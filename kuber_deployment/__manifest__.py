#-*- coding: utf-8 -*-

{
	"name": "Kuber deployment",
	"version": "1.0", 
	"depends": [
		'base', 'sh_git', 'sh_physical_server', 'so_server', 'product'
	],
	"author": "Alex Grisales Rivera",
	"category": "Utility",
	"website": "",
	
	"price": "10",
	"license": "OPL-1",
	"currency": "USD",
	"summary": "",
	"description": """""",
	"data": [
				"security/ir.model.access.csv",	
				# Menu
				"view/menu.xml",			
				# View
				
				"view/kuber_template.xml",
				"view/kuber_deploy.xml",
				"view/kuber_exposer.xml",
				"view/sh_git_repository.xml",				
				"view/sh_git_branch.xml",
				"view/kuber_commands.xml",
				"view/kuber_domains.xml",
				"view/kuber_domains_ssl.xml",
				"view/product_template.xml",
				"view/kuber_docker_image.xml",                
                # Crons
                "crons/commands.xml",
			],
	"installable": True,
	"auto_install": False,
	"application": True,
}