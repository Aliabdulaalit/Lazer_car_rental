# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
import math
import calendar
from pytz import timezone
from datetime import datetime
from dateutil.relativedelta import relativedelta
from io import BytesIO
import xlsxwriter
from odoo.exceptions import ValidationError
from odoo import models, fields, api, _


class RentalVehicleImage(models.Model):
    """Rental Vehicle Image"""
    _name = "rental.vehicle.image"
    _description = __doc__

    avatar = fields.Binary(string="Avatar")
    vehicle_contract_id = fields.Many2one('vehicle.contract')


class VehicleDamageImage(models.Model):
    """Vehicle Damage Image"""
    _name = "vehicle.damage.image"
    _description = __doc__

    avatar = fields.Binary(string="Avatar")
    vehicle_contract_id = fields.Many2one('vehicle.contract')


class VehicleContract(models.Model):
    """Vehicle Contract"""
    _name = 'vehicle.contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = __doc__
    _rec_name = 'reference_no'

    reference_no = fields.Char(string='Reference No', required=True, readonly=True, default=lambda self: _('New'),
                               copy=False)
    unavailable_vehicle_ids = fields.Many2many('fleet.vehicle')
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle",
                                 domain="[('id', 'not in', vehicle_ids), ('status', '=', 'available')]", copy=False)
    vehicle_model = fields.Char(related='vehicle_id.model_id.name')
    vehicle_brand_id = fields.Many2one(related='vehicle_id.model_id.brand_id')
    vehicle_license_plate = fields.Char(related='vehicle_id.license_plate')
    vehicle_color = fields.Char(related='vehicle_id.color')

    is_driver_required = fields.Boolean(string="Driver Required")
    is_equal_date = fields.Boolean(string="Is Equal Date", compute='compute_is_equal_date', store=1)
    driver_id = fields.Many2one('res.partner', string="Driver")
    driver_charge_type = fields.Selection([('including', "Including in rent charge"),
                                           ('excluding', "Excluding in rent charge")], string="Charge Type",
                                          default='including')
    driver_charge = fields.Monetary(string="Charge")

    last_odometer = fields.Float(string="Last Odometer", copy=False)
    after_receiving_odometer = fields.Float(copy=False)
    odometer_unit = fields.Selection([('kilometers', 'km'), ('miles', 'mi')], 'Odometer Unit',
                                     default='kilometers', copy=False)
    model_year = fields.Char(string="Model", copy=False)

    fuel_type = fields.Selection([('diesel', 'Diesel'),
                                  ('gasoline', 'Gasoline'),
                                  ('full_hybrid', 'Full Hybrid'),
                                  ('plug_in_hybrid_diesel', 'Plug-in Hybrid Diesel'),
                                  ('plug_in_hybrid_gasoline', 'Plug-in Hybrid Gasoline'),
                                  ('cng', 'CNG'),
                                  ('lpg', 'LPG'),
                                  ('hydrogen', 'Hydrogen'),
                                  ('electric', 'Electric')],
                                 string="Fuel Type")
    transmission = fields.Selection([('manual', 'Manual'), ('automatic', 'Automatic')], string="Transmission",
                                    copy=False)

    customer_id = fields.Many2one("res.partner", required=True)
    customer_phone = fields.Char(string="Phone", related="customer_id.phone")
    customer_email = fields.Char(string="Email", related="customer_id.email")
    work_name = fields.Char(string="Work Name", related="customer_id.work_name")
    residence_address = fields.Char(string="Residence Address", related="customer_id.residence_address")
    driving_license_no = fields.Char(string="Driving License No.", related="customer_id.driving_license_no")
    issued_place = fields.Many2one("res.country", string="Issued Place", related="customer_id.issued_place")
    nationality = fields.Many2one("res.country", string="Nationality", related="customer_id.nationality")
    expiry_date = fields.Date(string="Expiry Date", related="customer_id.expiry_date")
    related_blacklist = fields.Boolean(string="Blacklist", related="customer_id.blacklist", store=1)
    related_cpr = fields.Char(string="CPR", related="customer_id.cpr")
    related_card_number = fields.Char(string="Card Number", related="customer_id.card_number")
    related_card_holder_name = fields.Char(string="Card Holder Name", related="customer_id.card_holder_name")
    related_card_expiration_date = fields.Date(string="Card Expiration Date",
                                               related="customer_id.card_expiration_date")
    customer_document_id = fields.Many2one("customer.documents", string="Document")
    document_count = fields.Integer(compute='_compute_document_count')

    rent_type = fields.Selection([('hour', "Hours"), ('days', "Days"), ('week', "Weeks"), ('month', "Months"),
                                  ('year', "Years"), ('km', "Kilometers"), ('mi', 'Miles')], string="Rent Type")
    total_days = fields.Float(string="Total Days", compute="_total_rental_days")
    total_km = fields.Float(string="Total Kilometers", default=1)
    total_mi = fields.Float(string="Total Miles", default=1)
    rent = fields.Monetary(string="Rent")
    total_vehicle_rent = fields.Monetary(string="Total Rental Charge", compute='_get_total_vehicle_rent')

    is_any_extra_charges = fields.Boolean(string="Is any extra charge")
    total_extra_days = fields.Integer(string="Total Extra Days", default=1)
    total_extra_week = fields.Integer(string="Total Extra Weeks", default=1)
    total_extra_month = fields.Integer(string="Total Extra Months", default=1)

    total_extra_hour = fields.Integer(string="Total Extra Hours", default=1)
    total_extra_year = fields.Integer(string="Total Extra Years", default=1)

    total_extra_km = fields.Float(string="Total Extra K/M", default=1)
    total_extra_mi = fields.Float(string="Total Extra Miles", default=1)
    km_charges = fields.Float(string="KM Charges", default=0)
    extra_charge = fields.Monetary(string="Extra Charge")
    total_extra_charges = fields.Monetary(string="Total Extra Charges", compute='_get_total_extra_charges')

    has_extra_fuel_charges = fields.Boolean("Extra Fuel Charges ?")
    fuel_charges = fields.Float()
    extra_fuel_charges_invoice_id = fields.Many2one('account.move', readonly=True)
    # total_fuel_charges = fields.Monetary(string="Total Fuel Charges", compute='_get_total_extra_charges')

    start_date = fields.Datetime(string="Pick-up Date", copy=False)
    compute_start_date = fields.Date(string="Compute Start Date", copy=False, compute='compute_date')
    pick_up_street = fields.Char(translate=True)
    pick_up_street2 = fields.Char(translate=True)
    pick_up_city = fields.Char(translate=True)
    pick_up_state_id = fields.Many2one("res.country.state", string='State',
                                       domain="[('country_id', '=?', pick_up_country_id)]")
    pick_up_country_id = fields.Many2one("res.country")
    pick_up_zip = fields.Char()

    end_date = fields.Datetime(string="Drop-off Date", tracking=True, copy=False)
    end_date_cron = fields.Many2one('ir.cron', readonly=True)
    drop_off_street = fields.Char(translate=True)
    drop_off_street2 = fields.Char(translate=True)
    drop_off_city = fields.Char(translate=True)
    drop_off_state_id = fields.Many2one("res.country.state", string=' State',
                                        domain="[('country_id', '=?', drop_off_country_id)]")
    drop_off_country_id = fields.Many2one("res.country")
    drop_off_zip = fields.Char()

    responsible_id = fields.Many2one('res.users', default=lambda self: self.env.user, required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', related="company_id.currency_id")
    cancellation_policy_id = fields.Many2one("cancellation.policy", string="Policy")
    terms_and_conditions = fields.Text(string="Terms and Conditions")
    cancellation_reason = fields.Text(string="Cancellation Reason")
    cancellation_charge = fields.Monetary(string="Cancellation Charge")
    cancellation_invoice_id = fields.Many2one('account.move')
    cancellation_invoice_state = fields.Selection(related='cancellation_invoice_id.payment_state',
                                                  string="Cancellation Invoice State")
    rental_vehicle_image_ids = fields.One2many('rental.vehicle.image', 'vehicle_contract_id')
    vehicle_damage_image_ids = fields.One2many('vehicle.damage.image', 'vehicle_contract_id')
    insurance_policy_ids = fields.One2many('insurance.policy', 'vehicle_contract_id')
    extra_service_ids = fields.One2many('extra.service', 'vehicle_contract_id')
    damage_ids = fields.One2many('damage', 'vehicle_contract_id')
    extra_service_charge = fields.Monetary(compute="_total_extra_service_charge", store=True)

    description = fields.Text(string="Description")
    damage_amount = fields.Monetary(string="Damage Amount")

    tax_ids = fields.Many2many('account.tax', string='Rent Taxes', domain=[('type_tax_use', '=', 'sale')])
    fuel_tax_ids = fields.Many2many('account.tax', 'contract_fuel_tax', 'contract_id', 'fuel_tax_id',
                                    string='Extra Fuel Taxes', domain=[('type_tax_use', '=', 'sale')])
    invoice_id = fields.Many2one('account.move')
    is_invoice_done = fields.Boolean()
    invoice_count = fields.Integer(compute='_compute_invoice_count')
    status = fields.Selection([('a_draft', 'New'), ('b_in_progress', 'In Progress'), ('c_return', 'Return'),
                               ('d_cancel', 'Cancel')], default="a_draft")
    if_any_deposit = fields.Boolean()
    deposit = fields.Monetary(string="Deposit")
    account_payment_id = fields.Many2one('account.payment', string="Deposit Payment")
    account_payment_state = fields.Selection(related='account_payment_id.state', string="Account Payment State")
    journal_id = fields.Many2one('account.journal', domain=[('type', 'in', ('bank', 'cash'))],
                                 string="Deposit Journal")
    date = fields.Date(string="Date")
    signature = fields.Binary(string="Signature")

    payment_type = fields.Selection(
        [('daily', "Daily"), ('weekly', "Weekly"), ('monthly', "Monthly"), ('quarterly', "Quarterly"),
         ('yearly', "Yearly"), ('full_payment', "Full Payment")], string="Payment Type")
    vehicle_payment_option_ids = fields.One2many('vehicle.payment.option', 'vehicle_contract_id')
    invoice_item_id = fields.Many2one('product.product', string="Invoice Item", required=True,
                                      default=lambda self: self.env.ref('vehicle_rental.vehicle_rent_charge',
                                                                        raise_if_not_found=False))
    installment_created = fields.Boolean()
    extra_charge_invoice_id = fields.Many2one('account.move', string="Extra Charge Invoice")
    extra_charge_payment_state = fields.Selection(related='extra_charge_invoice_id.payment_state',
                                                  string="Extra Charge Payment State")
    extra_service_invoice_id = fields.Many2one('account.move', string="Extra Service Invoice")
    payment_state = fields.Selection(related="extra_service_invoice_id.payment_state", string="Payment State")

    # UnUsed
    total_day_rent = fields.Monetary(compute="_total_day_rent")
    total_km_rent = fields.Monetary(compute="_total_km_rent")
    total_mi_rent = fields.Monetary(compute="_total_mi_rent")

    @api.depends('start_date')
    def compute_date(self):
        for rec in self:
            if rec.start_date:
                rec.compute_start_date = rec.start_date.date()
            else:
                rec.compute_start_date = False

    @api.depends('start_date')
    def compute_is_equal_date(self):
        for rec in self:
            if rec.start_date:
                if rec.start_date.date() == fields.date.today():
                    rec.is_equal_date = True

                else:
                    rec.is_equal_date = False

    def set_end_date_cron(self):
        for rec in self:
            if rec.end_date_cron:
                rec.end_date_cron.unlink()

            if rec.end_date and rec.company_id.fleet_vehicle_expiration_notification_user:
                rec.end_date_cron = self.env['ir.cron'].sudo().create({
                    'name': f'Contract: {rec.reference_no} drop-off',
                    'model_id': self.env['ir.model'].sudo().search([('model', '=', 'vehicle.contract')], limit=1).id,
                    'state': 'code',
                    'code': f"""
contract_id = env['vehicle.contract'].sudo().browse({rec.id})
contract_id.write({{'activity_ids': [(0, 0, {{
    'res_model_id': env['ir.model'].sudo().search([('model', '=', 'vehicle.contract')], limit=1).id,
    'activity_type_id': env.ref('mail.mail_activity_data_todo').id,
    'date_deadline': '{
        rec.end_date.astimezone(timezone(self.env.context.get('tz', 'UTC'))).replace(tzinfo=None).date()
    }',
    'summary': contract_id.reference_no + ' drop-off',
    'user_id': contract_id.company_id.fleet_vehicle_expiration_notification_user.id
}})]}})
                                """,
                    'nextcall': rec.end_date - relativedelta(
                        days=self.env.company.fleet_vehicle_expiration_notification_days
                    ),
                    'numbercall': 1,
                    'active': True,
                })

    def action_block_customer(self):
        for rec in self:
            rec.customer_id.blacklist = True

    def action_unblock_customer(self):
        for rec in self:
            rec.customer_id.blacklist = False

    def a_draft_to_b_in_progress(self):
        for rec in self:
            vehicle_id = rec.vehicle_id.id
            existing_contract = self.env['vehicle.contract'].search(
                [('vehicle_id', '=', vehicle_id), ('status', '=', 'b_in_progress')])
            if existing_contract:
                message = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'warning',
                        'message': _(
                            "There is already a running contract for this vehicle. Please return the car before selecting a new contract."),
                        'sticky': False,
                    }
                }
                return message
            self.ensure_one()
            template_id = self.env.ref("vehicle_rental.vehicle_rental_booking_mail_template").sudo()
            ctx = {
                'default_model': 'vehicle.contract',
                'default_res_ids': self.ids,
                'default_partner_ids': [self.customer_id.id],
                'default_use_template': bool(template_id),
                'default_template_id': template_id.id,
                'default_composition_mode': 'comment',
                'default_email_from': self.env.company.email,
                'default_reply_to': self.env.company.email,
                'custom_layout': False,
                'force_email': True,
            }
            self.status = 'b_in_progress'
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(False, 'form')],
                'view_id': False,
                'target': 'new',
                'context': ctx,
            }

    def b_in_progress_to_c_return(self):
        for rec in self:
            if rec.last_odometer > rec.after_receiving_odometer:
                raise ValidationError(_("After receiving odometer cannot be less than last odometer"))
            rec.vehicle_id.odometer = rec.after_receiving_odometer
            rec.status = 'c_return'

    def c_return_to_d_cancel(self):
        for rec in self:
            rec.status = 'd_cancel'

    def action_vehicle_rent_deposit(self):
        for rec in self:
            if rec.if_any_deposit:
                if not rec.deposit:
                    message = {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'type': 'warning',
                            'message': "Please note: A rented vehicle deposit is required.",
                            'sticky': False,
                        }
                    }
                    return message
                data = {
                    'partner_id': self.customer_id.id,
                    'payment_type': 'inbound',
                    'amount': self.deposit,
                    'journal_id': self.journal_id.id,
                    'vehicle_contract_id': self.id,
                    'vehicle_contract_invoice_type': 'deposit'
                }
                account_payment_id = self.env['account.payment'].sudo().create(data)
                account_payment_id.action_post()
                self.account_payment_id = account_payment_id.id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference_no', _('New')) == _('New'):
                vals['reference_no'] = self.env['ir.sequence'].next_by_code('vehicle.contract') or _('New')

        res = super(VehicleContract, self).create(vals_list)

        res.set_end_date_cron()

        return res

    def write(self, vals):
        res = super(VehicleContract, self).write(vals)

        if 'end_date' in vals:
            self.set_end_date_cron()

        return res

    @api.onchange('start_date', 'end_date')
    def get_vehicle_select(self):
        for rec in self:
            if not rec.start_date or not rec.end_date:
                rec.vehicle_id = False

    # @api.onchange('customer_id')
    # def get_customer_details(self):
    #     for rec in self:
    #         if rec.customer_id:
    #             rec.customer_phone = rec.customer_id.phone
    #             rec.customer_email = rec.customer_id.email
    #             rec.work_name = rec.customer_id.work_name
    #             rec.residence_address = rec.customer_id.residence_address
    #             rec.driving_license_no = rec.customer_id.driving_license_no
    #             rec.issued_place = rec.customer_id.issued_place
    #             rec.expiry_date = rec.customer_id.expiry_date

    @api.onchange('vehicle_id')
    def get_vehicle_details(self):
        for rec in self:
            if rec.vehicle_id:
                rec.driver_id = rec.vehicle_id.driver_id
                rec.last_odometer = rec.vehicle_id.odometer
                rec.odometer_unit = rec.vehicle_id.odometer_unit
                rec.model_year = rec.vehicle_id.model_year
                rec.transmission = rec.vehicle_id.transmission
                rec.fuel_type = rec.vehicle_id.fuel_type

    @api.onchange('cancellation_policy_id')
    def get_policy_terms(self):
        for rec in self:
            if rec.cancellation_policy_id:
                rec.terms_and_conditions = rec.cancellation_policy_id.terms_and_conditions

    @api.onchange('rent_type', 'vehicle_id')
    def get_vehicle_rent_details(self):
        for rec in self:
            if rec.vehicle_id:
                if self.rent_type == 'days':
                    rec.rent = rec.vehicle_id.rent_day
                    rec.extra_charge = rec.vehicle_id.extra_charge_day
                elif self.rent_type == 'week':
                    rec.rent = rec.vehicle_id.rent_week
                    rec.extra_charge = rec.vehicle_id.extra_charge_week
                elif self.rent_type == 'month':
                    rec.rent = rec.vehicle_id.rent_month
                    rec.extra_charge = rec.vehicle_id.extra_charge_month
                elif self.rent_type == 'hour':
                    rec.rent = rec.vehicle_id.rent_hour
                    rec.extra_charge = rec.vehicle_id.extra_charge_hour
                elif self.rent_type == 'year':
                    rec.rent = rec.vehicle_id.rent_year
                    rec.extra_charge = rec.vehicle_id.extra_charge_year
                elif self.rent_type == 'km':
                    rec.rent = rec.vehicle_id.rent_km
                    rec.extra_charge = rec.vehicle_id.extra_charge_km
                elif self.rent_type == 'mi':
                    rec.rent = rec.vehicle_id.rent_mi
                    rec.extra_charge = rec.vehicle_id.extra_charge_mi

    @api.constrains('rent_type')
    def _get_rent_type(self):
        for record in self:
            if not record.rent_type:
                raise ValidationError(
                    _("Choose your preferred rental unit (days, week, month, hour, year, kilometers, or miles) and proceed accordingly."))

    @api.depends('extra_service_ids.amount', 'extra_service_ids.product_qty')
    def _total_extra_service_charge(self):
        for rec in self:
            extra_service_charge = 0.0
            for charge in rec.extra_service_ids:
                extra_service_charge = extra_service_charge + (charge.amount * charge.product_qty)
            rec.extra_service_charge = extra_service_charge

    @api.onchange('start_date', 'end_date')
    def _compute_unavailable_vehicle_ids(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                rec.unavailable_vehicle_ids = self.env['vehicle.contract'].search([
                    ('status', '=', 'b_in_progress'),
                    '|',
                    '&', ('start_date', '>=', rec.start_date), ('start_date', '<=', rec.end_date),
                    '&', ('end_date', '>=', rec.start_date), ('end_date', '<=', rec.end_date),
                ]).vehicle_id
            else:
                rec.unavailable_vehicle_ids = None
            rec.vehicle_id = None

    @api.constrains('start_date', 'end_date')
    def _contract_check_dates(self):
        for record in self:
            if record.start_date > record.end_date:
                raise ValidationError(_("Please ensure that the Drop-off Date is greater than the Pick-up Date"))

    @api.depends('rent_type', 'start_date', 'end_date')
    def _total_rental_days(self):
        for rec in self:
            count = 0.0
            if rec.end_date and rec.start_date and not (rec.start_date > rec.end_date):
                if rec.rent_type == 'days':
                    count = (rec.end_date - rec.start_date).days
                elif rec.rent_type == 'week':
                    count = (rec.end_date - rec.start_date).days / 7
                elif rec.rent_type == 'month':
                    delta_months = (rec.end_date.year - rec.start_date.year) * 12 + (
                            rec.end_date.month - rec.start_date.month)
                    count = delta_months + (rec.end_date.day - rec.start_date.day) / 30
                elif rec.rent_type == 'hour':
                    count = (rec.end_date - rec.start_date).total_seconds() / 3600
                elif rec.rent_type == 'year':
                    delta_years = rec.end_date.year - rec.start_date.year
                    remaining_months = rec.end_date.month - rec.start_date.month
                    remaining_days = (rec.end_date.day - rec.start_date.day) / 30
                    count = delta_years + remaining_months / 12 + remaining_days / 365
            rec.total_days = round(count, 2)

    @api.depends('total_vehicle_rent', 'rent_type', 'rent', 'total_days', 'driver_charge', 'total_km',
                 'driver_charge_type', 'total_mi')
    def _get_total_vehicle_rent(self):
        for rec in self:
            total_vehicle_rent = 0.0
            total = 0.0
            if rec.rent and rec.rent_type:
                if rec.rent_type in ['days', 'week', 'month', 'hour', 'year']:
                    total_vehicle_rent = rec.rent * rec.total_days
                elif rec.rent_type == 'km':
                    total_vehicle_rent = rec.rent * rec.total_km
                elif rec.rent_type == 'mi':
                    total_vehicle_rent = rec.rent * rec.total_mi
            if rec.driver_charge_type == 'including':
                total = total_vehicle_rent
            elif rec.driver_charge_type == 'excluding':
                total = total_vehicle_rent + rec.driver_charge
            rec.total_vehicle_rent = round(total, 2)

    @api.depends('total_extra_charges', 'rent_type', 'extra_charge', 'total_extra_days', 'total_extra_week',
                 'total_extra_month', 'total_extra_hour', 'total_extra_year', 'total_extra_km', 'total_extra_mi')
    def _get_total_extra_charges(self):
        for rec in self:
            total_extra_charges = 0.0
            if rec.extra_charge and rec.rent_type:
                if rec.rent_type == 'days':
                    total_extra_charges = rec.extra_charge * rec.total_extra_days
                elif rec.rent_type == 'week':
                    total_extra_charges = rec.extra_charge * rec.total_extra_week
                elif rec.rent_type == 'month':
                    total_extra_charges = rec.extra_charge * rec.total_extra_month
                elif rec.rent_type == 'hour':
                    total_extra_charges = rec.extra_charge * rec.total_extra_hour
                elif rec.rent_type == 'year':
                    total_extra_charges = rec.extra_charge * rec.total_extra_year
                elif rec.rent_type == 'km':
                    total_extra_charges = rec.extra_charge * rec.total_extra_km
                elif rec.rent_type == 'mi':
                    total_extra_charges = rec.extra_charge * rec.total_extra_mi
            rec.total_extra_charges = total_extra_charges + rec.km_charges
            # if rec.fuel_charges:
            #     rec.total_fuel_charges = rec.fuel_charges
            # else:
            #     rec.total_fuel_charges = 0

    def action_create_extra_charge_invoice(self):
        invoice_lines = []
        print(invoice_lines, "invvvvvv")
        if self.rent_type == 'days':
            invoice_lines.append((0, 0, {'product_id': self.env.ref('vehicle_rental.vehicle_rent_extra_charge').id,
                                         'name': self.vehicle_id.name,
                                         'analytic_distribution': {self.vehicle_id.analytic_tag_ids.id: 100},
                                         'quantity': self.total_extra_days,
                                         'price_unit': self.extra_charge,
                                         }))
        # if self.rent_type == 'days':
        #     extra_days = {
        #         'product_id': self.env.ref('vehicle_rental.vehicle_rent_extra_charge').id,
        #         'name': self.vehicle_id.name,
        #         'quantity': self.total_extra_days,
        #         'price_unit': self.extra_charge,
        #     }
        #     print("00000000")
        #     invoice_lines = [(0, 0, extra_days)]
        if self.rent_type == 'week':
            invoice_lines.append((0, 0, {'product_id': self.env.ref('vehicle_rental.vehicle_rent_extra_charge').id,
                                         'name': self.vehicle_id.name,
                                         'analytic_distribution': {self.vehicle_id.analytic_tag_ids.id: 100},
                                         'quantity': self.total_extra_week,
                                         'price_unit': self.extra_charge,
                                         }))
            # extra_weeks = {
            #     'product_id': self.env.ref('vehicle_rental.vehicle_rent_extra_charge').id,
            #     'name': self.vehicle_id.name,
            #     'quantity': self.total_extra_week,
            #     'price_unit': self.extra_charge,
            # }
            # invoice_lines = [(0, 0, extra_weeks)]
        if self.rent_type == 'month':
            invoice_lines.append((0, 0, {'product_id': self.env.ref('vehicle_rental.vehicle_rent_extra_charge').id,
                                         'analytic_distribution': {self.vehicle_id.analytic_tag_ids.id: 100},
                                         'name': self.vehicle_id.name,
                                         'quantity': self.total_extra_month,
                                         'price_unit': self.extra_charge,
                                         }))
            # extra_months = {
            #     'product_id': self.env.ref('vehicle_rental.vehicle_rent_extra_charge').id,
            #     'name': self.vehicle_id.name,
            #     'quantity': self.total_extra_month,
            #     'price_unit': self.extra_charge,
            # }
            # invoice_lines = [(0, 0, extra_months)]
        if self.rent_type == 'hour':
            invoice_lines.append((0, 0, {'product_id': self.env.ref('vehicle_rental.vehicle_rent_extra_charge').id,
                                         'name': self.vehicle_id.name,
                                         'quantity': self.total_extra_hour,
                                         'price_unit': self.extra_charge,
                                         }))
            # extra_hours = {
            #     'product_id': self.env.ref('vehicle_rental.vehicle_rent_extra_charge').id,
            #     'name': self.vehicle_id.name,
            #     'quantity': self.total_extra_hour,
            #     'price_unit': self.extra_charge,
            # }
            # invoice_lines = [(0, 0, extra_hours)]
        if self.rent_type == 'year':
            invoice_lines.append((0, 0, {'product_id': self.env.ref('vehicle_rental.vehicle_rent_extra_charge').id,
                                         'name': self.vehicle_id.name,
                                         'analytic_distribution': {self.vehicle_id.analytic_tag_ids.id: 100},
                                         'quantity': self.total_extra_year,
                                         'price_unit': self.extra_charge,
                                         }))
            # extra_years = {
            #     'product_id': self.env.ref('vehicle_rental.vehicle_rent_extra_charge').id,
            #     'name': self.vehicle_id.name,
            #     'quantity': self.total_extra_year,
            #     'price_unit': self.extra_charge,
            # }
            # invoice_lines = [(0, 0, extra_years)]
        if self.rent_type == 'km':
            invoice_lines.append((0, 0, {'product_id': self.env.ref('vehicle_rental.vehicle_rent_extra_charge').id,
                                         'name': self.vehicle_id.name,
                                         'analytic_distribution': {self.vehicle_id.analytic_tag_ids.id: 100},
                                         'quantity': self.total_extra_km,
                                         'price_unit': self.extra_charge,
                                         }))
            # extra_kms = {
            #     'product_id': self.env.ref('vehicle_rental.vehicle_rent_extra_charge').id,
            #     'name': self.vehicle_id.name,
            #     'quantity': self.total_extra_km,
            #     'price_unit': self.extra_charge,
            # }
            # invoice_lines = [(0, 0, extra_kms)]
        if self.rent_type == 'mi':
            invoice_lines.append((0, 0, {'product_id': self.env.ref('vehicle_rental.vehicle_rent_extra_charge').id,
                                         'name': self.vehicle_id.name,
                                         'analytic_distribution': {self.vehicle_id.analytic_tag_ids.id: 100},
                                         'quantity': self.total_extra_mi,
                                         'price_unit': self.extra_charge,
                                         }))
            # extra_mis = {
            #     'product_id': self.env.ref('vehicle_rental.vehicle_rent_extra_charge').id,
            #     'name': self.vehicle_id.name,
            #     'quantity': self.total_extra_mi,
            #     'price_unit': self.extra_charge,
            # }
            # invoice_lines = [(0, 0, extra_mis)]
        if self.km_charges:
            invoice_lines.append((0, 0, {'product_id': self.env.ref('vehicle_rental.vehicle_rent_km_extra_charge').id,
                                         'name': self.vehicle_id.name,
                                         'analytic_distribution': {self.vehicle_id.analytic_tag_ids.id: 100},
                                         'quantity': 1,
                                         'price_unit': self.km_charges,
                                         }))
            # fuel_extra_charges = {
            #     'product_id': self.env.ref('vehicle_rental.vehicle_rent_fuel_extra_charge').id,
            #     'name': self.vehicle_id.name,
            #     'quantity': 1,
            #     'price_unit': self.total_fuel_charges,
            # }
            # invoice_lines = [(0, 0, fuel_extra_charges)]
            print("111111")
        data = {
            'partner_id': self.customer_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_lines,
            'vehicle_contract_id': self.id,
            'vehicle_contract_invoice_type': 'extra_charges'
        }
        extra_charge_invoice_id = self.env['account.move'].sudo().create(data)
        extra_charge_invoice_id.action_post()
        self.extra_charge_invoice_id = extra_charge_invoice_id.id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Extra Charge Invoice'),
            'res_model': 'account.move',
            'res_id': extra_charge_invoice_id.id,
            'view_mode': 'form',
            'target': 'current'
        }

    def action_create_extra_fuel_charges_invoice(self):
        self.ensure_one()

        if self.fuel_charges > 0.0:
            self.extra_fuel_charges_invoice_id = self.env['account.move'].create({
                'partner_id': self.customer_id.id,
                'move_type': 'out_invoice',
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': [(0, 0, {
                    'product_id': self.env.ref('vehicle_rental.vehicle_rent_fuel_extra_charge').id,
                    'name': self.vehicle_id.name,
                    'analytic_distribution': {self.vehicle_id.analytic_tag_ids.id: 100},
                    'quantity': 1,
                    'price_unit': self.fuel_charges,
                    'tax_ids': [(6, 0, self.fuel_tax_ids.ids)]
                })],
                'vehicle_contract_id': self.id,
                'vehicle_contract_invoice_type': 'extra_fuel_charges'
            })
            self.extra_fuel_charges_invoice_id.action_post()

            return {
                'name': _('%s Extra Fuel Charges Invoice' % self.reference_no),
                'view_mode': 'form',
                'res_model': 'account.move',
                'res_id': self.extra_fuel_charges_invoice_id.id,
                'type': 'ir.actions.act_window',
                'target': 'current'
            }
        else:
            raise ValidationError(_("Fuel charges must be positive."))

    def action_create_vehicle_payment(self):
        for rec in self:
            if not rec.payment_type:
                message = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'warning',
                        'message': "Select your preferred payment method to proceed.",
                        'sticky': False,
                    }
                }
                return message
            if rec.end_date and rec.start_date:
                days_diff = rec.end_date - rec.start_date
                diff = relativedelta(rec.end_date, rec.start_date)
                total_days = days_diff.days

                total_months = (diff.years * 12) + diff.months
                total_weeks = total_days // 7
                quarter = (rec.end_date.year - rec.start_date.year) * 12 + rec.end_date.month - rec.start_date.month
                total_quarters = quarter // 3

                year_diff = relativedelta(rec.end_date, rec.start_date)
                total_years = year_diff.years + year_diff.months / 12 + year_diff.days / 365

                amount = self.total_vehicle_rent

                if self.payment_type == 'full_payment':
                    full_payment_data = {
                        'invoice_item_id': self.invoice_item_id.id,
                        'name': 'Full Payment Invoice',
                        'payment_date': fields.Date.today(),
                        'payment_amount': amount,
                        'vehicle_contract_id': self.id,
                    }
                    self.env['vehicle.payment.option'].create(full_payment_data)
                elif self.payment_type == 'daily':
                    if total_days == 0:
                        daily_payment_data = {
                            'invoice_item_id': self.invoice_item_id.id,
                            'name': 'Daily Payment Invoice',
                            'payment_date': fields.Date.today(),
                            'payment_amount': amount,
                            'vehicle_contract_id': self.id,
                        }
                        self.env['vehicle.payment.option'].create(daily_payment_data)
                    elif total_days > 0:
                        day_amount = amount / total_days
                        invoice_date = self.start_date.date()
                        for i in range(total_days):
                            daily_payment_data = {
                                'invoice_item_id': self.invoice_item_id.id,
                                'name': 'Installment ' + str(i + 1),
                                'payment_date': invoice_date,
                                'payment_amount': day_amount,
                                'vehicle_contract_id': self.id,
                            }
                            self.env['vehicle.payment.option'].create(daily_payment_data)
                            invoice_date = invoice_date + relativedelta(days=1)
                elif self.payment_type == 'monthly':
                    if total_months == 0:
                        monthly_payment_data = {
                            'invoice_item_id': self.invoice_item_id.id,
                            'name': 'Monthly Payment Invoice',
                            'payment_date': fields.Date.today(),
                            'payment_amount': amount,
                            'vehicle_contract_id': self.id,
                        }
                        self.env['vehicle.payment.option'].create(monthly_payment_data)
                    if total_months > 0:
                        day_amount = amount / total_days
                        remain_amount = amount
                        invoice_date = self.start_date.date()
                        for i in range(total_months):
                            current_month_days = calendar.monthrange(invoice_date.year, invoice_date.month)[1]
                            monthly_payment_data = {
                                'invoice_item_id': self.invoice_item_id.id,
                                'name': 'Installment ' + str(i + 1),
                                'payment_date': invoice_date,
                                'payment_amount': current_month_days * day_amount,
                                'vehicle_contract_id': self.id,
                            }
                            self.env['vehicle.payment.option'].create(monthly_payment_data)
                            invoice_date = invoice_date + relativedelta(months=1)
                            remain_amount = remain_amount - monthly_payment_data['payment_amount']
                        if remain_amount > 0:
                            monthly_payment_data = {
                                'invoice_item_id': self.invoice_item_id.id,
                                'name': 'Remain Days ',
                                'payment_date': invoice_date,
                                'payment_amount': remain_amount,
                                'vehicle_contract_id': self.id,
                            }
                            self.env['vehicle.payment.option'].create(monthly_payment_data)
                elif self.payment_type == 'weekly':
                    if total_weeks == 0:
                        weekly_payment_data = {
                            'invoice_item_id': self.invoice_item_id.id,
                            'name': 'Weekly Payment Invoice',
                            'payment_date': fields.Date.today(),
                            'payment_amount': amount,
                            'vehicle_contract_id': self.id,
                        }
                        self.env['vehicle.payment.option'].create(weekly_payment_data)
                    if total_weeks > 0:
                        start_date = self.start_date
                        day_amount = amount / total_days
                        remain_amount = amount
                        invoice_date = self.start_date.date()
                        for i in range(total_weeks):
                            q_end_date = start_date + relativedelta(days=7)
                            q_days = (q_end_date - start_date).days
                            weekly_payment_data = {
                                'invoice_item_id': self.invoice_item_id.id,
                                'name': 'Installment ' + str(i + 1),
                                'payment_date': invoice_date,
                                'payment_amount': q_days * day_amount,
                                'vehicle_contract_id': self.id,
                            }
                            self.env['vehicle.payment.option'].create(weekly_payment_data)
                            invoice_date = invoice_date + relativedelta(days=7)
                            remain_amount = remain_amount - weekly_payment_data['payment_amount']
                        if remain_amount > 0:
                            weekly_payment_data = {
                                'invoice_item_id': self.invoice_item_id.id,
                                'name': 'Remain Days',
                                'payment_date': invoice_date,
                                'payment_amount': remain_amount,
                                'vehicle_contract_id': self.id,
                            }
                            self.env['vehicle.payment.option'].create(weekly_payment_data)
                elif self.payment_type == 'quarterly':
                    if total_quarters == 0:
                        quarterly_payment_data = {
                            'invoice_item_id': self.invoice_item_id.id,
                            'name': 'Quarterly Payment Invoice',
                            'payment_date': fields.Date.today(),
                            'payment_amount': amount,
                            'vehicle_contract_id': self.id,
                        }
                        self.env['vehicle.payment.option'].create(quarterly_payment_data)
                    if total_quarters > 0:
                        start_date = self.start_date
                        day_amount = amount / total_days
                        remain_amount = amount
                        for i in range(total_quarters):
                            q_end_date = start_date + relativedelta(months=3)
                            q_days = (q_end_date - start_date).days
                            payment_data = {
                                'invoice_item_id': self.invoice_item_id.id,
                                'name': 'Installment ' + str(i + 1),
                                'payment_date': start_date,
                                'payment_amount': q_days * day_amount,
                                'vehicle_contract_id': self.id,
                            }
                            self.env['vehicle.payment.option'].create(payment_data)
                            start_date = q_end_date + relativedelta(days=1)
                            remain_amount = remain_amount - payment_data['payment_amount']
                        if remain_amount > 0:
                            monthly_payment_data = {
                                'invoice_item_id': self.invoice_item_id.id,
                                'name': 'Remain Days ',
                                'payment_date': start_date,
                                'payment_amount': remain_amount,
                                'vehicle_contract_id': self.id,
                            }
                            self.env['vehicle.payment.option'].create(monthly_payment_data)

                elif self.payment_type == 'yearly':
                    if total_years == 0:
                        yearly_payment_data = {
                            'invoice_item_id': self.invoice_item_id.id,
                            'name': 'Yearly Payment Invoice',
                            'payment_date': fields.Date.today(),
                            'payment_amount': amount,
                            'vehicle_contract_id': self.id,
                        }
                        self.env['vehicle.payment.option'].create(yearly_payment_data)
                    elif total_years > 0:
                        start_date = self.start_date
                        day_amount = amount / total_days
                        current_year = self.start_date.year
                        current_year_start_date = datetime(current_year, 1, 1)
                        current_year_end_date = datetime(current_year + 1, 1, 1)
                        number_of_days_in_current_year = (current_year_end_date - current_year_start_date).days
                        full_year_amount = round(number_of_days_in_current_year * day_amount, 2)
                        remain_amount = amount
                        for installment_number in range(int(total_years)):
                            payment_data = {
                                'invoice_item_id': self.invoice_item_id.id,
                                'name': f'Installment {installment_number + 1}',
                                'payment_date': start_date,
                                'payment_amount': full_year_amount,
                                'vehicle_contract_id': self.id,
                            }
                            self.env['vehicle.payment.option'].create(payment_data)
                            start_date = start_date + relativedelta(years=1)
                            remain_amount = remain_amount - payment_data['payment_amount']
                            current_year = start_date.year
                            current_year_start_date = datetime(current_year, 1, 1)
                            current_year_end_date = datetime(current_year + 1, 1, 1)
                            number_of_days_in_current_year = (current_year_end_date - current_year_start_date).days
                            full_year_amount = number_of_days_in_current_year * day_amount
                        if remain_amount > 0:
                            remain_days_payment_data = {
                                'invoice_item_id': self.invoice_item_id.id,
                                'name': 'Remain Days',
                                'payment_date': start_date,
                                'payment_amount': remain_amount,
                                'vehicle_contract_id': self.id,
                            }
                            self.env['vehicle.payment.option'].create(remain_days_payment_data)
            self.installment_created = True

    def action_create_extra_service_charge_invoice(self):
        invoice_lines = []
        for record in self.extra_service_ids:
            extra_service = {
                'product_id': record.product_id.id,
                'name': record.description,
                'quantity': record.product_qty,
                'price_unit': record.amount,
            }
            invoice_lines.append((0, 0, extra_service))
        data = {
            'partner_id': self.customer_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_lines,
            'vehicle_contract_id': self.id,
            'vehicle_contract_invoice_type': 'extra_services'
        }
        extra_service_invoice_id = self.env['account.move'].sudo().create(data)
        extra_service_invoice_id.action_post()
        self.extra_service_invoice_id = extra_service_invoice_id.id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Extra Service Invoice'),
            'res_model': 'account.move',
            'res_id': extra_service_invoice_id.id,
            'view_mode': 'form',
            'target': 'current'
        }

    def _compute_document_count(self):
        for rec in self:
            document_count = self.env['customer.documents'].search_count([('vehicle_contract_id', '=', rec.id)])
            rec.document_count = document_count
        return True

    def action_customer_document(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Documents'),
            'res_model': 'customer.documents',
            'domain': [('vehicle_contract_id', '=', self.id)],
            'context': {'default_vehicle_contract_id': self.id},
            'view_mode': 'tree',
            'target': 'current',
        }

    def _compute_invoice_count(self):
        for rec in self:
            invoice_count = self.env['account.move'].search_count([
                ('vehicle_contract_id', '=', rec.id), ('move_type', '=', 'out_invoice')
            ])
            rec.invoice_count = invoice_count
        return True

    def view_customer_invoice(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoices'),
            'res_model': 'account.move',
            'domain': [('vehicle_contract_id', '=', self.id), ('move_type', '=', 'out_invoice')],
            'context': {
                'default_vehicle_contract_id': self.id,
                'create': False,
            },
            'view_mode': 'tree,form',
            'target': 'current',
        }

    def cancellation_charge_invoice(self):
        invoice_line = []
        for rec in self:
            if not rec.cancellation_charge:
                message = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'warning',
                        'message': "Please note: A vehicle contract cancellation charge is required.",
                        'sticky': False,
                    }
                }
                return message
            cancellation_data = {
                'product_id': self.env.ref('vehicle_rental.vehicle_contract_cancellation_charge').id,
                'name': rec.cancellation_policy_id.title,
                'quantity': 1,
                'price_unit': rec.cancellation_charge
            }
            invoice_line = [(0, 0, cancellation_data)]
        data = {
            'partner_id': self.customer_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_line,
            'vehicle_contract_id': self.id,
            'vehicle_contract_invoice_type': 'cancellation'
        }
        cancellation_invoice_id = self.env['account.move'].sudo().create(data)
        cancellation_invoice_id.action_post()
        self.cancellation_invoice_id = cancellation_invoice_id.id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cancellation Invoice'),
            'res_model': 'account.move',
            'res_id': cancellation_invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def action_create_rent_payment_invoice(self):
        rental_contract = self.env['vehicle.contract'].sudo().search([('status', '=', 'b_in_progress')])
        today_date = fields.Date.today()
        for data in rental_contract:
            for rec in data.vehicle_payment_option_ids:
                if rec.payment_date == today_date:
                    rec.action_create_payment_invoice()

    def unlink(self):
        for rec in self:
            if rec.status != 'c_return':
                super(VehicleContract, rec).unlink()
            else:
                raise ValidationError(_('You cannot delete the return order.'))

    def generate_xlsx(self):
        return {
            'type': 'ir.actions.act_url',
            'url': f'{self.env.context["route"]}/{",".join([str(contract_id) for contract_id in self.ids])}'
        }

    @api.model
    def action_export(self, contract_ids, response):
        output = BytesIO()

        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        sheet = workbook.add_worksheet()

        header_format = workbook.add_format({
            'font_name': 'Courier New',
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'border_color': '#000000',
            'bg_color': '#CCCCCC'
        })

        sheet.merge_range(0, 0, 0, 5, 'Personal Details', header_format)
        sheet.merge_range(0, 6, 0, 9, 'Vehicle Details', header_format)
        sheet.merge_range(0, 10, 0, 11, 'Date / Timing', header_format)

        headers = [
            '#', 'Name', 'CPR / Passport', 'Nationality', 'Mobile', 'Address',
            'Brand', 'Model', 'Color', 'Plate No.',
            'Pick-up', 'Drop-off'
        ]

        max_size = [len(header) for header in headers]

        sheet.write_row(1, 0, headers, header_format)

        sheet.set_row(1, 25)

        data_format = workbook.add_format({
            'font_name': 'Courier New',
            'valign': 'vcenter',
            'border': 1,
            'border_color': '#000000',
        })

        row = 2
        for contract in self.env['vehicle.contract'].browse(contract_ids):
            data = [
                str(row - 1),
                contract.customer_id.name or '',
                contract.related_cpr or '',
                contract.nationality.name or '',
                contract.customer_phone or '',
                contract.residence_address or '',

                contract.vehicle_id.model_id.brand_id.name or '',
                contract.vehicle_id.model_id.name or '',
                contract.vehicle_id.color or '',
                contract.vehicle_id.license_plate or '',

                str(contract.start_date.astimezone(
                    timezone(self.env.context.get('tz', 'UTC'))
                ).replace(tzinfo=None)) if contract.start_date else '',
                str(contract.end_date.astimezone(
                    timezone(self.env.context.get('tz', 'UTC'))
                ).replace(tzinfo=None)) if contract.end_date else '',
            ]

            sheet.write_row(row, 0, data, data_format)

            for col in range(len(headers)):
                max_size[col] = max(max_size[col], len(data[col]))

            row += 1

        for col in range(len(headers)):
            sheet.set_column(col, col, max_size[col])

        workbook.close()

        output.seek(0)
        response.stream.write(output.read())
        output.close()

        return output

    @api.model
    def action_print_rental_deposit(self, contract_ids, response):
        output = BytesIO()

        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        sheet = workbook.add_worksheet()

        header_format = workbook.add_format({
            'font_name': 'Courier New',
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'border_color': '#000000',
            'bg_color': '#CCCCCC'
        })

        headers = ['S/N', 'NAME', 'ARG NO', 'CAR NO', 'RECEIPT', 'AMOUNT', 'PAYMENT TYPE']

        max_size = [len(header) for header in headers]

        sheet.write_row(0, 0, headers, header_format)

        data_format = workbook.add_format({
            'font_name': 'Courier New',
            'valign': 'vcenter',
            'border': 1,
            'border_color': '#000000',
        })

        row = 1
        for contract in self.env['vehicle.contract'].browse(contract_ids):
            for payment in self.env['account.payment'].search([('vehicle_contract_id', '=', contract.id)]).filtered(
                lambda p: p.state == 'posted'
            ):
                data = [
                    str(row),
                    contract.customer_id.name or '',
                    contract.reference_no or '',
                    contract.vehicle_id.license_plate or '',
                    ', '.join(payment.reconciled_invoice_ids.mapped('name')) or '',
                    str('{:,.3f}'.format(payment.amount)) or '',
                    payment.journal_id.name or '',
                ]

                sheet.write_row(row, 0, data, data_format)

                for col in range(len(headers)):
                    max_size[col] = max(max_size[col], len(data[col]))

                row += 1

        for col in range(len(headers)):
            sheet.set_column(col, col, max_size[col])

        workbook.close()

        output.seek(0)
        response.stream.write(output.read())
        output.close()

        return output

    @api.model
    def action_print_damage_deposit(self, contract_ids, response):
        output = BytesIO()

        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        sheet = workbook.add_worksheet()

        header_format = workbook.add_format({
            'font_name': 'Courier New',
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'border_color': '#000000',
            'bg_color': '#CCCCCC'
        })

        headers = ['S/N', 'NAME', 'ARG NO', 'CAR NO', 'RECEIPT', 'RATE', 'SPAN', 'AMOUNT', 'PAYMENT TYPE']

        max_size = [len(header) for header in headers]

        sheet.write_row(0, 0, headers, header_format)

        data_format = workbook.add_format({
            'font_name': 'Courier New',
            'valign': 'vcenter',
            'border': 1,
            'border_color': '#000000',
        })

        row = 1
        for contract in self.env['vehicle.contract'].browse(contract_ids):
            for payment in self.env['account.payment'].search([('vehicle_contract_id', '=', contract.id)]).filtered(
                lambda p: p.state == 'posted'
            ):
                data = [
                    str(row),
                    contract.customer_id.name or '',
                    contract.reference_no or '',
                    contract.vehicle_id.license_plate or '',
                    ', '.join(payment.reconciled_invoice_ids.mapped('name')) or '',
                    str('{:,.3f}'.format(contract.rent)) or '',
                    dict(self.env['vehicle.contract'].fields_get(
                        allfields=['rent_type']
                    )['rent_type']['selection']).get(contract.rent_type) or '',
                    str('{:,.3f}'.format(payment.amount)) or '',
                    payment.journal_id.name or '',
                ]

                sheet.write_row(row, 0, data, data_format)

                for col in range(len(headers)):
                    max_size[col] = max(max_size[col], len(data[col]))

                row += 1

        for col in range(len(headers)):
            sheet.set_column(col, col, max_size[col])

        workbook.close()

        output.seek(0)
        response.stream.write(output.read())
        output.close()

        return output

    @api.model
    def action_export_cid_daily(self, contract_ids, response):
        output = BytesIO()

        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        sheet = workbook.add_worksheet()

        header_format = workbook.add_format({
            'font_name': 'Courier New',
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'border_color': '#000000',
            'bg_color': '#CCCCCC'
        })

        headers = [
            'Name', 'CPR / Passport', 'Nationality', 'Mobile', 'Address',
            'Brand', 'Model', 'Color', 'Plate No.',
            'Pick-up', 'Drop-off'
        ]

        max_size = [len(header) for header in headers]

        sheet.write_row(0, 0, headers, header_format)

        subtitle_format = workbook.add_format({
            'font_name': 'Courier New',
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
        })

        data_format = workbook.add_format({
            'font_name': 'Courier New',
            'valign': 'vcenter',
            'border': 1,
            'border_color': '#000000',
        })

        now = datetime.now()

        start_date = now.astimezone(
            timezone(self.env.context.get('tz', 'UTC'))
        ).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
        end_date = start_date + relativedelta(days=1)

        def get_data(contract):
            return [
                contract.customer_id.name or '',
                contract.related_cpr or '',
                contract.nationality.name or '',
                contract.customer_phone or '',
                contract.residence_address or '',

                contract.vehicle_id.model_id.brand_id.name or '',
                contract.vehicle_id.model_id.name or '',
                contract.vehicle_id.color or '',
                contract.vehicle_id.license_plate or '',

                str(contract.start_date.astimezone(
                    timezone(self.env.context.get('tz', 'UTC'))
                ).replace(tzinfo=None)) if contract.start_date else '',
                str(contract.end_date.astimezone(
                    timezone(self.env.context.get('tz', 'UTC'))
                ).replace(tzinfo=None)) if contract.end_date else '',
            ]

        row = 1

        vehicles_in = self.env['vehicle.contract'].browse(contract_ids).filtered(
            lambda c: start_date <= c.end_date.astimezone(
                timezone(self.env.context.get('tz', 'UTC'))
            ).replace(tzinfo=None) < end_date
        )

        if vehicles_in:
            sheet.merge_range(row, 0, row, len(headers) - 1, 'Vehicles In', subtitle_format)

            row += 1

            for contract in vehicles_in:
                data = get_data(contract)

                sheet.write_row(row, 0, data, data_format)

                for col in range(len(headers)):
                    max_size[col] = max(max_size[col], len(data[col]))

                row += 1

        vehicles_out = self.env['vehicle.contract'].browse(contract_ids).filtered(
            lambda c: start_date <= c.start_date.astimezone(
                timezone(self.env.context.get('tz', 'UTC'))
            ).replace(tzinfo=None) < end_date
        )

        if vehicles_out:
            sheet.merge_range(row, 0, row, len(headers) - 1, 'Vehicles Out', subtitle_format)

            row += 1

            for contract in vehicles_out:
                data = get_data(contract)

                sheet.write_row(row, 0, data, data_format)

                for col in range(len(headers)):
                    max_size[col] = max(max_size[col], len(data[col]))

                row += 1

        for col in range(len(headers)):
            sheet.set_column(col, col, max_size[col])

        workbook.close()

        output.seek(0)
        response.stream.write(output.read())
        output.close()

        return output
