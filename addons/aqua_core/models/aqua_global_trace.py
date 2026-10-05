from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AquaGlobalTrace(models.Model):
    _name = "aqua.global.trace"
    _description = "Global Biological Traceability ID"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default=lambda self: _("New"),
    )
    species_id = fields.Many2one("aqua.species", required=True, tracking=True)
    origin_company_id = fields.Many2one("res.company", tracking=True)
    origin_batch_id = fields.Many2one("aqua.batch", tracking=True)
    batch_ids = fields.One2many("aqua.batch", "global_trace_id")
    source_global_trace_ids = fields.Many2many(
        "aqua.global.trace",
        "aqua_global_trace_source_rel",
        "trace_id",
        "source_trace_id",
        string="Source Global IDs",
        help="Preserves source IDs when an Aquaculture Manager approves a cross-global merge.",
    )
    status = fields.Selection(
        [
            ("active", "Active"),
            ("completed", "Completed"),
            ("problem", "Problem"),
            ("closed", "Closed"),
        ],
        default="active",
        required=True,
        tracking=True,
    )
    date_start = fields.Date(default=fields.Date.today)
    date_end = fields.Date()
    active = fields.Boolean(default=True)
    note = fields.Text()

    batch_count = fields.Integer(compute="_compute_trace_counts")
    event_count = fields.Integer(compute="_compute_trace_counts")
    relation_count = fields.Integer(compute="_compute_trace_counts")

    _name_uniq = models.Constraint(
        "unique(name)",
        "Global Biological ID must be unique.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "aqua.global.trace"
                ) or _("New")
        return super().create(vals_list)

    @api.depends(
        "batch_ids",
        "batch_ids.event_ids",
        "batch_ids.parent_relation_ids",
        "batch_ids.child_relation_ids",
    )
    def _compute_trace_counts(self):
        Event = self.env["aqua.batch.event"]
        Relation = self.env["aqua.batch.relation"]
        for trace in self:
            trace.batch_count = len(trace.batch_ids)
            trace.event_count = Event.search_count([("global_trace_id", "=", trace.id)])
            trace.relation_count = Relation.search_count(
                [("global_trace_id", "=", trace.id)]
            )

    @api.ondelete(at_uninstall=False)
    def _unlink_except_archive(self):
        raise UserError(
            _("Archive global traceability records instead of deleting them.")
        )

    def action_open_batches(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Batches"),
            "res_model": "aqua.batch",
            "view_mode": "list,form",
            "domain": [("global_trace_id", "=", self.id)],
            "context": {"default_global_trace_id": self.id},
        }

    def action_open_events(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Batch Events"),
            "res_model": "aqua.batch.event",
            "view_mode": "list,form",
            "domain": [("global_trace_id", "=", self.id)],
        }

    def action_open_relations(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Batch Relations"),
            "res_model": "aqua.batch.relation",
            "view_mode": "list,form",
            "domain": [("global_trace_id", "=", self.id)],
        }
