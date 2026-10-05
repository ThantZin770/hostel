from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AquaStage(models.Model):
    _name = "aqua.stage"
    _description = "Aquaculture Lifecycle Stage"
    _order = "sequence, name"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    company_type = fields.Selection(
        [
            ("breeder", "Breeder Company"),
            ("hatchery", "Hatchery Company"),
            ("nursery", "Nursery Company"),
            ("growout", "Grow-out Company"),
            ("harvest_sales", "Harvest & Sales Company"),
            ("any", "Any Company"),
        ],
        required=True,
        default="any",
    )
    stage_type = fields.Selection(
        [
            ("breeder", "Breeder"),
            ("broodstock", "Broodstock"),
            ("spawning", "Spawning"),
            ("egg", "Egg"),
            ("larvae", "Larvae"),
            ("nursery1", "Nursery 1"),
            ("nursery2", "Nursery 2"),
            ("nursery3", "Nursery 3"),
            ("growout", "Grow-out"),
            ("harvest", "Harvest"),
        ],
        required=True,
    )
    active = fields.Boolean(default=True)
    note = fields.Text()

    _code_uniq = models.Constraint(
        "unique(code)",
        "Lifecycle stage code must be unique.",
    )

    @api.constrains("sequence")
    def _check_sequence_positive(self):
        for stage in self:
            if stage.sequence <= 0:
                raise ValidationError(_("Lifecycle stage sequence must be positive."))
