#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)

class sh_product_template_attribute_value(models.Model):
    _inherit = 'product.template.attribute.value'

    sh_is_subscription = fields.Boolean("Is Subscription?", default=False)
    sh_multiplier_factor = fields.Integer("Multiplier Factor", default=1)
    sh_capacity_gb = fields.Float("Capacity (GB)", default=0)
    sh_code_identifier = fields.Selection([('PERIOD','Period'),('DISK','SSD'),('RAM','Memory Ram'),('PROCESSOR','Processor'),('WORKERS','Workers'),('CUSTOMISATION','Customisation')], string="Key")

    def create(self, default=None):      
        rec = super(sh_product_template_attribute_value, self).create(default)
        _product_id = int(1)
        if default:
            for record  in default:
                _logger.warning('record <<<<')
                _logger.warning(record)
                
                attribute_value = self.env['product.template.attribute.value'].search_read([('product_tmpl_id','=',_product_id),('product_attribute_value_id','=',record['product_attribute_value_id'])])
                if attribute_value:
                    attribute_value = attribute_value[0]
                    attribute_value_to_update = self.env['product.template.attribute.value'].search_read([('attribute_line_id','=',record['attribute_line_id']),('product_attribute_value_id','=',record['product_attribute_value_id'])])[0]
                    attribute_value_to_update = self.env['product.template.attribute.value'].browse(int(attribute_value_to_update['id']))
                    attribute_value_to_update.write({
                                                        'sh_is_subscription':attribute_value['sh_is_subscription'],
                                                        'sh_multiplier_factor':attribute_value['sh_multiplier_factor'],
                                                        'sh_capacity_gb':attribute_value['sh_capacity_gb'],
                                                        'sh_code_identifier':attribute_value['sh_code_identifier'],
                                                        'price_extra':attribute_value['price_extra'],
                                                    })

        return rec