from odoo import models, fields

class HostelBuilding(models.Model):
    _name = 'hostel.building'
    _description = 'Hostel Building'

    name = fields.Char(string='Building Name', required=True)
    code = fields.Char(string='Building Code', required=True)

    section_ids = fields.One2many(
        'hostel.section',
        'building_id',
        string='Sections'
    )

