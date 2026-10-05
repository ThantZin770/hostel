from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AquaBatch(models.Model):
    _name = "aqua.batch"
    _description = "Aquaculture Biological Batch"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(string="Local Batch Number", tracking=True, copy=False)
    global_trace_id = fields.Many2one(
        "aqua.global.trace",
        required=True,
        index=True,
        tracking=True,
        ondelete="restrict",
    )
    global_bio_id = fields.Char(
        related="global_trace_id.name",
        store=True,
        readonly=True,
        string="Global Biological ID",
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        tracking=True,
        default=lambda self: self.env.company,
        index=True,
    )
    farm_id = fields.Many2one("aqua.farm", required=True, tracking=True)
    production_unit_id = fields.Many2one(
        "aqua.production.unit",
        required=True,
        tracking=True,
    )
    species_id = fields.Many2one("aqua.species", required=True, tracking=True)
    stage_id = fields.Many2one("aqua.stage", required=True, tracking=True)
    stage_type = fields.Selection(
        related="stage_id.stage_type",
        store=True,
        readonly=True,
    )
    previous_generation_batch_id = fields.Many2one(
        "aqua.batch",
        string="Previous-generation Source Batch",
        help="Optional reference when breeder stock came from an old grow-out batch.",
    )

    parent_relation_ids = fields.One2many(
        "aqua.batch.relation",
        "child_batch_id",
        string="Parent Relations",
    )
    child_relation_ids = fields.One2many(
        "aqua.batch.relation",
        "parent_batch_id",
        string="Child Relations",
    )
    event_ids = fields.One2many("aqua.batch.event", "batch_id")
    water_quality_ids = fields.One2many("aqua.water.quality", "batch_id")
    input_consumption_ids = fields.One2many("aqua.input.consumption", "batch_id")

    status = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("transferred", "Transferred"),
            ("completed", "Completed"),
            ("harvested", "Harvested"),
            ("quarantine", "Quarantine"),
            ("problem", "Problem"),
            ("closed", "Closed"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )
    start_date = fields.Date(default=fields.Date.today)
    end_date = fields.Date()
    quantity = fields.Float(tracking=True)
    avg_weight_g = fields.Float(string="Average Weight (g)", tracking=True)
    biomass_kg = fields.Float(compute="_compute_biomass", store=True)
    mortality_qty = fields.Float(tracking=True)
    mortality_rate = fields.Float(compute="_compute_mortality_rates", store=True)
    survival_rate = fields.Float(compute="_compute_mortality_rates", store=True)

    is_parallel = fields.Boolean()
    is_merged = fields.Boolean()
    is_split_child = fields.Boolean()
    problem_flag = fields.Boolean(tracking=True)
    problem_note = fields.Text()
    note = fields.Text()
    active = fields.Boolean(default=True)

    parent_count = fields.Integer(compute="_compute_trace_counts")
    child_count = fields.Integer(compute="_compute_trace_counts")
    event_count = fields.Integer(compute="_compute_trace_counts")
    water_quality_count = fields.Integer(compute="_compute_trace_counts")
    input_consumption_count = fields.Integer(compute="_compute_trace_counts")

    _name_company_uniq = models.Constraint(
        "unique(company_id, name)",
        "Local batch number must be unique inside the same company.",
    )

    @api.depends("quantity", "avg_weight_g")
    def _compute_biomass(self):
        for batch in self:
            batch.biomass_kg = batch.quantity * batch.avg_weight_g / 1000

    @api.depends("quantity", "mortality_qty")
    def _compute_mortality_rates(self):
        for batch in self:
            if batch.quantity > 0:
                batch.mortality_rate = batch.mortality_qty / batch.quantity * 100
                batch.survival_rate = max(100 - batch.mortality_rate, 0)
            else:
                batch.mortality_rate = 0
                batch.survival_rate = 0

    @api.depends(
        "parent_relation_ids",
        "child_relation_ids",
        "event_ids",
        "water_quality_ids",
        "input_consumption_ids",
    )
    def _compute_trace_counts(self):
        for batch in self:
            batch.parent_count = len(batch.parent_relation_ids)
            batch.child_count = len(batch.child_relation_ids)
            batch.event_count = len(batch.event_ids)
            batch.water_quality_count = len(batch.water_quality_ids)
            batch.input_consumption_count = len(batch.input_consumption_ids)

    @api.model_create_multi
    def create(self, vals_list):
        Stage = self.env["aqua.stage"]
        Trace = self.env["aqua.global.trace"]
        for vals in vals_list:
            stage = (
                Stage.browse(vals.get("stage_id")) if vals.get("stage_id") else Stage
            )
            species_id = vals.get("species_id")
            company_id = vals.get("company_id") or self.env.company.id

            if not vals.get("global_trace_id"):
                if stage and stage.stage_type == "breeder":
                    trace = Trace.create(
                        {
                            "species_id": species_id,
                            "origin_company_id": company_id,
                            "date_start": vals.get("start_date") or fields.Date.today(),
                        }
                    )
                    vals["global_trace_id"] = trace.id
                else:
                    raise ValidationError(
                        _(
                            "Please select an existing Global Biological ID or start the lifecycle from a Breeder batch."
                        )
                    )

            if not vals.get("name"):
                vals["name"] = self._next_local_batch_name(stage)

        batches = super().create(vals_list)
        for batch in batches:
            if (
                batch.stage_type == "breeder"
                and not batch.global_trace_id.origin_batch_id
            ):
                batch.global_trace_id.write({"origin_batch_id": batch.id})
            batch._create_event(
                "created",
                _("Created: %s") % batch.name,
                quantity=batch.quantity,
                weight=batch.avg_weight_g,
            )
        return batches

    def _next_local_batch_name(self, stage):
        year = fields.Date.context_today(self).year
        stage_code = stage.code if stage and stage.exists() and stage.code else "BATCH"
        sequence = self.env["ir.sequence"].next_by_code("aqua.batch.local") or "000001"
        return f"{stage_code}-{year}-{sequence}"

    def _create_event(
        self,
        event_type,
        name,
        quantity=0.0,
        weight=0.0,
        note=False,
        source_model=False,
        source_id=False,
    ):
        self.ensure_one()
        return self.env["aqua.batch.event"].create(
            {
                "name": name,
                "batch_id": self.id,
                "event_type": event_type,
                "quantity": quantity,
                "weight": weight,
                "operator_id": self.env.user.id,
                "note": note,
                "source_model": source_model,
                "source_id": source_id,
            }
        )

    @api.constrains("quantity", "avg_weight_g", "mortality_qty")
    def _check_non_negative_quantities(self):
        for batch in self:
            if batch.quantity < 0:
                raise ValidationError(_("Batch quantity cannot be negative."))
            if batch.avg_weight_g < 0:
                raise ValidationError(_("Average weight cannot be negative."))
            if batch.mortality_qty < 0:
                raise ValidationError(_("Mortality quantity cannot be negative."))
            if batch.quantity > 0 and batch.mortality_qty > batch.quantity:
                raise ValidationError(
                    _("Mortality quantity cannot exceed batch quantity.")
                )

    @api.constrains("company_id", "farm_id", "production_unit_id")
    def _check_location_company_consistency(self):
        for batch in self:
            if batch.farm_id.company_id != batch.company_id:
                raise ValidationError(
                    _("Batch farm must belong to the selected company.")
                )
            if batch.production_unit_id.farm_id != batch.farm_id:
                raise ValidationError(
                    _("Production unit must belong to the selected farm.")
                )
            if batch.production_unit_id.company_id != batch.company_id:
                raise ValidationError(
                    _("Production unit must belong to the selected company.")
                )

    @api.constrains("stage_id", "company_id")
    def _check_stage_company_type(self):
        for batch in self:
            company_type = batch.company_id.aqua_company_type
            if (
                batch.stage_id.company_type
                and batch.stage_id.company_type != "any"
                and company_type
                and batch.stage_id.company_type != company_type
            ):
                raise ValidationError(
                    _(
                        "Stage %(stage)s is configured for %(stage_company_type)s companies, but %(company)s is %(company_type)s."
                    )
                    % {
                        "stage": batch.stage_id.display_name,
                        "stage_company_type": batch.stage_id.company_type,
                        "company": batch.company_id.display_name,
                        "company_type": company_type,
                    }
                )

    @api.ondelete(at_uninstall=False)
    def _unlink_except_archive(self):
        raise UserError(_("Archive biological batches instead of deleting them."))

    def action_create_parallel_batch(self):
        self.ensure_one()
        return self._wizard_action(
            "aqua.batch.parallel.wizard",
            _("Create Parallel Batch"),
            {
                "default_parent_batch_id": self.id,
                "default_company_id": self.company_id.id,
                "default_farm_id": self.farm_id.id,
                "default_production_unit_id": self.production_unit_id.id,
                "default_quantity": self.quantity,
                "default_avg_weight_g": self.avg_weight_g,
            },
        )

    def action_split_batch(self):
        self.ensure_one()
        return self._wizard_action(
            "aqua.batch.split.wizard",
            _("Split Batch"),
            {"default_parent_batch_id": self.id},
        )

    def action_separate_batch(self):
        self.ensure_one()
        return self._wizard_action(
            "aqua.batch.separate.wizard",
            _("Separate Batch"),
            {"default_parent_batch_id": self.id},
        )

    def action_merge_batches(self):
        batches = self
        if not batches and self.env.context.get("active_ids"):
            batches = self.browse(self.env.context["active_ids"])
        if not batches:
            raise UserError(_("Select at least two batches to merge."))
        first = batches[0]
        return self._wizard_action(
            "aqua.batch.merge.wizard",
            _("Merge Batches"),
            {
                "default_parent_batch_ids": [(6, 0, batches.ids)],
                "default_target_company_id": first.company_id.id,
                "default_target_farm_id": first.farm_id.id,
                "default_target_production_unit_id": first.production_unit_id.id,
                "default_target_stage_id": first.stage_id.id,
                "default_quantity": sum(batches.mapped("quantity")),
                "default_avg_weight_g": first.avg_weight_g,
            },
        )

    def action_transfer_stage(self):
        self.ensure_one()
        return self._wizard_action(
            "aqua.batch.transfer.wizard",
            _("Transfer Stage"),
            {
                "default_parent_batch_id": self.id,
                "default_target_company_id": self.company_id.id,
                "default_target_farm_id": self.farm_id.id,
                "default_target_production_unit_id": self.production_unit_id.id,
                "default_quantity": self.quantity,
                "default_avg_weight_g": self.avg_weight_g,
            },
        )

    def _wizard_action(self, res_model, title, context):
        return {
            "type": "ir.actions.act_window",
            "name": title,
            "res_model": res_model,
            "view_mode": "form",
            "target": "new",
            "context": context,
        }

    def action_open_upstream_trace(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Parent Batches"),
            "res_model": "aqua.batch.relation",
            "view_mode": "list,form",
            "domain": [("child_batch_id", "=", self.id)],
            "context": {"default_child_batch_id": self.id},
        }

    def action_open_downstream_trace(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Child Batches"),
            "res_model": "aqua.batch.relation",
            "view_mode": "list,form",
            "domain": [("parent_batch_id", "=", self.id)],
            "context": {"default_parent_batch_id": self.id},
        }

    def action_open_global_trace(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Global Biological ID"),
            "res_model": "aqua.global.trace",
            "view_mode": "form",
            "res_id": self.global_trace_id.id,
        }

    def action_open_events(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Batch Events"),
            "res_model": "aqua.batch.event",
            "view_mode": "list,form",
            "domain": [("batch_id", "=", self.id)],
            "context": {"default_batch_id": self.id},
        }

    def action_open_water_quality(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Water Quality"),
            "res_model": "aqua.water.quality",
            "view_mode": "list,form",
            "domain": [("batch_id", "=", self.id)],
            "context": {"default_batch_id": self.id},
        }

    def action_open_input_consumption(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Input Consumption"),
            "res_model": "aqua.input.consumption",
            "view_mode": "list,form",
            "domain": [("batch_id", "=", self.id)],
            "context": {"default_batch_id": self.id},
        }
