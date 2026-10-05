from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseReturn(models.Model):
    _name = "purchase.return"
    _description = "Purchase Return"
    _order = "id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
    )
    requester_id = fields.Many2one(
        "hr.employee",
        string="Requester",
        required=True,
        default=lambda self: self.env.user.employee_id,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("requested", "Requested"),
            ("bu_approved", "BU Approved"),
            ("central_approved", "Central Approved"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        copy=False,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    line_ids = fields.One2many(
        "purchase.return.line",
        "return_id",
        string="Lines",
    )
    note = fields.Text()
    requested_date = fields.Datetime(string="Requested Date", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "purchase.return"
                ) or _("New")
        return super().create(vals_list)

    def action_request(self):
        for record in self:
            if not record.line_ids:
                raise UserError(_("Please add at least one return line."))
            record.state = "requested"
            record.requested_date = fields.Datetime.now()

    def action_bu_approve(self):
        self.state = "bu_approved"
        # self.write({"state": "bu_approved"})

    def action_central_approve(self):
        self.state = "central_approved"
        # self.write({"state": "central_approved"})

    def action_cancel(self):
        self.state = "cancelled"
        # self.write({"state": "cancelled"})

    def action_reset_to_draft(self):
        self.state = "draft"
        # self.write({"state": "draft"})

    def action_return_dispatch_note(self): ...
