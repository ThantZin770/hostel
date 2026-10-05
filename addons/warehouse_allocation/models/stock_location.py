from odoo import models


class StockLocation(models.Model):
    _inherit = "stock.location"
    #
    # product_id = fields.Many2one(
    #     comodel_name="product.template",
    #     string="Product",
    # )
