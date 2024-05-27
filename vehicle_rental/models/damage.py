# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _


class Damage(models.Model):
    _name = 'damage'
    _description = __doc__

    description = fields.Char(string="Description")
    damage_amount = fields.Monetary(string="Damage Amount")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', related="company_id.currency_id")
    vehicle_contract_id = fields.Many2one('vehicle.contract')
    damage_date = fields.Date(string="Damage Date")
    move_id = fields.Many2one('account.move', string='Invoice', required=True, readonly=True)
