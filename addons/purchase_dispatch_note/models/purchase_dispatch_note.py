from odoo import api, fields, models


class PurchaseDispatchNote(models.Model):
    _inherit = "dispatch.note"

    type = fields.Selection(
        selection_add=[("purchase", "Purchase")],
        ondelete={"purchase": "set default"},
    )
    purchase_order_id = fields.Many2one("purchase.order", string="Purchase Order")
    picking_ids = fields.One2many(
        comodel_name="stock.picking",
        inverse_name="dispatch_note_id",
        string="Pickings",
        readonly=True,
    )

    @api.model
    def _get_dispatch_note_sequence_codes(self):
        sequence_codes = super()._get_dispatch_note_sequence_codes()
        sequence_codes["purchase"] = "purchase.dispatch.note"
        return sequence_codes

    def action_confirm(self):
        res = super().action_confirm()
        for note in self.filtered(lambda note: note.type == "purchase"):
            order = note.purchase_order_id
            if order and order.state == "purchase":
                order._create_dispatch_note_receipt(note)
        return res
