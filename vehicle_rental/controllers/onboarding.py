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
