from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AquaBatchSeparateWizard(models.TransientModel):
    _name = "aqua.batch.separate.wizard"
    _description = "Separate Aquaculture Batch"

    parent_batch_id = fields.Many2one("aqua.batch", required=True)
    line_ids = fields.One2many("aqua.batch.separate.wizard.line", "wizard_id")
    note = fields.Text()

    def action_confirm(self):
        self.ensure_one()
        parent = self.parent_batch_id
        if not self.line_ids:
            raise ValidationError(_("Add at least one separation line."))
        total_quantity = sum(self.line_ids.mapped("quantity"))
        if (
            parent.quantity
            and total_quantity > parent.quantity
            and not self.env.user.has_group("aqua_core.group_aqua_manager")
        ):
            raise ValidationError(
                _("Total separated quantity cannot exceed parent quantity.")
            )

        children = self.env["aqua.batch"]
        for line in self.line_ids:
            line._check_values()
            reason = dict(line._fields["separation_reason"].selection).get(
                line.separation_reason
            )
            note = " - ".join(part for part in [reason, line.note or self.note] if part)
            child = self.env["aqua.batch"].create(
                {
                    "global_trace_id": parent.global_trace_id.id,
                    "company_id": line.company_id.id,
                    "farm_id": line.farm_id.id,
                    "production_unit_id": line.production_unit_id.id,
                    "species_id": parent.species_id.id,
                    "stage_id": (line.target_stage_id or parent.stage_id).id,
                    "quantity": line.quantity,
                    "avg_weight_g": line.avg_weight_g,
                    "status": "active",
                    "note": note,
                }
            )
            self.env["aqua.batch.relation"].create(
                {
                    "parent_batch_id": parent.id,
                    "child_batch_id": child.id,
                    "operation_type": "separate",
                    "quantity": line.quantity,
                    "note": note,
                }
            )
            children |= child

        parent._create_event(
            "separate",
            _("Batch separated into %s child batches") % len(children),
            quantity=total_quantity,
            note=self.note,
        )
        return {"type": "ir.actions.act_window_close"}


class AquaBatchSeparateWizardLine(models.TransientModel):
    _name = "aqua.batch.separate.wizard.line"
    _description = "Separate Aquaculture Batch Line"

    wizard_id = fields.Many2one(
        "aqua.batch.separate.wizard", required=True, ondelete="cascade"
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    farm_id = fields.Many2one("aqua.farm", required=True)
    production_unit_id = fields.Many2one("aqua.production.unit", required=True)
    target_stage_id = fields.Many2one("aqua.stage")
    quantity = fields.Float()
    avg_weight_g = fields.Float(string="Average Weight (g)")
    separation_reason = fields.Selection(
        [
            ("size", "Size"),
            ("quality", "Quality"),
            ("health", "Health"),
            ("gender", "Gender"),
            ("location", "Location"),
            ("other", "Other"),
        ],
        required=True,
        default="size",
    )
    note = fields.Text()

    @api.constrains("quantity", "avg_weight_g")
    def _check_values(self):
        for line in self:
            if line.quantity < 0:
                raise ValidationError(_("Separated quantity cannot be negative."))
            if line.avg_weight_g < 0:
                raise ValidationError(_("Average weight cannot be negative."))
