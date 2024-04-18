import requests
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.http import request
from werkzeug.exceptions import Forbidden, NotFound
from odoo.exceptions import UserError, ValidationError
# from .BenefitAPI import BenefitAPIPlugin
import logging
import werkzeug
from io import BytesIO
import uuid
import qrcode
import json
from werkzeug import urls
import base64
import pprint
from base64 import b64encode

from werkzeug.urls import url_encode

from urllib import parse

_logger = logging.getLogger(__name__)


class EazypayGateway(WebsiteSale):

    @http.route('/shop/payment/eazypay', type='http', auth="public", website=True, save_session=False)
    def shop_payment_eazypay(self, **kwargs):
        website = http.request.website
        website = website.get_current_website()
        base_url = website.domain or request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        acquirer_id = request.env['payment.provider'].sudo().search([('code', '=', 'eazypay')], limit=1)
        order = request.website.sale_get_order()
        # merchant_name = acquirer_id.x_eazypay_merchant_name
        merchant_id = acquirer_id.eazypay_merchant_id
        password = acquirer_id.eazypay_password
        user = 'merchant.%s' % merchant_id
        api_url = "https://eazypay.gateway.mastercard.com/api/rest/version/78/merchant/%s/session/" % merchant_id
        data = json.dumps({
            "apiOperation": "INITIATE_CHECKOUT",
            "interaction": {
                "operation": "PURCHASE",
                "returnUrl": urls.url_join(base_url, '/payment/eazypay/success?%s' % url_encode(
                    {'order': order.name})),
                "cancelUrl": urls.url_join(base_url, '/shop/cart/'),
                "merchant": {'name': merchant_id},
                "displayControl": {'billingAddress': 'HIDE'},
            },

            "order": {
                "amount": order.amount_total,
                "currency": order.currency_id.name,
                "description": order.name,
                "id": order.id,
            },
        })
        headers = {
            "Authorization": "Basic {}".format(
                b64encode(bytes(f"{user}:{password}", "utf-8")).decode("ascii")
            )
        }
        try:
            resp = requests.request('POST', api_url, data=data, headers=headers)
        except:
            return request.redirect('/payment/status')

        body = json.loads(resp.text)
        if resp.status_code == 201 and body.get('result') == 'SUCCESS':
            payment_url = "https://eazypay.gateway.mastercard.com/checkout/entry/%s?checkoutVersion=1.0.0" % (body['session']['id'])
            return werkzeug.utils.redirect(payment_url)
        else:
            return request.redirect('/payment/status')
        # return body

    @http.route('/payment/eazypay/success', type='http', auth='public', website=True, sitemap=False, csrf=False,
                save_session=False, cors="https://ap-gateway.mastercard.com")
    def eazypay_success(self, **kwargs):
        order = request.env['sale.order'].sudo().search([('name', '=', kwargs['order'])])
        acquirer_id = request.env['payment.provider'].sudo().search([('code', '=', 'eazypay')], limit=1)
        order.action_confirm()
        # order = request.website.sale_get_order()
        # merchant_name = acquirer_id.eazypay_merchant_name
        # merchant_id = acquirer_id.eazypay_merchant_id
        # password = acquirer_id.eazypay_password
        # user = 'merchant.%s' % merchant_id
        # api_url = "https://eazypay.gateway.mastercard.com/api/rest/version/78/merchant/%s/order/%s" % (merchant_id, order.id)
        # headers = {
        #     "Authorization": "Basic {}".format(
        #         b64encode(bytes(f"{user}:{password}", "utf-8")).decode("ascii")
        #     )
        # }
        # # confirm that order has been paid
        # try:
        #     resp = requests.request('GET', api_url, headers=headers)
        # except:
        #     return request.redirect('/shop/cart?payment_error=True')
        # if resp.status_code != 200:
        #     return request.redirect('/shop/cart?payment_error=True')
        # order.sudo().action_confirm()
        # acquirer_id = request.env['payment.provider'].sudo().search([('code', '=', 'afs')], limit=1)
        # payment = request.env['account.payment'].sudo().create({
        #     'payment_type': 'inbound',
        #     'amount': order.amount_total,
        #     'partner_id': order.partner_id.id,
        #     'ref': order.name,
        #     'journal_id': acquirer_id.journal_id.id
        # })
        # payment.sudo().action_post()
        #
        # processing_values = {
        #     'provider_id': acquirer_id.id,
        #     'reference': order.name,
        #     'amount': order.amount_total,
        #     'currency_id': order.currency_id.id,
        #     'partner_id': order.partner_id.id,
        #     'payment_id': payment.id,
        #     'sale_order_ids': [(4, order.id)]
        # }
        # payment_transaction = request.env['payment.transaction'].sudo().create(processing_values)
        # payment_transaction.sudo()._set_done()
        # payment_transaction.sudo()._reconcile_after_done()
        return request.redirect('/shop/confirmation')

    # @http.route(['/shop/cart'], type='http', auth="public", website=True, sitemap=False)
    # def cart(self, access_token=None, revive='', **post):
    #     # override to add payment error
    #     """
    #     Main cart management + abandoned cart revival
    #     access_token: Abandoned cart SO access token
    #     revive: Revival method when abandoned cart. Can be 'merge' or 'squash'
    #     """
    #     order = request.website.sale_get_order()
    #     if order and order.state != 'draft':
    #         request.session['sale_order_id'] = None
    #         order = request.website.sale_get_order()
    #
    #     request.session['website_sale_cart_quantity'] = order.cart_quantity
    #
    #     values = {}
    #     if access_token:
    #         abandoned_order = request.env['sale.order'].sudo().search([('access_token', '=', access_token)], limit=1)
    #         if not abandoned_order:  # wrong token (or SO has been deleted)
    #             raise NotFound()
    #         if abandoned_order.state != 'draft':  # abandoned cart already finished
    #             values.update({'abandoned_proceed': True})
    #         elif revive == 'squash' or (revive == 'merge' and not request.session.get(
    #                 'sale_order_id')):  # restore old cart or merge with unexistant
    #             request.session['sale_order_id'] = abandoned_order.id
    #             return request.redirect('/shop/cart')
    #         elif revive == 'merge':
    #             abandoned_order.order_line.write({'order_id': request.session['sale_order_id']})
    #             abandoned_order.action_cancel()
    #         elif abandoned_order.id != request.session.get(
    #                 'sale_order_id'):  # abandoned cart found, user have to choose what to do
    #             values.update({'access_token': abandoned_order.access_token})
    #
    #     values.update({
    #         'website_sale_order': order,
    #         'date': fields.Date.today(),
    #         'suggested_products': [],
    #     })
    #     if post.get('payment_error'):
    #         values.update({'payment_error': True})
    #     if order:
    #         order.order_line.filtered(lambda l: not l.product_id.active).unlink()
    #         values['suggested_products'] = order._cart_accessories()
    #         values.update(self._get_express_shop_payment_values(order))
    #
    #     if post.get('type') == 'popover':
    #         # force no-cache so IE11 doesn't cache this XHR
    #         return request.render("website_sale.cart_popover", values, headers={'Cache-Control': 'no-cache'})
    #
    #     return request.render("website_sale.cart", values)


