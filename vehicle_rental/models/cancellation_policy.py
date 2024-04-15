# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _


class CancellationPolicy(models.Model):
    """Cancellation Policy"""
    _name = 'cancellation.policy'
    _description = __doc__
    _rec_name = 'title'

    title = fields.Char(string="Title", required=True)
    created_on = fields.Date(string="Created On")
    terms_and_conditions = fields.Text(string="Terms and Conditions")