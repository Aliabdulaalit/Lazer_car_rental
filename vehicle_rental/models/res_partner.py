from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _


class Contacts(models.Model):
    _inherit = 'res.partner'
    _description = __doc__

    work_name = fields.Char(string="Work Name")
    residence_address = fields.Char(string="Residence Address")
    card_number = fields.Char(string="Card Number")
    card_holder_name = fields.Char(string="Card Holder Name")
    card_expiration_date = fields.Date(string="Card Expiration Date")
    driving_license_no = fields.Char(string="Driving License No.")
    cpr = fields.Char(string="CPR")
    issued_place = fields.Many2one("res.country", string="Issued Place")
    nationality = fields.Many2one("res.country", string="Nationality")
    expiry_date = fields.Date(string="Expiry Date")
    blacklist = fields.Boolean(string="Blacklist", tracking=1, store=1)

    _sql_constraints = [
        ('driving_license_no_uniq', 'unique (driving_license_no)', """Driving License No Already Exist"""),
        ('cpr_uniq', 'unique (cpr)', """CPR Already Exist"""),
        ('card_number_uniq', 'unique (card_number)', """Card Number Already Exist"""),
    ]

    def action_block_customer(self):
        for rec in self:
            rec.blacklist = True

    def action_unblock_customer(self):
        for rec in self:
            rec.blacklist = False


