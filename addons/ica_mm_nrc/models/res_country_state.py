from odoo import fields, models


class ResCountryState(models.Model):
    _inherit = "res.country.state"

    code = fields.Char(string="Code", translate=False)
    township_ids = fields.Many2one("res.country.state.township")
