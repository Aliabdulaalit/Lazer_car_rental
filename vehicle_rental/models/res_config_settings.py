# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    fleet_vehicle_expiration_notification_user = fields.Many2one(
        related='company_id.fleet_vehicle_expiration_notification_user', readonly=False
    )
    fleet_vehicle_expiration_notification_days = fields.Integer(
        related='company_id.fleet_vehicle_expiration_notification_days', readonly=False
    )
