from odoo import _, fields, models
from odoo.exceptions import ValidationError


class AquaBatchParallelWizard(models.TransientModel):
    _name = "aqua.batch.parallel.wizard"
    _description = "Create Parallel Aquaculture Batch"

    parent_batch_id = fields.Many2one("aqua.batch", required=True)
    company_id = fields.Many2one("res.company", required=True)
    farm_id = fields.Many2one("aqua.farm", required=True)
    production_unit_id = fields.Many2one("aqua.production.unit", required=True)
    quantity = fields.Float()
    avg_weight_g = fields.Float(string="Average Weight (g)")
    note = fields.Text()

    def action_confirm(self):
        self.ensure_one()
        if self.quantity < 0 or self.avg_weight_g < 0:
            raise ValidationError(_("Quantity and average weight cannot be negative."))

        parent = self.parent_batch_id
        child = self.env["aqua.batch"].create(
            {
                "global_trace_id": parent.global_trace_id.id,
                "company_id": self.company_id.id,
                "farm_id": self.farm_id.id,
                "production_unit_id": self.production_unit_id.id,
                "species_id": parent.species_id.id,
                "stage_id": parent.stage_id.id,
                "quantity": self.quantity,
                "avg_weight_g": self.avg_weight_g,
                "is_parallel": True,
                "status": "active",
                "note": self.note,
            }
        )
        self.env["aqua.batch.relation"].create(
            {
                "parent_batch_id": parent.id,
                "child_batch_id": child.id,
                "operation_type": "parallel",
                "quantity": self.quantity,
                "note": self.note,
            }
        )
        parent._create_event(
            "note",
            _("Parallel batch created: %s") % child.name,
            quantity=self.quantity,
            note=self.note,
        )
        return {"type": "ir.actions.act_window_close"}
