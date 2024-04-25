# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _


class FleetVehicle(models.Model):
    """Fleet Vehicle"""
    _inherit = 'fleet.vehicle'
    _description = __doc__

    rent_day = fields.Monetary(string="Rent / Day")
    rent_week = fields.Monetary(string="Rent / Week")
    rent_month = fields.Monetary(string="Rent / Month")
    rent_km = fields.Monetary(string="Rent / Kilometer")
    rent_mi = fields.Monetary(string="Rent / Mile")

    rent_hour = fields.Monetary(string="Rent / Hour")
    rent_year = fields.Monetary(string="Rent / Year")

    extra_charge_day = fields.Monetary(string="Charge / Day")
    extra_charge_week = fields.Monetary(string="Charge / Week")
    extra_charge_month = fields.Monetary(string="Charge / Month")
    extra_charge_km = fields.Monetary(string="Charge / Kilometer")
    extra_charge_mi = fields.Monetary(string="Charge / Mile")

    extra_charge_hour = fields.Monetary(string="Charge / Hour")
    extra_charge_year = fields.Monetary(string="Charge / Year")

    status = fields.Selection([('available', 'Available'), ('in_maintenance', 'Under Maintenance')],
                              string="Status", default="available")
    user_id = fields.Many2one('res.users', required=True,
                              domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    insurance_expiration_date = fields.Date(tracking=True)
    insurance_cron = fields.Many2one('ir.cron', readonly=True)

    registration_expiration_date = fields.Date(tracking=True)
    registration_cron = fields.Many2one('ir.cron', readonly=True)
    analytic_tag_ids = fields.Many2many('account.analytic.account', string='Analytic Tags')

    @api.model
    def create(self, vals):
        vals['analytic_tag_ids'] = [
            (0, 0, {'name': vals['license_plate'], 'plan_id': self.env.ref('vehicle_rental.analytic_plan_rent').id})]
        result = super(FleetVehicle, self).create(vals)
        return result

    # def set_insurance_cron(self):
    #     for rec in self:
    #         if rec.insurance_cron:
    #             rec.insurance_cron.unlink()
    #
    #         if rec.insurance_expiration_date and rec.user_id:
    #             rec.insurance_cron = self.env['ir.cron'].sudo().create({
    #                 'name': f'Vehicle: {rec.name} insurance expiration',
    #                 'model_id': self.env['ir.model'].sudo().search([('model', '=', 'fleet.vehicle')], limit=1).id,
    #                 'state': 'code',
    #                 'code': f"""
    # vehicle_id = env['fleet.vehicle'].sudo().browse({rec.id})
    # vehicle_id.write({{'activity_ids': [(0, 0, {{
    #     'res_model_id': env['ir.model'].sudo().search([('model', '=', 'fleet.vehicle')], limit=1).id,
    #     'activity_type_id': env.ref('note.mail_activity_data_reminder').id,
    #     'date_deadline': vehicle_id.insurance_expiration_date,
    #     'summary': vehicle_id.name + ' insurance is about to expire',
    #     'user_id': vehicle_id.user_id.id
    # }})]}})
    #                     """,
    #                 'nextcall': datetime(
    #                     rec.insurance_expiration_date.year,
    #                     rec.insurance_expiration_date.month,
    #                     rec.insurance_expiration_date.day,
    #                     0,
    #                     0,
    #                     0
    #                 ) - relativedelta(days=self.env.company.fleet_vehicle_expiration_notification_days),
    #                 'numbercall': 1,
    #                 'active': True,
    #             })

    # def set_registration_cron(self):
    #     for rec in self:
    #         if rec.registration_cron:
    #             rec.registration_cron.unlink()
    #
    #         if rec.registration_expiration_date and rec.user_id:
    #             rec.registration_cron = self.env['ir.cron'].sudo().create({
    #                 'name': f'Vehicle: {rec.name} registration expiration',
    #                 'model_id': self.env['ir.model'].sudo().search([('model', '=', 'fleet.vehicle')], limit=1).id,
    #                 'state': 'code',
    #                 'code': f"""
    # vehicle_id = env['fleet.vehicle'].sudo().browse({rec.id})
    # vehicle_id.write({{'activity_ids': [(0, 0, {{
    #     'res_model_id': env['ir.model'].sudo().search([('model', '=', 'fleet.vehicle')], limit=1).id,
    #     'activity_type_id': env.ref('note.mail_activity_data_reminder').id,
    #     'date_deadline': vehicle_id.registration_expiration_date,
    #     'summary': vehicle_id.name + ' registration is about to expire',
    #     'user_id': vehicle_id.user_id.id
    # }})]}})
    #                     """,
    #                 'nextcall': datetime(
    #                     rec.registration_expiration_date.year,
    #                     rec.registration_expiration_date.month,
    #                     rec.registration_expiration_date.day,
    #                     0,
    #                     0,
    #                     0
    #                 ) - relativedelta(days=self.env.company.fleet_vehicle_expiration_notification_days),
    #                 'numbercall': 1,
    #                 'active': True,
    #             })

    # @api.model_create_multi
    # def create(self, vals_list):
    #     res = super(FleetVehicle, self).create(vals_list)
    #     res.set_insurance_cron()
    #     res.set_registration_cron()
    #     res.set_third_party_cron()
    #     return res

    # def write(self, vals):
    #     res = super(FleetVehicle, self).write(vals)
    #     if 'user_id' in vals or 'insurance_expiration_date' in vals:
    #         self.set_insurance_cron()
    #     if 'user_id' in vals or 'registration_expiration_date' in vals:
    #         self.set_registration_cron()
    #     if 'user_id' in vals or 'third_party_expiration_date' in vals:
    #         self.set_third_party_cron()
    #     return res

    def available_to_in_maintenance(self):
        self.status = 'in_maintenance'

    def in_maintenance_to_available(self):
        self.status = 'available'


class FleetVehicleLogContract(models.Model):
    """Fleet Vehicle Log Contract"""
    _inherit = 'fleet.vehicle.log.contract'
    _description = __doc__

    license_plate = fields.Char(string="License Plate")


class RentalInvoice(models.Model):
    """Rental Invoice"""
    _inherit = 'account.move'
    _description = __doc__

    vehicle_contract_id = fields.Many2one('vehicle.contract', string="Vehicle Contract")


class RentalDeposit(models.Model):
    """Rental Deposit"""
    _inherit = 'account.payment'
    _description = __doc__

    vehicle_contract_id = fields.Many2one('vehicle.contract', string="Vehicle Contract")
