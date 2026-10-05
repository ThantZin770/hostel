from odoo import fields, models


class AquaFarm(models.Model):
    _name = "aqua.farm"
    _description = "Aquaculture Farm / Site"
    _order = "company_id, name"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    location = fields.Char()
    address = fields.Text()
    latitude = fields.Float()
    longitude = fields.Float()
    active = fields.Boolean(default=True)
    note = fields.Text()

    _code_company_uniq = models.Constraint(
        "unique(company_id, code)",
        "Farm code must be unique per company.",
    )
