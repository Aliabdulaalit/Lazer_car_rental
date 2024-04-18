# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class easypay_gateway_17(models.Model):
#     _name = 'easypay_gateway_17.easypay_gateway_17'
#     _description = 'easypay_gateway_17.easypay_gateway_17'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

