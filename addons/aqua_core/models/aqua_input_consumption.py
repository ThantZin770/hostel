from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AquaInputConsumption(models.Model):
    _name = "aqua.input.consumption"
    _description = "Aquaculture Input Consumption"
    _order = "consume_date desc, id desc"

    name = fields.Char(compute="_compute_name", store=True)
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
    consume_date = fields.Datetime(default=fields.Datetime.now)
    product_id = fields.Many2one("product.product")
    input_type = fields.Selection(
        [
            ("feed", "Feed"),
            ("medicine", "Medicine"),
            ("chemical", "Chemical"),
            ("probiotic", "Probiotic"),
            ("fertilizer", "Fertilizer"),
            ("other", "Other"),
        ],
        required=True,
        default="feed",
    )
    quantity = fields.Float()
    note = fields.Text()
    used_by_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    @api.depends("batch_id", "product_id", "input_type", "consume_date")
    def _compute_name(self):
        for record in self:
            input_label = dict(record._fields["input_type"].selection).get(
                record.input_type, _("Input")
            )
            product = (
                record.product_id.display_name if record.product_id else input_label
            )
            record.name = _("%(batch)s - %(product)s") % {
                "batch": record.batch_id.name or _("Batch"),
                "product": product,
            }

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            event_type = "note"
            if record.input_type == "feed":
                event_type = "feeding"
            elif record.input_type in ("medicine", "chemical", "probiotic"):
                event_type = "treatment"
            record.batch_id._create_event(
                event_type,
                _("Input Consumption: %s")
                % (record.product_id.display_name or record.input_type),
                quantity=record.quantity,
                note=record.note,
                source_model=record._name,
                source_id=record.id,
            )
        return records

    @api.constrains("quantity")
    def _check_quantity(self):
        for record in self:
            if record.quantity < 0:
                raise ValidationError(
                    _("Input consumption quantity cannot be negative.")
                )

    @api.ondelete(at_uninstall=False)
    def _unlink_except_archive(self):
        raise UserError(
            _("Archive input consumption records instead of deleting them.")
        )
