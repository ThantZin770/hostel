from odoo import _, fields, models
from odoo.exceptions import UserError


class DispatchReturnNote(models.TransientModel):
    _name = "dispatch.return.note"
    _description = "Dispatch Return Note"

    source_note_id = fields.Many2one("dispatch.note", required=True, readonly=True)
    line_ids = fields.One2many("dispatch.return.note.line", "return_note_id")

    def action_return_dispatch(self):
        return_qty = sum(self.line_ids.mapped("return_qty"))
        if return_qty <= 0:
            raise UserError(_("Please Add A Return Qty"))

    def action_return_all_dispatch(self):
        self.ensure_one()
        for line in self.line_ids:
            line.return_qty = line.dispatch_qty
        self.action_return_dispatch()


class DispatchReturnNoteLine(models.TransientModel):
    _name = "dispatch.return.note.line"
    _description = "Dispatch Return Note Line"

    return_note_id = fields.Many2one("dispatch.return.note")
    product_id = fields.Many2one("product.product")
    uom_id = fields.Many2one("uom.uom")
    dispatch_qty = fields.Float(required=True, readonly=True)
    return_qty = fields.Float(required=True)
