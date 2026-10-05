from odoo import models, fields


class HostelSection(models.Model):
    _name = 'hostel.section'
    _description = 'Hostel Section'


    name = fields.Char(
        string='Section Name',
        required=True
    )

    building_id = fields.Many2one(
        'hostel.building',
        required=True,
        ondelete='cascade'
    )

    floor_ids = fields.One2many(
        'hostel.floor',
        'section_ids',
        string='Floors'
    )
