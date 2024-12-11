#-*- coding: utf-8 -*-

{
	"name": "SH Virtual Server",
	"version": "1.0", 
	"depends": [
				'base', 
                'sale', 
                'sh_physical_server', 
                'sh_git',
                'hetzner'
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
		"view/sh_physical_server.xml",
		"view/so_server.xml",
		"view/so_owner.xml",
		"view/sh_git_repository.xml",
        "view/sale_order.xml",
        "view/menu.xml",
        "crons/commands.xml",
	],
	"installable": True,
	"auto_install": False,
	"application": True,
}