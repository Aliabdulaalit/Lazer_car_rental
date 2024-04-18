from odoo import fields, models, api, _
import json
from werkzeug import urls
import requests
from odoo.http import request
import logging
from base64 import b64encode
from odoo.exceptions import ValidationError
from datetime import datetime
from urllib.error import HTTPError
# from ..controllers.main import EasyPayController
import dateutil.parser
import pytz
from odoo.addons.eazypay_gateway_17 import const

_logger = logging.getLogger(__name__)


class AcquirerEazypay(models.Model):
    _inherit = 'payment.provider'

    # provider = fields.Selection(
    #     selection_add=[('manual', 'Custom Payment Form'), ('easypay', 'EasyPay')], string='Provider',
    #     default='manual', required=True)
    code = fields.Selection(selection_add=[('eazypay', 'EazyPay')], ondelete={'eazypay': 'set default'})
    eazypay_merchant_id = fields.Char('Merchant ID', required=False)
    eazypay_merchant_name = fields.Char('Merchant Name', required=False)
    eazypay_password = fields.Char('Password', required=False)


    def _get_default_payment_method_codes(self):
        """ Override of `payment` to return the default payment method codes. """
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'easypay':
            return default_codes
        return const.DEFAULT_PAYMENT_METHOD_CODES


# class PaymentTransactionEasyPay(models.Model):
#     _inherit = 'payment.transaction'
#
#     def easypay_s2s_do_transaction(self, **kwargs):
#         self.ensure_one()
#         # print("kwargs easypay-----------", kwargs)
#         return self._easypay_s2s_validate_tree(kwargs)
#
#     @api.model
#     def _easypay_form_get_tx_from_data(self, data):
#         # print("data easypay++++++++++++++++++++++++++++++++++++", data)
#         """ Given a data dict coming from easypay, verify it and find the related
#         transaction record. """
#         reference = data.get('reference')
#         if not reference:
#             easypay_error = data.get('error', {}).get('message', '')
#             _logger.error('easypay: invalid reply received from EasyPay API, looks like '
#                           'the transaction failed. (error: %s)', easypay_error or 'n/a')
#             error_msg = _("We're sorry to report that the transaction has failed.")
#             if easypay_error:
#                 error_msg += " " + (_("EasyPay gave us the following info about the problem: '%s'") %
#                                     easypay_error)
#             error_msg += " " + _("Perhaps the problem can be solved by double-checking your "
#                                  "credit card details, or contacting your bank?")
#             raise ValidationError(error_msg)
#
#         tx = self.search([('reference', '=', reference)])
#         if not tx:
#             error_msg = (_('easypay: no order found for reference %s') % reference)
#             _logger.error(error_msg)
#             raise ValidationError(error_msg)
#         elif len(tx) > 1:
#             error_msg = (_('easypay: %s orders found for reference %s') % (len(tx), reference))
#             _logger.error(error_msg)
#             raise ValidationError(error_msg)
#         # print("WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWw", tx, tx.state)
#         courses = []
#         tx_id = tx
#         if tx_id and tx_id.state == 'done':
#             sale_order_ids = tx_id.sale_order_ids
#             for line in sale_order_ids.sudo().mapped('order_line'):
#                 course_id = request.env['slide.channel'].sudo().search([('product_id', '=', line.product_id.id)])
#                 if course_id and course_id.is_approve:
#                     courses.append(course_id.id)
#             tx_user_id = request.env['res.users'].search([('partner_id', '=', tx_id.partner_id.id)])
#             if courses:
#                 for course in set(courses):
#                     user_approval_id = request.env['user.approval'].sudo().search([('user_id', '=', tx_user_id.id),
#                                                                                    ('user_channel_id', '=', course),
#                                                                                    (
#                                                                                        'create_date', '=',
#                                                                                        datetime.now())])
#                     if not user_approval_id:
#                         request.env['user.approval'].sudo().create(
#                             {'user_id': tx_user_id.id, 'user_channel_id': course, 'create_date': datetime.now()})
#         return tx[0]
#
#     def _easypay_s2s_validate_tree(self, tree):
#         # print("calllllllllllllllllllllddddddddddddddddddddddddddddddddddddddddddd*************",tree)
#         self.ensure_one()
#         if self.state not in ("draft", "pending"):
#             _logger.info('easypay: trying to validate an already validated tx (ref %s)', self.reference)
#             return True
#         # if tree.get('status') == 'succeeded':
#         status = tree.get('status')
#         tx_id = tree.get('id')
#         # print("transacrion id:77777777777777777777777777777777777777", tx_id)
#
#         # tx_secret = tree.get("client_secret")
#         res = {
#             "date": fields.datetime.now(),
#             "acquirer_reference": tx_id,
#         }
#         if status == 'succeeded':
#             _logger.info('Validated easypay payment for tx %s: set as done' % (
#                 self.reference))
#             try:
#                 order = request.session['sale_order_id']
#                 order = self.env['sale.order'].browse(order)
#                 order.action_confirm()
#                 move = order._create_invoices()
#                 if move:
#                     move.action_post()
#                 # dateutil and pytz don't recognize abbreviations PDT/PST
#                 tzinfos = {
#                     'PST': -8 * 3600,
#                     'PDT': -7 * 3600,
#                 }
#                 # print(tree)
#                 # date = dateutil.parser.parse(data.get('payment_date'),tzinfos=tzinfos).astimezone(pytz.utc)
#                 date = dateutil.parser.parse(tree.get('payment_date'), tzinfos=tzinfos).astimezone(pytz.utc)
#             except:
#                 date = fields.Datetime.now()
#             res.update(date=date)
#             self._set_transaction_done()
#             return self.write(res)
#         if status in ('processing', 'requires_action'):
#             # self.write(vals)
#             self.write(tree)
#             self._set_transaction_pending()
#             return True
#         if status == 'requires_payment_method':
#             self._set_transaction_cancel()
#             return False
#         else:
#             error = tree.get("failure_message") or tree.get('error', {}).get('message')
#             self._set_transaction_error(error)
#             return False
#
#     def _easypay_form_validate(self, data):
#         # print("easypay form validate:::::::::::;:::::::::::::::::::::::::::::::")
#         return self._easypay_s2s_validate_tree(data)
