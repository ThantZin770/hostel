from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AquaWaterQuality(models.Model):
    _name = "aqua.water.quality"
    _description = "Aquaculture Water Quality"
    _order = "check_date desc, id desc"

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
    check_date = fields.Datetime(default=fields.Datetime.now)
    temperature_c = fields.Float(string="Temperature (C)")
    ph = fields.Float(string="pH")
    dissolved_oxygen = fields.Float()
    salinity_ppt = fields.Float(string="Salinity (ppt)")
    ammonia = fields.Float()
    nitrite = fields.Float()
    alkalinity = fields.Float()
    note = fields.Text()
    checked_by_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    @api.depends("batch_id", "production_unit_id", "check_date")
    def _compute_name(self):
        for record in self:
            record.name = _("%(batch)s Water Quality") % {
                "batch": record.batch_id.name or _("Batch"),
            }

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record.batch_id._create_event(
                "water_quality",
                _("Water Quality: %s") % record.batch_id.name,
                note=record.note,
                source_model=record._name,
                source_id=record.id,
            )
        return records

    @api.constrains(
        "temperature_c",
        "ph",
        "dissolved_oxygen",
        "salinity_ppt",
        "ammonia",
        "nitrite",
        "alkalinity",
    )
    def _check_values(self):
        non_negative_fields = [
            "temperature_c",
            "dissolved_oxygen",
            "salinity_ppt",
            "ammonia",
            "nitrite",
            "alkalinity",
        ]
        for record in self:
            if record.ph and not 0 <= record.ph <= 14:
                raise ValidationError(_("pH must be between 0 and 14."))
            for field_name in non_negative_fields:
                if record[field_name] < 0:
                    raise ValidationError(
                        _("%s cannot be negative.") % record._fields[field_name].string
                    )

    @api.ondelete(at_uninstall=False)
    def _unlink_except_archive(self):
        raise UserError(_("Archive water quality records instead of deleting them."))
