from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    dispatch_note_ids = fields.One2many(
        "dispatch.note",
        "purchase_order_id",
        related="order_id.dispatch_note_ids",
        domain=[("type", "=", "purchase")],
    )
    qty_dispatch_note = fields.Float(
        compute="_compute_qty_dispatch_note",
        string="Dispatch Note Qty",
        digits="Product Unit",
        store=False,
    )

    @api.depends(
        "order_id.state",
        # 'product_qty',
        # 'product_id',
        # 'order_id.order_line.product_id',
        # 'order_id.order_line.product_qty',
        "order_id.dispatch_note_ids",
        # 'order_id.dispatch_note_ids.line_ids.product_id',
        # 'order_id.dispatch_note_ids.line_ids.quantity',
    )
    def _compute_qty_dispatch_note(self):
        for order in self.mapped("order_id"):
            for po_line in order.order_line:
                po_line.qty_dispatch_note = 0.0

            for product in order.order_line.mapped("product_id"):
                po_lines = order.order_line.filtered(
                    lambda po_line_key: po_line_key.product_id == product
                ).sorted(lambda key_po_line: key_po_line.id)

                dispatch_qty = sum(
                    order.dispatch_note_ids.filtered(
                        lambda d: d.type == "purchase" and d.state == "confirm"
                    )
                    .mapped("line_ids")
                    .filtered(lambda note_line: note_line.product_id == product)
                    .mapped("quantity")
                )

                remaining_qty = dispatch_qty

                for index, po_line in enumerate(po_lines):
                    # last line gets all remaining qty
                    if index == len(po_lines) - 1:
                        po_line.qty_dispatch_note = remaining_qty
                    else:
                        qty = min(remaining_qty, po_line.product_qty)
                        po_line.qty_dispatch_note = qty
                        remaining_qty -= qty
