from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class PurchaseDemandPlanCreateRFQWizard(models.TransientModel):
    _name = "purchase.demand.plan.create.rfq.wizard"
    _description = "Create RFQ from Demand Planning Lines"

    line_ids = fields.Many2many(
        "purchase.demand.plan.line",
        "purchase_demand_create_rfq_wizard_line_rel",
        "wizard_id",
        "line_id",
        string="Demand Lines",
        required=True,
    )
    preferred_vendor_id = fields.Many2one(
        "res.partner",
        string="Global Vendor",
    )
    vendor_mode = fields.Selection(
        [
            ("single", "Single Vendor"),
            ("multi", "Multi Vendor"),
        ],
        default="single",
        required=True,
    )
    line_count = fields.Integer(compute="_compute_line_info")
    has_mixed_preferred_vendors = fields.Boolean(compute="_compute_line_info")
    has_missing_preferred_vendor = fields.Boolean(compute="_compute_line_info")
    wizard_line_ids = fields.One2many(
        "purchase.demand.plan.create.rfq.wizard.line",
        "wizard_id",
        string="RFQ Lines",
    )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        line_ids = self.env.context.get("central_demand_plan_line_ids")
        if (
            not line_ids
            and self.env.context.get("active_model") == "purchase.demand.plan.line"
        ):
            line_ids = self.env.context.get("active_ids")

        if not line_ids:
            return values

        lines = self.env["purchase.demand.plan"]._get_central_rfq_lines(
            line_ids,
            strict=True,
        )
        values["line_ids"] = [fields.Command.set(lines.ids)]
        values["wizard_line_ids"] = self._prepare_summary_line_commands(lines)

        common_vendor = self.env["purchase.demand.plan"]._get_common_central_rfq_vendor(
            lines
        )
        values["vendor_mode"] = "single" if common_vendor else "multi"
        if common_vendor:
            values["preferred_vendor_id"] = common_vendor.id
        return values

    @api.model
    def _prepare_summary_line_commands(self, lines):
        grouped_lines = defaultdict(lambda: self.env["purchase.demand.plan.line"])
        for line in lines:
            grouped_lines[self._get_summary_group_key(line)] |= line

        return [
            fields.Command.create(self._prepare_summary_line_values(group_lines))
            for group_lines in grouped_lines.values()
        ]

    @api.model
    def _get_summary_group_key(self, line):
        return (
            line.demand_id.company_id.id,
            line.product_id.id,
            line.uom_id.id,
        )

    @api.model
    def _prepare_summary_line_values(self, lines):
        representative_line = lines[:1]
        approved_qty = sum(lines.mapped("approved_qty"))
        common_vendor = self._get_common_vendor(lines)
        return {
            "source_line_ids": [fields.Command.set(lines.ids)],
            "demand_reference": ", ".join(
                sorted(set(lines.mapped("demand_id.reference")))
            ),
            "product_id": representative_line.product_id.id,
            "approved_qty": approved_qty,
            "rfq_qty": approved_qty,
            "uom_id": representative_line.uom_id.id,
            "preferred_vendor_id": common_vendor.id,
        }

    @api.model
    def _get_common_vendor(self, lines):
        vendors = lines.mapped("preferred_vendor_id")
        if (
            len(lines.filtered("preferred_vendor_id")) == len(lines)
            and len(vendors) == 1
        ):
            return vendors
        return self.env["res.partner"]

    @api.onchange("preferred_vendor_id")
    def _onchange_preferred_vendor_id(self):
        if self.vendor_mode != "single":
            return
        for wizard_line in self.wizard_line_ids:
            wizard_line.preferred_vendor_id = self.preferred_vendor_id

    @api.onchange("vendor_mode")
    def _onchange_vendor_mode(self):
        if self.vendor_mode == "single":
            self._onchange_preferred_vendor_id()
        else:
            self.preferred_vendor_id = False

    def _get_split_sibling_lines(self, wizard_line):
        source_ids = self._get_split_key(wizard_line)
        return self.wizard_line_ids.filtered(
            lambda line: self._get_split_key(line) == source_ids
        )

    @api.model
    def _get_split_key(self, wizard_line):
        return tuple(sorted(wizard_line.source_line_ids.ids))

    def _add_missing_split_line(self, wizard_line):
        self.ensure_one()
        sibling_lines = self._get_split_sibling_lines(wizard_line)
        total_qty = sum(sibling_lines.mapped("rfq_qty"))
        precision = wizard_line.uom_id.rounding or 0.01
        if (
            not sibling_lines
            or float_compare(
                total_qty,
                wizard_line.approved_qty or 0.0,
                precision_rounding=precision,
            )
            >= 0
        ):
            return False

        self.wizard_line_ids += self.env[
            "purchase.demand.plan.create.rfq.wizard.line"
        ].new(self._prepare_split_balance_values(wizard_line, total_qty))
        return True

    @api.model
    def _prepare_split_balance_values(self, wizard_line, current_qty):
        return {
            "source_line_ids": [fields.Command.set(wizard_line.source_line_ids.ids)],
            "demand_reference": wizard_line.demand_reference,
            "product_id": wizard_line.product_id.id,
            "approved_qty": wizard_line.approved_qty,
            "rfq_qty": (wizard_line.approved_qty or 0.0) - current_qty,
            "uom_id": wizard_line.uom_id.id,
            "preferred_vendor_id": wizard_line.preferred_vendor_id.id,
            "is_split_balance": True,
        }

    @api.depends(
        "line_ids",
        "preferred_vendor_id",
        "vendor_mode",
        "wizard_line_ids",
        "wizard_line_ids.preferred_vendor_id",
    )
    def _compute_line_info(self):
        for wizard in self:
            if wizard.vendor_mode == "single":
                vendors = wizard.preferred_vendor_id
                vendor_lines = (
                    wizard.wizard_line_ids
                    if wizard.preferred_vendor_id
                    else self.env["purchase.demand.plan.create.rfq.wizard.line"]
                )
            else:
                vendor_lines = wizard.wizard_line_ids.filtered("preferred_vendor_id")
                vendors = vendor_lines.mapped("preferred_vendor_id")
            wizard.line_count = len(wizard.line_ids)
            wizard.has_mixed_preferred_vendors = len(vendors) > 1
            wizard.has_missing_preferred_vendor = len(vendor_lines) != len(
                wizard.wizard_line_ids
            )

    def action_confirm(self):
        self.ensure_one()
        if not self.wizard_line_ids:
            raise UserError(_("Select at least one demand line to create an RFQ."))
        self._apply_common_vendor()
        self._check_vendor_lines()
        return self.env["purchase.demand.plan"]._create_rfq_from_wizard_values(
            self._prepare_rfq_split_values()
        )

    def _apply_common_vendor(self):
        if self.vendor_mode == "single" and self.preferred_vendor_id:
            for wizard_line in self.wizard_line_ids:
                wizard_line.preferred_vendor_id = self.preferred_vendor_id

    def _check_vendor_lines(self):
        if self.vendor_mode == "single" and not self.preferred_vendor_id:
            raise UserError(_("Select a global vendor before creating RFQs."))
        missing_vendor_lines = self.wizard_line_ids.filtered(
            lambda wizard_line: not wizard_line.preferred_vendor_id
        )
        if missing_vendor_lines:
            raise UserError(
                _(
                    "Some RFQ lines do not have a vendor. "
                    "Select a vendor on every wizard line before creating RFQs."
                )
            )

    def _prepare_rfq_split_values(self):
        return [
            {
                "source_line_ids": wizard_line.source_line_ids.ids,
                "preferred_vendor_id": (
                    self.preferred_vendor_id.id
                    if self.vendor_mode == "single"
                    else wizard_line.preferred_vendor_id.id
                ),
                "product_id": wizard_line.product_id.id,
                "uom_id": wizard_line.uom_id.id,
                "approved_qty": wizard_line.approved_qty,
                "rfq_qty": wizard_line.rfq_qty,
            }
            for wizard_line in self.wizard_line_ids
        ]


