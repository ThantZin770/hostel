from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AquaBatchSplitWizard(models.TransientModel):
    _name = "aqua.batch.split.wizard"
    _description = "Split Aquaculture Batch"

    parent_batch_id = fields.Many2one("aqua.batch", required=True)
    line_ids = fields.One2many("aqua.batch.split.wizard.line", "wizard_id")
    note = fields.Text()

    def action_confirm(self):
        self.ensure_one()
        parent = self.parent_batch_id
        if not self.line_ids:
            raise ValidationError(_("Add at least one split line."))
        total_quantity = sum(self.line_ids.mapped("quantity"))
        if (
            parent.quantity
            and total_quantity > parent.quantity
            and not self.env.user.has_group("aqua_core.group_aqua_manager")
        ):
            raise ValidationError(
                _("Total split quantity cannot exceed parent quantity.")
            )

        children = self.env["aqua.batch"]
        for line in self.line_ids:
            line._check_values()
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
                    "is_split_child": True,
                    "status": "active",
                    "note": line.note or self.note,
                }
            )
            self.env["aqua.batch.relation"].create(
                {
                    "parent_batch_id": parent.id,
                    "child_batch_id": child.id,
                    "operation_type": "split",
                    "quantity": line.quantity,
                    "note": line.note or self.note,
                }
            )
            children |= child

        parent._create_event(
            "split",
            _("Batch split into %s child batches") % len(children),
            quantity=total_quantity,
            note=self.note,
        )
        return {"type": "ir.actions.act_window_close"}


class AquaBatchSplitWizardLine(models.TransientModel):
    _name = "aqua.batch.split.wizard.line"
    _description = "Split Aquaculture Batch Line"

    wizard_id = fields.Many2one(
        "aqua.batch.split.wizard", required=True, ondelete="cascade"
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
    note = fields.Text()

    @api.constrains("quantity", "avg_weight_g")
    def _check_values(self):
        for line in self:
            if line.quantity < 0:
                raise ValidationError(_("Split quantity cannot be negative."))
            if line.avg_weight_g < 0:
                raise ValidationError(_("Average weight cannot be negative."))
