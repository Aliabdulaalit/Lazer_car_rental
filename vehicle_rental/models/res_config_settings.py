# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    fleet_vehicle_expiration_notification_days = fields.Integer(
        related='company_id.fleet_vehicle_expiration_notification_days', readonly=False
    )
