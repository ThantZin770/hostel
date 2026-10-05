from odoo import _, api, fields, models
from odoo.exceptions import AccessDenied


class PurchaseDemandPlanLine(models.Model):
    _inherit = "purchase.demand.plan.line"
    _rec_name = "demand_id"

    @api.model
    def retrieve_central_demand_planning_dashboard(self, domain=None):
        if not self.env.user._is_internal():
            raise AccessDenied()
        self.browse().check_access("read")

        base_domain = domain or []
        states = ["pending", "approved", "rfq_created", "rejected"]
        result = {
            "global": {
                "pending": 0,
                "approved": 0,
                "late": 0,
                "rfq_created": 0,
                "rejected": 0,
                "requested_qty": 0,
                "approved_qty": 0,
            },
            "my": {
                "pending": 0,
                "approved": 0,
                "late": 0,
                "rfq_created": 0,
                "rejected": 0,
                "requested_qty": 0,
                "approved_qty": 0,
            },
        }

        user_domain = [("demand_requester_id", "=", self.env.user.id)]
        today = fields.Date.context_today(self)
        late_domain = [
            ("required_date", "<", today),
            ("state", "not in", ["rfq_created", "rejected"]),
        ]

        for state in states:
            state_domain = [("state", "=", state)]
            result["global"][state] = self.search_count(
                fields.Domain.AND([base_domain, state_domain])
            )
            result["my"][state] = self.search_count(
                fields.Domain.AND([base_domain, state_domain, user_domain])
            )

        result["global"]["late"] = self.search_count(
            fields.Domain.AND([base_domain, late_domain])
        )
        result["my"]["late"] = self.search_count(
            fields.Domain.AND([base_domain, late_domain, user_domain])
        )

        for key, extra_domain in (("global", []), ("my", user_domain)):
            sums = self._read_group(
                fields.Domain.AND([base_domain, extra_domain]),
                aggregates=["requested_qty:sum", "approved_qty:sum"],
            )
            if sums:
                requested_qty, approved_qty = sums[0]
                result[key]["requested_qty"] = requested_qty or 0
                result[key]["approved_qty"] = approved_qty or 0

        return result

    def action_central_approve_line(self):
        return self.env["purchase.demand.plan"].action_central_approve_lines(self.ids)

    def action_central_reject_line(self):
        return self.env["purchase.demand.plan"].action_central_reject_lines(self.ids)

    def action_create_central_rfq(self):
        return self.env["purchase.demand.plan"].action_create_rfq_from_lines(self.ids)

    def action_open_demand_request(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Demand Request"),
            "res_model": "purchase.demand.plan",
            "res_id": self.demand_id.id,
            "views": [(False, "form")],
            "target": "current",
        }
