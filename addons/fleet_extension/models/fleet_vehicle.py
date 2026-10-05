from odoo import fields, models


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    fleet_type = fields.Selection(
        selection=[
            ("internal", "Internal"),
            ("external", "External"),
        ],
        string="Fleet Type",
        default="internal",
        required=True,
    )
