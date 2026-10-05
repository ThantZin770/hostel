from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AquaBatchEvent(models.Model):
    _name = "aqua.batch.event"
    _description = "Aquaculture Batch Event"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "event_date desc, id desc"

    name = fields.Char(required=True, default=lambda self: _("Batch Event"))
    batch_id = fields.Many2one(
        "aqua.batch",
        required=True,
        index=True,
        ondelete="restrict",
    )
    global_trace_id = fields.Many2one(
        "aqua.global.trace",
        related="batch_id.global_trace_id",
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company",
        related="batch_id.company_id",
        store=True,
        readonly=True,
    )
    farm_id = fields.Many2one(
        "aqua.farm",
        related="batch_id.farm_id",
        store=True,
        readonly=True,
    )
    production_unit_id = fields.Many2one(
        "aqua.production.unit",
        related="batch_id.production_unit_id",
        store=True,
        readonly=True,
    )
    stage_id = fields.Many2one(
        "aqua.stage",
        related="batch_id.stage_id",
        store=True,
        readonly=True,
    )
    event_type = fields.Selection(
        [
            ("created", "Created"),
            ("feeding", "Feeding"),
            ("mortality", "Mortality"),
            ("grading", "Grading"),
            ("transfer", "Transfer"),
            ("split", "Split"),
            ("separate", "Separate"),
            ("merge", "Merge"),
            ("health", "Health"),
            ("treatment", "Treatment"),
            ("water_quality", "Water Quality"),
            ("harvest", "Harvest"),
            ("problem", "Problem"),
            ("note", "Note"),
        ],
        required=True,
        default="note",
    )
    event_date = fields.Datetime(default=fields.Datetime.now)
    quantity = fields.Float()
    weight = fields.Float()
    operator_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    note = fields.Text()
    source_model = fields.Char()
    source_id = fields.Integer()
    active = fields.Boolean(default=True)

    @api.constrains("quantity", "weight")
    def _check_non_negative(self):
        for event in self:
            if event.quantity < 0:
                raise ValidationError(_("Event quantity cannot be negative."))
            if event.weight < 0:
                raise ValidationError(_("Event weight cannot be negative."))

    @api.ondelete(at_uninstall=False)
    def _unlink_except_archive(self):
        raise UserError(_("Archive batch events instead of deleting them."))
