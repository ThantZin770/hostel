from odoo import api, fields, models


class PurchaseDemandPlanLine(models.Model):
    _name = "purchase.demand.plan.line"
    _description = "Purchase Demand Plan Line"

    # =====================================================
    # LINK TO DEMAND HEADER
    # =====================================================

    demand_id = fields.Many2one(
        "purchase.demand.plan",
        string="Demand Reference",
        required=True,
        ondelete="cascade",
    )

    # =====================================================
    # PRODUCT INFO
    # =====================================================

    product_id = fields.Many2one("product.product", string="Product", required=True)

    description = fields.Char(string="Description")

    uom_id = fields.Many2one("uom.uom", string="UoM", related="product_id.uom_id")

    # =====================================================
    # Build in QUANTITIES
    # =====================================================
    qty_available = fields.Float(
        related="product_id.qty_available", string="On Hand Qty"
    )
    virtual_available = fields.Float(
        related="product_id.virtual_available", string="Forecasted Qty"
    )
    free_qty = fields.Float(related="product_id.free_qty", string="Available Qty")
    incoming_qty = fields.Float(related="product_id.incoming_qty")
    outgoing_qty = fields.Float(related="product_id.outgoing_qty")

    # =====================================================
    # QUANTITIES
    # =====================================================

    requested_qty = fields.Float(string="Demand Qty", required=True, default=1.0)

    approved_qty = fields.Float(string="Approved Qty", default=0.0)

    rejected_qty = fields.Float(
        string="Rejected Qty", compute="_compute_rejected_qty", store=True
    )

    forecasted_issue = fields.Boolean(compute="_compute_forecasted_issue")
    is_storable = fields.Boolean(related="product_id.is_storable")

    demand_reference = fields.Char(
        related="demand_id.reference",
        string="Reference",
        store=True,
        readonly=True,
    )
    demand_requester_id = fields.Many2one(
        "res.users",
        related="demand_id.requester_id",
        string="Requester",
        store=True,
        readonly=True,
    )
    demand_company_id = fields.Many2one(
        "res.company",
        related="demand_id.company_id",
        string="Company",
        readonly=True,
    )
    demand_request_date = fields.Date(
        related="demand_id.request_date",
        string="Request Date",
        readonly=True,
    )
    demand_state = fields.Selection(
        related="demand_id.state",
        string="Demand Status",
        readonly=True,
    )

    @api.depends("requested_qty")
    def _compute_forecasted_issue(self):
        for line in self:
            warehouse = line.demand_id.picking_type_id.warehouse_id
            line.forecasted_issue = False
            if line.product_id:
                virtual_available = line.product_id.with_context(
                    warehouse_id=warehouse.id
                ).virtual_available
                # if line.state == 'draft':
                #     virtual_available += line.product_uom_qty
                if virtual_available < 0:
                    line.forecasted_issue = True

    def action_product_forecast_report(self):
        self.ensure_one()

        action = self.product_id.action_product_forecast_report()
        warehouse = self.demand_id.picking_type_id.warehouse_id

        action["context"] = {
            "active_id": self.product_id.id,
            "active_model": "product.product",
            # 'move_to_match_ids': self.move_ids.filtered(lambda m: m.product_id == self.product_id).ids,
            # 'purchase_line_to_match_id': self.id,
        }
        if warehouse:
            action["context"]["warehouse_id"] = warehouse.id

        # action['context'] = context
        return action

    # =====================================================
    # PROCUREMENT
    # =====================================================

    preferred_vendor_id = fields.Many2one("res.partner", string="Preferred Vendor")

    required_date = fields.Date(string="Expected Delivery Date")

    remark = fields.Text(string="Remark")

    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rfq_created", "RFQ Created"),
            ("rejected", "Rejected"),
        ],
        default="pending",
    )

    rfq_ids = fields.Many2many(
        "purchase.order",
        "purchase_demand_plan_line_purchase_order_rel",
        "demand_line_id",
        "purchase_order_id",
        string="RFQ",
        readonly=True,
        copy=False,
    )
    rfq_line_ids = fields.Many2many(
        "purchase.order.line",
        "purchase_demand_plan_line_purchase_order_line_rel",
        "demand_line_id",
        "purchase_order_line_id",
        string="RFQ Line",
        readonly=True,
        copy=False,
    )

    # =====================================================
    # COMPUTE
    # =====================================================

    @api.depends("requested_qty", "approved_qty")
    def _compute_rejected_qty(self):
        for rec in self:
            rec.rejected_qty = (
                rec.requested_qty - rec.approved_qty if rec.approved_qty > 0 else 0
            )
