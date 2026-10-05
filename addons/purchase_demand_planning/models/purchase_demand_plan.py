from odoo import _, api, fields, models


class PurchaseDemandPlan(models.Model):
    _name = "purchase.demand.plan"
    _description = "Purchase Demand Plan"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "reference"
    _order = "id desc"

    # =====================================================
    # BASIC INFO
    # =====================================================

    reference = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )

    requester_id = fields.Many2one(
        "res.users", string="Requester", default=lambda self: self.env.user
    )

    request_date = fields.Date(string="Request Date", default=fields.Date.today)

    note = fields.Text(string="Notes")

    @api.model
    def _default_picking_type(self):
        return self._get_picking_type(
            self.env.context.get("company_id") or self.env.company.id
        )

    picking_type_id = fields.Many2one(
        "stock.picking.type",
        "Deliver To",
        required=True,
        default=_default_picking_type,
        domain="['|', ('warehouse_id', '=', False), ('warehouse_id.company_id', '=', company_id)]",
        help="This will determine operation type of incoming shipment",
    )

    @api.model
    def _get_picking_type(self, company_id):
        picking_type = self.env["stock.picking.type"].search(
            [("code", "=", "incoming"), ("warehouse_id.company_id", "=", company_id)]
        )
        if not picking_type:
            picking_type = self.env["stock.picking.type"].search(
                [("code", "=", "incoming"), ("warehouse_id", "=", False)]
            )
        if not picking_type:
            picking_type = (
                self.env["stock.picking.type"]
                .with_context(active_test=False)
                .search([("code", "=", "incoming"), ("warehouse_id", "=", False)])
            )
        return picking_type[:1]

    # =====================================================
    # STATUS
    # =====================================================

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("bu_approved", "Business Unit Approved"),
            ("central_approved", "Central Approved"),
            ("rfq_created", "RFQ Created"),
            ("cancel", "Cancelled"),
        ],
        default="draft",
    )
    type = fields.Selection(
        [
            ("auto", "Automatic"),
            ("import", "Data Import"),
        ],
        default="import",
        string="Planning Type",
    )

    # =====================================================
    # DEMAND LINES LINK
    # =====================================================

    line_ids = fields.One2many(
        "purchase.demand.plan.line", "demand_id", string="Demand Lines"
    )
    purchase_order_count = fields.Integer(compute="_compute_purchase_order_count")

    # =====================================================
    # CREATE
    # =====================================================

    @api.model
    def create(self, vals):
        for val in vals:
            if val.get("reference", _("New")) == _("New"):
                if val.get("type") == "auto":
                    val["reference"] = self.env["ir.sequence"].next_by_code(
                        "purchase.demand.plan.auto"
                    ) or _("New")
                else:
                    val["reference"] = self.env["ir.sequence"].next_by_code(
                        "purchase.demand.plan"
                    ) or _("New")

        return super().create(vals)

    # =====================================================
    # View Actions
    # =====================================================
    def action_submitted(self):
        for rec in self:
            rec.write({"state": "submitted"})

    def action_bu_approved(self):
        for plan in self:
            plan.write({"state": "bu_approved"})

    @api.depends("line_ids.rfq_ids")
    def _compute_purchase_order_count(self):
        for plan in self:
            plan.purchase_order_count = len(plan.line_ids.mapped("rfq_ids"))

    def action_view_purchase_orders(self):
        self.ensure_one()
        purchase_orders = self.line_ids.mapped("rfq_ids")
        return {
            "type": "ir.actions.act_window",
            "name": _("Purchase"),
            "res_model": "purchase.order",
            "view_mode": "list,form",
            "domain": [("id", "in", purchase_orders.ids)],
            "target": "current",
        }
