from odoo import _, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class AquaBatchMergeWizard(models.TransientModel):
    _name = "aqua.batch.merge.wizard"
    _description = "Merge Aquaculture Batches"

    parent_batch_ids = fields.Many2many("aqua.batch", required=True)
    target_company_id = fields.Many2one("res.company", required=True)
    target_farm_id = fields.Many2one("aqua.farm", required=True)
    target_production_unit_id = fields.Many2one("aqua.production.unit", required=True)
    target_stage_id = fields.Many2one("aqua.stage", required=True)
    quantity = fields.Float()
    avg_weight_g = fields.Float(string="Average Weight (g)")
    allow_cross_global_merge = fields.Boolean()
    note = fields.Text()

    def action_confirm(self):
        self.ensure_one()
        parents = self.parent_batch_ids
        if len(parents) < 2:
            raise ValidationError(_("Select at least two parent batches to merge."))
        if len(parents.mapped("species_id")) != 1:
            raise ValidationError(_("All merged batches must have the same species."))
        if self.quantity < 0 or self.avg_weight_g < 0:
            raise ValidationError(_("Quantity and average weight cannot be negative."))

        source_traces = parents.mapped("global_trace_id")
        if len(source_traces) == 1:
            target_trace = source_traces
        else:
            if not self.env.user.has_group("aqua_core.group_aqua_manager"):
                raise AccessError(
                    _(
                        "Only an Aquaculture Manager can merge batches from different Global Biological IDs."
                    )
                )
            if not self.allow_cross_global_merge:
                raise UserError(
                    _(
                        "Enable Cross-global Merge Override to merge different Global Biological IDs."
                    )
                )
            target_trace = self.env["aqua.global.trace"].create(
                {
                    "species_id": parents[0].species_id.id,
                    "origin_company_id": self.target_company_id.id,
                    "source_global_trace_ids": [(6, 0, source_traces.ids)],
                    "note": self.note,
                }
            )

        child = self.env["aqua.batch"].create(
            {
                "global_trace_id": target_trace.id,
                "company_id": self.target_company_id.id,
                "farm_id": self.target_farm_id.id,
                "production_unit_id": self.target_production_unit_id.id,
                "species_id": parents[0].species_id.id,
                "stage_id": self.target_stage_id.id,
                "quantity": self.quantity,
                "avg_weight_g": self.avg_weight_g,
                "is_merged": True,
                "status": "active",
                "note": self.note,
            }
        )

        for parent in parents:
            self.env["aqua.batch.relation"].create(
                {
                    "global_trace_id": target_trace.id,
                    "parent_batch_id": parent.id,
                    "child_batch_id": child.id,
                    "operation_type": "merge",
                    "quantity": parent.quantity,
                    "note": self.note,
                }
            )
            parent._create_event(
                "merge",
                _("Merged into %s") % child.name,
                quantity=parent.quantity,
                note=self.note,
            )
        return {"type": "ir.actions.act_window_close"}
