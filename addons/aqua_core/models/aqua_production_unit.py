from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AquaProductionUnit(models.Model):
    _name = "aqua.production.unit"
    _description = "Aquaculture Production Unit"
    _order = "company_id, farm_id, code"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    farm_id = fields.Many2one("aqua.farm", required=True, index=True)
    company_id = fields.Many2one(
        "res.company",
        related="farm_id.company_id",
        store=True,
        readonly=True,
        index=True,
    )
    unit_type = fields.Selection(
        [
            ("pond", "Pond"),
            ("tank", "Tank"),
            ("cage", "Cage"),
            ("hapa", "Hapa"),
            ("nursery_area", "Nursery Area"),
            ("broodstock_tank", "Broodstock Tank"),
            ("spawning_tank", "Spawning Tank"),
            ("egg_incubation", "Egg Incubation Area"),
            ("larvae_tank", "Larvae Tank"),
            ("processing_area", "Processing Area"),
            ("warehouse_area", "Warehouse Area"),
            ("other", "Other"),
        ],
        required=True,
        default="pond",
    )
    capacity = fields.Float()
    water_type = fields.Selection(
        [
            ("freshwater", "Freshwater"),
            ("brackish", "Brackish"),
            ("seawater", "Seawater"),
            ("mixed", "Mixed"),
        ],
    )
    active = fields.Boolean(default=True)
    note = fields.Text()
    batch_ids = fields.One2many(
        "aqua.batch",
        "production_unit_id",
        string="Batch History",
    )
    current_batch_ids = fields.Many2many(
        "aqua.batch",
        compute="_compute_current_batch_ids",
        string="Current Batches",
    )
    batch_count = fields.Integer(compute="_compute_batch_metrics", store=True)
    current_batch_count = fields.Integer(compute="_compute_batch_metrics", store=True)
    current_state = fields.Selection(
        [
            ("empty", "Empty"),
            ("occupied", "Occupied"),
            ("quarantine", "Quarantine"),
            ("problem", "Problem"),
            ("harvested", "Harvested"),
        ],
        compute="_compute_batch_metrics",
        store=True,
        string="Current State",
    )
    current_quantity = fields.Float(compute="_compute_batch_metrics", store=True)
    current_biomass_kg = fields.Float(compute="_compute_batch_metrics", store=True)

    _code_farm_uniq = models.Constraint(
        "unique(farm_id, code)",
        "Production unit code must be unique per farm.",
    )

    @api.constrains("capacity")
    def _check_capacity_non_negative(self):
        for unit in self:
            if unit.capacity < 0:
                negative_str = _("Production unit capacity cannot be negative.")
                raise ValidationError(negative_str)

    @api.depends(
        "batch_ids",
        "batch_ids.active",
        "batch_ids.status",
        "batch_ids.quantity",
        "batch_ids.biomass_kg",
        "batch_ids.problem_flag",
    )
    def _get_current_batches(self):
        self.ensure_one()
        return self.batch_ids.filtered(
            lambda batch: (
                batch.active
                and batch.status not in ("transferred", "completed", "closed")
            )
        )

    @api.depends(
        "batch_ids",
        "batch_ids.active",
        "batch_ids.status",
        "batch_ids.quantity",
        "batch_ids.biomass_kg",
        "batch_ids.problem_flag",
    )
    def _compute_current_batch_ids(self):
        for unit in self:
            unit.current_batch_ids = unit._get_current_batches()

    @api.depends(
        "batch_ids",
        "batch_ids.active",
        "batch_ids.status",
        "batch_ids.quantity",
        "batch_ids.biomass_kg",
        "batch_ids.problem_flag",
    )
    def _compute_batch_metrics(self):
        for unit in self:
            current_batches = unit._get_current_batches()
            unit.batch_count = len(unit.batch_ids)
            unit.current_batch_count = len(current_batches)
            unit.current_quantity = sum(current_batches.mapped("quantity"))
            unit.current_biomass_kg = sum(current_batches.mapped("biomass_kg"))

            if not current_batches:
                unit.current_state = "empty"
            elif any(
                batch.problem_flag or batch.status == "problem"
                for batch in current_batches
            ):
                unit.current_state = "problem"
            elif any(batch.status == "quarantine" for batch in current_batches):
                unit.current_state = "quarantine"
            elif all(batch.status == "harvested" for batch in current_batches):
                unit.current_state = "harvested"
            else:
                unit.current_state = "occupied"

    def action_open_batch_history(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Batch History",
            "res_model": "aqua.batch",
            "view_mode": "list,form",
            "domain": [("production_unit_id", "=", self.id)],
            "context": {
                "default_company_id": self.company_id.id,
                "default_farm_id": self.farm_id.id,
                "default_production_unit_id": self.id,
            },
        }

    def action_open_current_batches(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Current Batches",
            "res_model": "aqua.batch",
            "view_mode": "list,form",
            "domain": [
                ("production_unit_id", "=", self.id),
                ("active", "=", True),
                ("status", "not in", ["transferred", "completed", "closed"]),
            ],
            "context": {
                "default_company_id": self.company_id.id,
                "default_farm_id": self.farm_id.id,
                "default_production_unit_id": self.id,
            },
        }
