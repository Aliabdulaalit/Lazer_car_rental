# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
import logging
import pprint

import requests
import werkzeug
from werkzeug import urls

from odoo import http

from odoo.http import request
from datetime import datetime

_logger = logging.getLogger(__name__)


class EasyPayController(http.Controller):
    _cancel_url = '/payment/easypay/cancel/'
    _return_url = '/payment/easypay/dpn/'

    @http.route('/payment/easypay/cancel', type='http', auth='public', csrf=False, save_session=False)
    def easypay_cancel(self, **post):
        # print("I am HERE :=(")
        """ When the user cancels its EasyPay payment: GET on this route """
        post['id'] = request.session['easypay_values']['order']
        post['reference'] = request.session['easypay_values']['reference']
        post['status'] = 'requires_payment_method'
        # print("H$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$444", post, pprint.pformat(post))
        # print("Session request %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%5", request.session)
        _logger.info('Beginning EasyPay cancel with post data %s', pprint.pformat(post))
        request.env['payment.transaction'].sudo().form_feedback(post, 'easypay')
        return werkzeug.utils.redirect('/payment/process')

    @http.route(['/payment/easypay/dpn'], type='http', auth='public', csrf=False, save_session=False)
    # @http.route(['/payment/easypay/dpn'], type='http', auth='public', csrf=False, website=True, sitemap=False)
    def easypay_success(self, **kwargs):
        # print("YES! I am HERE :=)")
        _logger.info('Beginning EasyPay start with post data %s', pprint.pformat(kwargs))  # debug
        kwargs['order'] = request.session['easypay_values']['order']
        kwargs['reference'] = request.session['easypay_values']['reference']
        kwargs['status'] = 'succeeded'
        request.env['payment.transaction'].sudo().form_feedback(kwargs, 'easypay')
        return werkzeug.utils.redirect('/shop/confirmation')

    @http.route(['/get_easypay_session_data'], type='json', auth="public", methods=['POST'], website=True)
    def get_easypay_session_data(self, **kwargs):
        # print("kwargs", kwargs)
        # print("request", request)
        # print("request.session", request.session)
        acquirer = kwargs.get('acquirer_id')
        acquirer_id = request.env['payment.provider'].browse(int(acquirer))
        values = {'order_id': kwargs.get('order_id'), 'acquirer_id': kwargs.get('acquirer_id')}
        # print("values:EE666666666666666666666666666666666666666666666666666", values)
        acquirer_id.get_easypay_payment_data(values)
        if 'easypay_values' in request.session:
            easypay_data = request.session['easypay_values']
            # print("easypay_data: ", easypay_data)
            return easypay_data
        else:
            return None
