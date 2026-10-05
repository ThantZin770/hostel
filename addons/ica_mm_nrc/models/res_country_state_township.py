from odoo import fields, models


class ResCountryStateTownship(models.Model):
    _name = "res.country.state.township"
    _description = "IcaMmTownship"

    name = fields.Char(string="Name", required=True, translate=True)
    code = fields.Char(string="Code", required=True, translate=True)
    state_id = fields.Many2one("res.country.state")
