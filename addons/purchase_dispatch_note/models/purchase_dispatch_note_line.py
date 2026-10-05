from odoo import api, fields, models


class PurchaseDispatchNoteLine(models.Model):
    _inherit = "dispatch.note.line"

    product_id_domain = fields.Binary(
        compute="_compute_product_id_domain",
    )

    @api.depends("note_id.purchase_order_id.order_line.product_id")
    def _compute_product_id_domain(self):
        for rec in self:
            purchase_order = rec.note_id.purchase_order_id
            rec.product_id_domain = (
                [("id", "in", purchase_order.order_line.product_id.ids)]
                if purchase_order
                else []
            )
