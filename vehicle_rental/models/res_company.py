# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    fleet_vehicle_expiration_notification_user = fields.Many2one('res.users', 'Send Expiration Notification to')
    fleet_vehicle_expiration_notification_days = fields.Integer(string='Number of Days Before Expiration Notification')

    @api.constrains('fleet_vehicle_expiration_notification_days')
    def _check_days_before_expiration_notification(self):
        for rec in self:
            if rec.fleet_vehicle_expiration_notification_days < 0:
                raise ValidationError(_("Number of days before expiration notification must be positive."))
