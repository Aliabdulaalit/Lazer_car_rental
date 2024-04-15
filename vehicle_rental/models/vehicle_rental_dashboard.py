# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _


class VehicleRentalDashboard(models.Model):
    """Vehicle Rental Dashboard"""
    _name = "vehicle.rental.dashboard"
    _description = __doc__

    @api.model
    def get_vehicle_rental_dashboard(self):
        total_vehicle = self.env['fleet.vehicle'].sudo().search_count([])
        available_vehicle = self.env['fleet.vehicle'].sudo().search_count([('status', '=', 'available')])
        under_maintenance_vehicle = self.env['fleet.vehicle'].sudo().search_count([('status', '=', 'in_maintenance')])
        draft_vehicle = self.env['vehicle.contract'].sudo().search_count([])
        in_progress_vehicle = self.env['vehicle.contract'].sudo().search_count([('status', '=', 'b_in_progress')])
        return_contract = self.env['vehicle.contract'].sudo().search_count([('status', '=', 'c_return')])
        cancel_contract = self.env['vehicle.contract'].sudo().search_count([('status', '=', 'd_cancel')])
        customers = self.env['res.partner'].sudo().search_count([])

        customer_invoice = self.env['account.move'].sudo().search_count(
            [('vehicle_contract_id', '!=', False), ('move_type', '=', 'out_invoice')])
        pending_invoices = self.env['account.move'].sudo().search_count(
            [('vehicle_contract_id', '!=', False), ('payment_state', '!=', 'paid'),
             ('move_type', '=', 'out_invoice')])
        data = {
            'total_vehicle': total_vehicle,
            'available_vehicle': available_vehicle,
            'under_maintenance_vehicle': under_maintenance_vehicle,
            'draft_vehicle': draft_vehicle,
            'in_progress_vehicle': in_progress_vehicle,
            'return_contract': return_contract,
            'cancel_contract': cancel_contract,
            'customers': customers,
            'customer_invoice': customer_invoice,
            'pending_invoices': pending_invoices,
            'rent_duration': self.get_rent_contract(),
            'rent_invoice_month': self.get_rent_invoice_month(),

        }
        return data

    def get_rent_contract(self):
        contract_data = []
        vehicle_contracts = self.env['vehicle.contract'].search([('status', '=', 'c_return')])
        for contract in vehicle_contracts:
            contract_data.append({
                'name': contract.reference_no,
                'start_date': str(contract.start_date),
                'end_date': str(contract.end_date),
            })
        return contract_data

    def get_rent_invoice_month(self):
        year = fields.date.today().year
        data_dict = {'January': 0,
                     'February': 0,
                     'March': 0,
                     'April': 0,
                     'May': 0,
                     'June': 0,
                     'July': 0,
                     'August': 0,
                     'September': 0,
                     'October': 0,
                     'November': 0,
                     'December': 0,
                     }

        invoice_id = self.env['account.move'].search(
            [('vehicle_contract_id', '!=', False), ('move_type', '=', 'out_invoice')])
        for data in invoice_id:
            if data.invoice_date and data.invoice_date.year == year:
                if data.vehicle_contract_id.status == 'c_return':
                    data_dict[data.invoice_date.strftime("%B")] = data_dict[data.invoice_date.strftime(
                        "%B")] + data.amount_total
        return [list(data_dict.keys()), list(data_dict.values())]
