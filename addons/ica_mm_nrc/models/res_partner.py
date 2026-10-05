from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    state_code = fields.Char(related="state_id.code")
    township_id = fields.Many2one("res.country.state.township")
    township_code = fields.Char(related="township_id.code")
    nrc_number = fields.Char(required=False, string="NRC Number")
