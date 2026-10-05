from odoo import _, fields, models
from odoo.exceptions import ValidationError


class AquaBatchTransferWizard(models.TransientModel):
    _name = "aqua.batch.transfer.wizard"
    _description = "Transfer Aquaculture Batch Stage"

    parent_batch_id = fields.Many2one("aqua.batch", required=True)
    target_company_id = fields.Many2one("res.company", required=True)
    target_farm_id = fields.Many2one("aqua.farm", required=True)
    target_production_unit_id = fields.Many2one("aqua.production.unit", required=True)
    target_stage_id = fields.Many2one("aqua.stage", required=True)
    quantity = fields.Float()
    avg_weight_g = fields.Float(string="Average Weight (g)")
    note = fields.Text()

    def action_confirm(self):
        self.ensure_one()
        parent = self.parent_batch_id
        quantity = self.quantity or parent.quantity
        avg_weight_g = self.avg_weight_g or parent.avg_weight_g
        if quantity < 0 or avg_weight_g < 0:
            raise ValidationError(_("Quantity and average weight cannot be negative."))

        child = self.env["aqua.batch"].create(
            {
                "global_trace_id": parent.global_trace_id.id,
                "company_id": self.target_company_id.id,
                "farm_id": self.target_farm_id.id,
                "production_unit_id": self.target_production_unit_id.id,
                "species_id": parent.species_id.id,
                "stage_id": self.target_stage_id.id,
                "quantity": quantity,
                "avg_weight_g": avg_weight_g,
                "status": "active",
                "note": self.note,
            }
        )
        self.env["aqua.batch.relation"].create(
            {
                "parent_batch_id": parent.id,
                "child_batch_id": child.id,
                "operation_type": "stage_transfer",
                "quantity": quantity,
                "note": self.note,
            }
        )
        if parent.quantity and quantity >= parent.quantity:
            parent.status = "transferred"
        parent._create_event(
            "transfer",
            _("Transferred to %s") % child.name,
            quantity=quantity,
            weight=avg_weight_g,
            note=self.note,
        )
        return {"type": "ir.actions.act_window_close"}
