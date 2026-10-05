from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Command


class DispatchNote(models.Model):
    _name = "dispatch.note"
    _description = "Dispatch Note"
    _order = "id desc"

    _dispatch_note_type = "internal"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
    )
    state = fields.Selection(
        [("draft", "Draft"), ("confirm", "Confirmed"), ("cancel", "Cancelled")],
        default="draft",
    )
    type = fields.Selection(
        selection=[("internal", "Internal")],
        string="Type",
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: self._get_default_dispatch_note_type(),
    )
    note_type = fields.Selection(
        [("plan", "Plan"), ("late", "Late"), ("return", "Return")],
        default="plan",
        readonly=True,
    )
    delivery_date = fields.Date(string="Delivery Date")
    line_ids = fields.One2many(
        comodel_name="dispatch.note.line",
        inverse_name="note_id",
        string="Lines",
    )
    remark = fields.Text(string="Remark")
    company_id = fields.Many2one(
        "res.company", string="Source Company", default=lambda self: self.env.company
    )
    vehicle_id = fields.Many2one(
        comodel_name="fleet.vehicle",
        string="Vehicle",
    )
    driver_id = fields.Many2one("res.partner", string="Driver")

    source_dispatch_note_id = fields.Many2one("dispatch.note", readonly=True)
    return_ids = fields.One2many(
        "dispatch.note", "source_dispatch_note_id", readonly=True
    )

    @api.model
    def _get_dispatch_note_sequence_codes(self):
        return {
            "internal": "dispatch.note.internal",
        }

    @api.model
    def _get_dispatch_note_sequence_code(self, dispatch_type):
        return self._get_dispatch_note_sequence_codes().get(dispatch_type, self._name)

    @api.model
    def _get_default_dispatch_note_type(self):
        return self.env.context.get("default_type") or self._dispatch_note_type

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            dispatch_type = vals.get("type") or self._get_default_dispatch_note_type()
            if not vals.get("type"):
                vals["type"] = dispatch_type
            if vals.get("name", _("New")) == _("New"):
                sequence_code = self._get_dispatch_note_sequence_code(dispatch_type)
                vals["name"] = self.env["ir.sequence"].next_by_code(sequence_code) or _(
                    "New"
                )
        return super().create(vals_list)

    def _change_state(self, new_state):
        for rec in self:
            rec.state = new_state

    def action_rest_to_draft(self):
        self._change_state("draft")

    def action_confirm(self):
        for note in self:
            if not note.line_ids:
                raise UserError(_("Product lines not found."))
        self._change_state("confirm")

    def action_cancel(self):
        self._change_state("cancel")

    def _prepare_return_values(self, line):
        return {
            "product_id": line.product_id.id,
            "uom_id": line.uom_id.id,
            "dispatch_qty": line.quantity,
            "return_qty": 0,
        }

    def action_return_dispatch(self):
        self.ensure_one()
        return_note_model = self.env["dispatch.return.note"]
        data = {
            "source_note_id": self.id,
            "line_ids": [
                Command.create(self._prepare_return_values(line))
                for line in self.line_ids
            ],
        }
        return_wizard = return_note_model.create(data)
        return {
            "name": _("Return Dispatch"),
            "type": "ir.actions.act_window",
            "res_model": "dispatch.return.note",
            "res_id": return_wizard.id,
            "target": "new",
            "view_mode": "form",
        }
