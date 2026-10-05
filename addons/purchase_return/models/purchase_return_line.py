from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PurchaseReturnLine(models.Model):
    _name = "purchase.return.line"
    _description = "Purchase Return Line"
    _order = "id"

    return_id = fields.Many2one(
        "purchase.return",
        string="Purchase Return",
        required=True,
        ondelete="cascade",
    )
    dispatch_note_id = fields.Many2one(
        "dispatch.note",
        string="Dispatch Note",
        required=True,
        domain="[('type', '=', 'purchase')]",
    )
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        required=True,
    )
    product_id_domain = fields.Binary(compute="_compute_product_id_domain")
    dispatched_qty = fields.Float(compute="_compute_dispatch_qty")
    return_qty = fields.Float(string="Qty", required=True)
    uom_id = fields.Many2one("uom.uom", string="Units of Measure", required=True)

    @api.depends(
        "dispatch_note_id.line_ids.product_id", "dispatch_note_id.line_ids.quantity"
    )
    def _compute_dispatch_qty(self):
        for rec in self:
            rec.dispatched_qty = sum(
                rec.dispatch_note_id.line_ids.filtered(
                    lambda product: product.product_id == rec.product_id
                ).mapped("quantity")
            )

    @api.depends("dispatch_note_id.line_ids.product_id")
    def _compute_product_id_domain(self):
        for line in self:
            product_ids = line.dispatch_note_id.line_ids.product_id.ids
            line.product_id_domain = [("id", "in", product_ids)] if product_ids else []

    @api.onchange("dispatch_note_id")
    def _onchange_dispatch_note_id(self):
        for line in self:
            allowed_products = line.dispatch_note_id.line_ids.product_id
            if line.product_id and line.product_id not in allowed_products:
                line.product_id = False
                line.uom_id = False

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for line in self:
            if line.product_id and not line.uom_id:
                line.uom_id = line.product_id.uom_id

    @api.constrains("return_qty")
    def _check_qty_positive(self):
        for line in self:
            if line.return_qty <= 0:
                raise ValidationError(_("Return quantity must be greater than zero."))

    @api.constrains("dispatch_note_id", "product_id")
    def _check_product_in_dispatch_note(self):
        for line in self:
            if (
                line.dispatch_note_id
                and line.product_id
                and line.product_id not in line.dispatch_note_id.line_ids.product_id
            ):
                raise ValidationError(
                    _(
                        "Product must be one of the products on the selected dispatch note."
                    )
                )
