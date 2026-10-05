from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    dispatch_note_id = fields.Many2one(
        comodel_name="dispatch.note",
        string="Dispatch Note",
        domain=[("type", "=", "purchase")],
        copy=False,
        index=True,
        ondelete="set null",
    )
