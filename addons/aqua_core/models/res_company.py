from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    is_aqua_company = fields.Boolean(string="Aquaculture Company")
    aqua_company_type = fields.Selection(
        [
            ("central", "Central Company"),
            ("aqua_main", "Aqua Culture Company"),
            ("breeder", "Breeder Company"),
            ("hatchery", "Hatchery Company"),
            ("nursery", "Nursery Company"),
            ("growout", "Grow-out Company"),
            ("harvest_sales", "Harvest & Sales Company"),
            ("other", "Other"),
        ],
        string="Aquaculture Company Type",
    )
    aqua_code = fields.Char(string="Aquaculture Code")
