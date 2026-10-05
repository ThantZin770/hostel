from odoo import fields, models


class DispatchNoteLine(models.Model):
    _name = "dispatch.note.line"
    _description = "Dispatch Note Line"

    note_id = fields.Many2one(
        comodel_name="dispatch.note",
        string="Dispatch Note",
        required=True,
        ondelete="cascade",
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
    )
    product_id_domain = fields.Binary(
        readonly=True,
        store=False,
    )
    company_id = fields.Many2one("res.company", string="Destination Company")
    warehouse_id = fields.Many2one(
        "stock.warehouse", domain="[('company_id','=',company_id)]", string="Warehouse"
    )
    dest_location_id = fields.Many2one(
        "stock.location",
        domain="[('warehouse_id','=',warehouse_id),('usage','=','internal')]",
    )
    quantity = fields.Float(string="Quantity")
    uom_id = fields.Many2one("uom.uom", required=False)
