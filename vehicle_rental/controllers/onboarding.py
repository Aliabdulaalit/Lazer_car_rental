# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request, content_disposition


class OnboardingController(http.Controller):
    @http.route('/vehicle/contract/export/<string:contract_ids>', type='http', auth='user')
    def vehicles_contracts_export(self, contract_ids):
        response = request.make_response(None, headers=[
            ('Content-Type', 'application/vnd.ms-excel'),
            ('Content-Disposition', content_disposition('Vehicles Contracts.xlsx'))
        ])

        request.env['vehicle.contract'].action_export(
            [int(contract_id) for contract_id in contract_ids.split(',')],
            response
        )

        return response

    @http.route('/contract/rental/deposit/<string:contract_ids>', type='http', auth='user')
    def contracts_rental_deposit(self, contract_ids):
        response = request.make_response(None, headers=[
            ('Content-Type', 'application/vnd.ms-excel'),
            ('Content-Disposition', content_disposition('Rental Deposit.xlsx'))
        ])

        request.env['vehicle.contract'].action_print_rental_deposit(
            [int(contract_id) for contract_id in contract_ids.split(',')],
            response
        )

        return response

    @http.route('/contract/damage/deposit/<string:contract_ids>', type='http', auth='user')
    def contracts_damage_deposit(self, contract_ids):
        response = request.make_response(None, headers=[
            ('Content-Type', 'application/vnd.ms-excel'),
            ('Content-Disposition', content_disposition('Damage Deposit.xlsx'))
        ])

        request.env['vehicle.contract'].action_print_damage_deposit(
            [int(contract_id) for contract_id in contract_ids.split(',')],
            response
        )

        return response
