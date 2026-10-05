from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class PurchaseDemandPlan(models.Model):
    _inherit = "purchase.demand.plan"

    @api.model
    def action_central_approve_lines(self, line_ids):
        lines = self.env["purchase.demand.plan.line"].browse(line_ids).exists()
        for line in lines:
            values = {"state": "approved"}
            if not line.approved_qty:
                raise UserError(_("Please add approved quantity!"))
            line.write(values)
        self._sync_central_plan_states(lines.mapped("demand_id"))
        return True

    @api.model
    def action_central_reject_lines(self, line_ids):
        lines = self.env["purchase.demand.plan.line"].browse(line_ids).exists()
        lines.write(
            {
                "approved_qty": 0.0,
                "state": "rejected",
            }
        )
        self._sync_central_plan_states(lines.mapped("demand_id"))
        return True

    def action_central_approve(self):
        for plan in self:
            approvable_lines = plan.line_ids.filtered(
                lambda line: line.state != "rejected"
            )
            for line in approvable_lines:
                values = {"state": "approved"}
                if not line.approved_qty:
                    raise UserError(_("Please add approved quantity!"))
                line.write(values)
            plan.state = "central_approved"
        return True

    def action_central_reject(self):
        for plan in self:
            plan.line_ids.write(
                {
                    "approved_qty": 0.0,
                    "state": "rejected",
                }
            )
            plan.state = "cancel"
        return True

    def action_mark_rfq_created(self):
        lines = self.mapped("line_ids").filtered(
            lambda line: line.state == "approved" and not line.rfq_line_ids
        )
        return self.action_create_rfq_from_lines(lines.ids)

    @api.model
    def action_create_rfq_from_lines(self, line_ids, vendor_id=False):
        if not vendor_id:
            return self.action_open_create_rfq_wizard(line_ids)

        return self._create_rfq_from_lines(line_ids, vendor_id=vendor_id)

    @api.model
    def action_open_create_rfq_wizard(self, line_ids):
        lines = self._get_central_rfq_lines(line_ids, strict=True)
        common_vendor = self._get_common_central_rfq_vendor(lines)
        wizard_model = self.env["purchase.demand.plan.create.rfq.wizard"]
        wizard = wizard_model.create(
            {
                "line_ids": [fields.Command.set(lines.ids)],
                "vendor_mode": "single" if common_vendor else "multi",
                "preferred_vendor_id": common_vendor.id if common_vendor else False,
                "wizard_line_ids": wizard_model._prepare_summary_line_commands(lines),
            }
        )
        context = {
            "active_model": "purchase.demand.plan.line",
            "active_ids": lines.ids,
            "central_demand_plan_line_ids": lines.ids,
        }
        if common_vendor:
            context["default_vendor_id"] = common_vendor.id

        return {
            "type": "ir.actions.act_window",
            "name": _("Create RFQ"),
            "res_model": "purchase.demand.plan.create.rfq.wizard",
            "res_id": wizard.id,
            "views": [
                (
                    self.env.ref(
                        "purchase_demand_planning_central.view_purchase_demand_plan_create_rfq_wizard_form"
                    ).id,
                    "form",
                )
            ],
            "target": "new",
            "context": context,
        }

    @api.model
    def _get_central_rfq_lines(self, line_ids, strict=False):
        selected_lines = self.env["purchase.demand.plan.line"].browse(line_ids).exists()
        lines = selected_lines.filtered(
            lambda line: line.state == "approved" and not line.rfq_line_ids
        )
        skipped_lines = selected_lines - lines
        if strict and skipped_lines:
            references = ", ".join(
                sorted(set(skipped_lines.mapped("demand_id.reference")))
            )
            raise UserError(
                _(
                    "Only approved demand lines without an RFQ can be selected. "
                    "Check: %(references)s",
                    references=references,
                )
            )
        if not lines:
            raise UserError(
                _("There are no approved demand lines available to create RFQs.")
            )

        return lines

    @api.model
    def _get_common_central_rfq_vendor(self, lines):
        preferred_lines = lines.filtered("preferred_vendor_id")
        preferred_vendors = preferred_lines.mapped("preferred_vendor_id")
        if len(preferred_lines) == len(lines) and len(preferred_vendors) == 1:
            return preferred_vendors
        return self.env["res.partner"]

    @api.model
    def _create_rfq_from_lines(self, line_ids, vendor_id=False):
        lines = self._get_central_rfq_lines(line_ids, strict=True)
        vendor = self.env["res.partner"].browse(vendor_id).exists()
        if vendor_id and not vendor:
            raise UserError(_("Select a valid vendor before creating an RFQ."))
        if vendor:
            lines.write({"preferred_vendor_id": vendor.id})

        missing_vendor_lines = lines.filtered(lambda line: not line.preferred_vendor_id)
        if missing_vendor_lines:
            references = ", ".join(
                sorted(set(missing_vendor_lines.mapped("demand_id.reference")))
            )
            raise UserError(
                _(
                    "Set a preferred vendor before creating RFQs for: %(references)s",
                    references=references,
                )
            )

        invalid_qty_lines = lines.filtered(
            lambda line: (line.approved_qty or 0.0) <= 0.0
        )
        if invalid_qty_lines:
            references = ", ".join(
                sorted(set(invalid_qty_lines.mapped("demand_id.reference")))
            )
            raise UserError(
                _(
                    "Approved quantity must be greater than zero for: %(references)s",
                    references=references,
                )
            )

        grouped_lines = defaultdict(lambda: self.env["purchase.demand.plan.line"])
        for line in lines:
            grouped_lines[
                line.demand_id.company_id.id, line.preferred_vendor_id.id
            ] |= line

        purchase_orders = self.env["purchase.order"]
        for (company_id, vendor_id), group_lines in grouped_lines.items():
            company = self.env["res.company"].browse(company_id)
            vendor = self.env["res.partner"].browse(vendor_id)
            origins = sorted(set(group_lines.mapped("demand_id.reference")))
            order = (
                self.env["purchase.order"]
                .with_company(company)
                .create(
                    {
                        "partner_id": vendor.id,
                        "company_id": company.id,
                        "origin": ", ".join(origins),
                    }
                )
            )
            for demand_line in group_lines:
                rfq_line = (
                    self.env["purchase.order.line"]
                    .with_company(company)
                    .create(
                        {
                            "order_id": order.id,
                            **self._prepare_central_rfq_line(demand_line),
                        }
                    )
                )
                demand_line.write(
                    {
                        "state": "rfq_created",
                        "rfq_ids": [fields.Command.set(order.ids)],
                        "rfq_line_ids": [fields.Command.set(rfq_line.ids)],
                    }
                )
            purchase_orders |= order

        self._sync_central_plan_states(lines.mapped("demand_id"))

        return {
            "type": "ir.actions.act_window",
            "name": _("Created RFQs"),
            "res_model": "purchase.order",
            "domain": [("id", "in", purchase_orders.ids)],
            "views": [(False, "list"), (False, "form")],
            "target": "current",
        }

    @api.model
    def _create_rfq_from_wizard_values(self, split_values):
        line_ids = self._get_wizard_source_line_ids(split_values)
        lines = self._get_central_rfq_lines(line_ids, strict=True)
        self._check_wizard_split_vendors(split_values)
        split_groups = self._prepare_wizard_split_groups(lines, split_values)
        self._check_wizard_split_totals(split_groups)

        purchase_orders, rfq_lines_by_group = self._create_wizard_purchase_orders(
            split_groups
        )
        self._mark_wizard_lines_rfq_created(split_groups, rfq_lines_by_group)
        self._sync_central_plan_states(lines.mapped("demand_id"))

        return {
            "type": "ir.actions.act_window",
            "name": _("Created RFQs"),
            "res_model": "purchase.order",
            "domain": [("id", "in", purchase_orders.ids)],
            "views": [(False, "list"), (False, "form")],
            "target": "current",
        }

    @api.model
    def _get_wizard_source_line_ids(self, split_values):
        return list(
            {
                line_id
                for split_value in split_values
                for line_id in split_value.get("source_line_ids", [])
            }
        )

    @api.model
    def _check_wizard_split_vendors(self, split_values):
        missing_vendor_values = [
            split_value
            for split_value in split_values
            if not split_value.get("preferred_vendor_id")
        ]
        if missing_vendor_values:
            raise UserError(
                _("Select a vendor on every RFQ line before creating RFQs.")
            )

        vendor_ids = {
            split_value["preferred_vendor_id"]
            for split_value in split_values
            if split_value.get("preferred_vendor_id")
        }
        vendors = self.env["res.partner"].browse(vendor_ids).exists()
        if len(vendors) != len(vendor_ids):
            raise UserError(_("Select a valid vendor for every RFQ line."))

    @api.model
    def _prepare_wizard_split_groups(self, lines, split_values):
        groups = {}
        invalid_qty_values = []
        for split_value in split_values:
            source_lines = lines.filtered(
                lambda line: line.id in split_value.get("source_line_ids", [])
            )
            if not source_lines:
                continue
            group_key = tuple(sorted(source_lines.ids))
            quantity = split_value.get("rfq_qty") or 0.0
            precision = source_lines[:1].uom_id.rounding or 0.01
            if float_compare(quantity, 0.0, precision_rounding=precision) <= 0:
                invalid_qty_values.append(split_value)
            group = groups.setdefault(
                group_key,
                {
                    "source_lines": source_lines,
                    "approved_qty": split_value.get("approved_qty")
                    or sum(source_lines.mapped("approved_qty")),
                    "rfq_qty": 0.0,
                    "split_values": [],
                },
            )
            group["rfq_qty"] += quantity
            group["split_values"].append(split_value)

        if invalid_qty_values:
            raise UserError(
                _("RFQ quantity must be greater than zero on every RFQ line.")
            )
        return groups

    @api.model
    def _check_wizard_split_totals(self, split_groups):
        over_total_lines = self.env["purchase.demand.plan.line"]
        invalid_total_lines = self.env["purchase.demand.plan.line"]
        for group in split_groups.values():
            source_lines = group["source_lines"]
            precision = source_lines[:1].uom_id.rounding or 0.01
            comparison = float_compare(
                group["rfq_qty"],
                group["approved_qty"],
                precision_rounding=precision,
            )
            if comparison > 0:
                over_total_lines |= source_lines
            elif comparison < 0:
                invalid_total_lines |= source_lines

        if over_total_lines:
            references = ", ".join(
                sorted(set(over_total_lines.mapped("demand_id.reference")))
            )
            raise UserError(
                _(
                    "RFQ quantity cannot exceed approved quantity for: %(references)s",
                    references=references,
                )
            )

        if invalid_total_lines:
            references = ", ".join(
                sorted(set(invalid_total_lines.mapped("demand_id.reference")))
            )
            raise UserError(
                _(
                    "Split RFQ quantity total must match approved quantity for: "
                    "%(references)s",
                    references=references,
                )
            )

    @api.model
    def _create_wizard_purchase_orders(self, split_groups):
        grouped_splits = defaultdict(list)
        for group_key, group in split_groups.items():
            representative_line = group["source_lines"][:1]
            for split_value in group["split_values"]:
                grouped_splits[
                    representative_line.demand_id.company_id.id,
                    split_value["preferred_vendor_id"],
                ].append((group_key, group["source_lines"], split_value))

        purchase_orders = self.env["purchase.order"]
        rfq_lines_by_group = defaultdict(lambda: self.env["purchase.order.line"])
        for (company_id, vendor_id), split_lines in grouped_splits.items():
            company = self.env["res.company"].browse(company_id)
            vendor = self.env["res.partner"].browse(vendor_id)
            origins = sorted(
                {
                    reference
                    for _group_key, source_lines, _split_value in split_lines
                    for reference in source_lines.mapped("demand_id.reference")
                }
            )
            order = self._create_wizard_purchase_order(company, vendor, origins)
            for group_key, source_lines, split_value in split_lines:
                rfq_line = self._create_wizard_purchase_order_line(
                    order, source_lines[:1], split_value
                )
                rfq_lines_by_group[group_key] |= rfq_line
            purchase_orders |= order
        return purchase_orders, rfq_lines_by_group

    @api.model
    def _create_wizard_purchase_order(self, company, vendor, origins):
        return (
            self.env["purchase.order"]
            .with_company(company)
            .create(
                {
                    "partner_id": vendor.id,
                    "company_id": company.id,
                    "origin": ", ".join(origins),
                }
            )
        )

    @api.model
    def _create_wizard_purchase_order_line(self, order, line, split_value):
        return (
            self.env["purchase.order.line"]
            .with_company(order.company_id)
            .create(
                {
                    "order_id": order.id,
                    **self._prepare_central_rfq_line(
                        line,
                        quantity=split_value["rfq_qty"],
                    ),
                }
            )
        )

    @api.model
    def _mark_wizard_lines_rfq_created(self, split_groups, rfq_lines_by_group):
        for group_key, group in split_groups.items():
            rfq_lines = rfq_lines_by_group[group_key]
            purchase_orders = rfq_lines.mapped("order_id")
            vendor_ids = {
                split_value["preferred_vendor_id"]
                for split_value in group["split_values"]
            }
            group["source_lines"].write(
                {
                    "state": "rfq_created",
                    "rfq_ids": [fields.Command.set(purchase_orders.ids)],
                    "rfq_line_ids": [fields.Command.set(rfq_lines.ids)],
                    "preferred_vendor_id": (
                        next(iter(vendor_ids)) if len(vendor_ids) == 1 else False
                    ),
                }
            )

    def _sync_central_plan_states(self, plans):
        for plan in plans:
            if not plan.line_ids:
                continue
            line_states = set(plan.line_ids.mapped("state"))
            if line_states == {"rfq_created"}:
                plan.state = "rfq_created"
            elif line_states <= {"approved", "rfq_created"}:
                plan.state = "central_approved"
            elif line_states == {"rejected"}:
                plan.state = "cancel"

    @api.model
    def _prepare_central_rfq_line(self, line, quantity=None):
        required_date = (
            fields.Datetime.to_datetime(line.required_date)
            if line.required_date
            else fields.Datetime.now()
        )
        uom = line.uom_id or line.product_id.uom_po_id or line.product_id.uom_id
        return {
            "product_id": line.product_id.id,
            "name": line.description or line.product_id.display_name,
            "product_qty": quantity if quantity is not None else line.approved_qty,
            "product_uom_id": uom.id,
            "date_planned": required_date,
        }
