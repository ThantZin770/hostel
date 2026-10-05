from odoo import fields, models


class AquaSpecies(models.Model):
    _name = "aqua.species"
    _description = "Aquaculture Species"
    _order = "name"

    name = fields.Char(required=True)
    scientific_name = fields.Char()
    category = fields.Selection(
        [
            ("fish", "Fish"),
            ("shrimp", "Shrimp"),
            ("crab", "Crab"),
            ("mollusk", "Mollusk"),
            ("other", "Other"),
        ],
        default="fish",
    )
    active = fields.Boolean(default=True)
    note = fields.Text()

    _name_uniq = models.Constraint(
        "unique(name)",
        "Species name must be unique.",
    )
