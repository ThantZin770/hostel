from odoo import models


class StockReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    def _prepare_picking_default_values_based_on(self, picking):
        vals = super()._prepare_picking_default_values_based_on(picking)
        if picking.dispatch_note_id:
            vals["dispatch_note_id"] = picking.dispatch_note_id.id
        return vals
