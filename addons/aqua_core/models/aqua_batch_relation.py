from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AquaBatchRelation(models.Model):
    _name = "aqua.batch.relation"
    _description = "Aquaculture Batch Relation"
    _order = "operation_date desc, id desc"

    name = fields.Char(compute="_compute_name", store=True)
    global_trace_id = fields.Many2one(
        "aqua.global.trace",
        required=True,
        index=True,
        ondelete="restrict",
    )
    parent_batch_id = fields.Many2one(
        "aqua.batch",
        required=True,
        index=True,
        ondelete="restrict",
    )
    child_batch_id = fields.Many2one(
        "aqua.batch",
        required=True,
        index=True,
        ondelete="restrict",
    )
    operation_type = fields.Selection(
        [
            ("created", "Created"),
            ("parallel", "Parallel"),
            ("split", "Split"),
            ("separate", "Separate"),
            ("merge", "Merge"),
            ("stage_transfer", "Stage Transfer"),
            ("harvest", "Harvest"),
            ("adjustment", "Adjustment"),
        ],
        required=True,
        default="stage_transfer",
    )
    operation_date = fields.Datetime(default=fields.Datetime.now)
    from_company_id = fields.Many2one("res.company")
    to_company_id = fields.Many2one("res.company")
    from_stage_id = fields.Many2one("aqua.stage")
    to_stage_id = fields.Many2one("aqua.stage")
    quantity = fields.Float()
    note = fields.Text()
    active = fields.Boolean(default=True)

    @api.depends("operation_type", "parent_batch_id", "child_batch_id")
    def _compute_name(self):
        for relation in self:
            parent = relation.parent_batch_id.name or _("Parent")
            child = relation.child_batch_id.name or _("Child")
            operation = dict(relation._fields["operation_type"].selection).get(
                relation.operation_type,
                relation.operation_type or _("Relation"),
            )
            relation.name = _("%(operation)s: %(parent)s -> %(child)s") % {
                "operation": operation,
                "parent": parent,
                "child": child,
            }

    @api.model_create_multi
    def create(self, vals_list):
        Batch = self.env["aqua.batch"]
        for vals in vals_list:
            parent = (
                Batch.browse(vals.get("parent_batch_id"))
                if vals.get("parent_batch_id")
                else Batch
            )
            child = (
                Batch.browse(vals.get("child_batch_id"))
                if vals.get("child_batch_id")
                else Batch
            )

            vals.setdefault(
                "global_trace_id", (child.global_trace_id or parent.global_trace_id).id
            )
            vals.setdefault("from_company_id", parent.company_id.id)
            vals.setdefault("to_company_id", child.company_id.id)
            vals.setdefault("from_stage_id", parent.stage_id.id)
            vals.setdefault("to_stage_id", child.stage_id.id)
        relations = super().create(vals_list)
        for relation in relations:
            event_type = {
                "created": "created",
                "parallel": "note",
                "split": "split",
                "separate": "separate",
                "merge": "merge",
                "stage_transfer": "transfer",
                "harvest": "harvest",
                "adjustment": "note",
            }[relation.operation_type]
            relation.child_batch_id._create_event(
                event_type,
                relation.name,
                quantity=relation.quantity,
                note=relation.note,
                source_model=relation._name,
                source_id=relation.id,
            )
        return relations

    @api.constrains("parent_batch_id", "child_batch_id")
    def _check_parent_child(self):
        for relation in self:
            if relation.parent_batch_id == relation.child_batch_id:
                raise ValidationError(
                    _("Parent batch and child batch cannot be the same.")
                )

    @api.constrains("quantity")
    def _check_quantity(self):
        for relation in self:
            if relation.quantity < 0:
                raise ValidationError(_("Relation quantity cannot be negative."))

    @api.constrains(
        "global_trace_id", "parent_batch_id", "child_batch_id", "operation_type"
    )
    def _check_global_trace_consistency(self):
        for relation in self:
            parent_trace = relation.parent_batch_id.global_trace_id
            child_trace = relation.child_batch_id.global_trace_id
            if parent_trace == child_trace:
                if relation.global_trace_id not in (parent_trace, child_trace):
                    raise ValidationError(
                        _(
                            "Relation Global Biological ID must match the linked batches."
                        )
                    )
                continue

            approved_cross_merge = (
                relation.operation_type == "merge"
                and self.env.user.has_group("aqua_core.group_aqua_manager")
                and parent_trace in relation.global_trace_id.source_global_trace_ids
                and child_trace == relation.global_trace_id
            )
            if not approved_cross_merge:
                raise ValidationError(
                    _(
                        "Parent and child batches must share the same Global Biological ID unless a manager-approved cross-global merge is used."
                    )
                )

    @api.constrains(
        "from_company_id", "to_company_id", "parent_batch_id", "child_batch_id"
    )
    def _check_company_consistency(self):
        for relation in self:
            if (
                relation.from_company_id
                and relation.from_company_id != relation.parent_batch_id.company_id
            ):
                raise ValidationError(
                    _("From Company must match the parent batch company.")
                )
            if (
                relation.to_company_id
                and relation.to_company_id != relation.child_batch_id.company_id
            ):
                raise ValidationError(
                    _("To Company must match the child batch company.")
                )

    @api.ondelete(at_uninstall=False)
    def _unlink_except_archive(self):
        raise UserError(_("Archive batch relations instead of deleting them."))
