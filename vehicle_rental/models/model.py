# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
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
