# -*- coding: utf-8 -*-

from odoo import http
from odoo import fields
from odoo.http import request
import logging
import json
_logger = logging.getLogger(__name__)

from odoo.addons.website_sale.controllers.variant import WebsiteSaleVariantController
from odoo.addons.website_sale.controllers.main import WebsiteSale


class sh_subscription(http.Controller):

    @http.route('/sh_subscription/ssh_test_connection/', methods=['POST'], type='json')
    def ssh_test_connection(self, **kw):
        message = "Can't connect to server with details provided. \n"
        has_error = False
        response = { "has_error":has_error,"message":message }
        ssh = kw.get('ssh')
        ssh_parts = str(ssh).split(",")        
        
        try:
            user = ssh_parts[0]
        except:
            message = message + "User not provided. \n"
            has_error = True
        try:
            password = ssh_parts[1]
        except:
            message = message + "Password not provided. \n"
            has_error = True
        try:
            host = ssh_parts[2]
        except:
            message = message + "Host not provided. \n"
            has_error = True
        try:
            port = ssh_parts[3]
        except:
            message = message + "Port not provided. \n"
            has_error = True

        if(not has_error):
            response ["message"] = "Connection successfully."
            response ["has_error"] = False
        else:
            response ["message"] = message + str("Remember ssh details order: (root,pass,host,port)")
            response ["has_error"] = True

        return response
        



class WebsiteSaleStockVariantController(WebsiteSaleVariantController):
    @http.route()
    def get_combination_info_website(self, product_template_id, product_id, combination, add_qty, **kw):
        response =  super(WebsiteSaleStockVariantController, self).get_combination_info_website(product_template_id, product_id, combination, add_qty, **kw)   

        _logger.warning('combination >>')
        _logger.warning(combination)    

        # manual programming system ::: combination: follow code work in order for attributes values; if subscription peridon is first. So, must be [0] in vector ...  

        #try:
        if(len(combination)>0):
            query = "select sh_is_subscription, sh_multiplier_factor from product_template_attribute_value where id = "+str(combination[1])
            request.cr.execute(query)
            product_template_attribute_value = request.cr.dictfetchone()

            _logger.warning('product_template_attribute_value >>')
            _logger.warning(product_template_attribute_value)     

            if('sh_is_subscription' in product_template_attribute_value):
                if(bool(product_template_attribute_value['sh_is_subscription'])):
                    response['price'] = ((float(response['price']) * float(product_template_attribute_value['sh_multiplier_factor'])) * float(add_qty))
                    response['list_price'] = ((float(response['list_price']) * float(product_template_attribute_value['sh_multiplier_factor'])) * float(add_qty))
        #except:
        #    pass                    
        return response