class PurchaseDemandPlanCreateRFQWizardLine(models.TransientModel):
    _name = "purchase.demand.plan.create.rfq.wizard.line"
    _description = "Create RFQ Vendor Selection Line"

    wizard_id = fields.Many2one(
        "purchase.demand.plan.create.rfq.wizard",
        required=True,
        ondelete="cascade",
    )
    source_line_ids = fields.Many2many(
        "purchase.demand.plan.line",
        "purchase_demand_create_rfq_wizard_source_line_rel",
        "wizard_line_id",
        "line_id",
        string="Demand Lines",
        readonly=True,
    )
    demand_reference = fields.Char(string="Demand Reference", readonly=True)
    product_id = fields.Many2one("product.product", string="Product", readonly=True)
    approved_qty = fields.Float(string="Total Approved Qty", readonly=True)
    rfq_qty = fields.Float(string="Approved Qty", required=True)
    uom_id = fields.Many2one("uom.uom", string="UoM", readonly=True)
    preferred_vendor_id = fields.Many2one(
        "res.partner",
        string="Vendor",
    )
    is_split_balance = fields.Boolean(default=False)
    no_remaining_qty = fields.Boolean(compute="_compute_no_remaining_qty")

    @api.onchange("rfq_qty")
    def _onchange_rfq_qty(self):
        self._check_not_over_approved_qty()

    @api.constrains("rfq_qty", "source_line_ids", "wizard_id")
    def _check_not_over_approved_qty(self):
        for line in self.filtered("wizard_id"):
            sibling_lines = line.wizard_id._get_split_sibling_lines(line)
            total_qty = sum(sibling_lines.mapped("rfq_qty"))
            precision = line.uom_id.rounding or 0.01
            if (
                float_compare(
                    total_qty,
                    line.approved_qty or 0.0,
                    precision_rounding=precision,
                )
                > 0
            ):
                raise UserError(
                    _(
                        "Approved quantity cannot exceed total Approved "
                        "quantity for %(product)s.",
                        product=line.product_id.display_name,
                    )
                )

    @api.depends(
        "approved_qty",
        "rfq_qty",
        "source_line_ids",
        "wizard_id.wizard_line_ids.rfq_qty",
        "wizard_id.wizard_line_ids.source_line_ids",
    )
    def _compute_no_remaining_qty(self):
        for line in self:
            precision = line.uom_id.rounding or 0.01
            if not line.wizard_id:
                total_qty = line.rfq_qty
            else:
                total_qty = sum(
                    line.wizard_id._get_split_sibling_lines(line).mapped("rfq_qty")
                )
            line.no_remaining_qty = (
                float_compare(
                    total_qty,
                    line.approved_qty or 0.0,
                    precision_rounding=precision,
                )
                >= 0
            )

    def action_split_remaining(self):
        self.ensure_one()
        self.wizard_id._add_missing_split_line(self)
        return {
            "type": "ir.actions.act_window",
            "name": _("Create RFQ"),
            "res_model": "purchase.demand.plan.create.rfq.wizard",
            "res_id": self.wizard_id.id,
            "views": [(False, "form")],
            "target": "new",
        }
