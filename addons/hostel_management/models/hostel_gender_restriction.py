from odoo import models, fields, api
class GenderRestriction(models.Model):
    _name = 'hostel.gender.restriction'
    _description = 'Gender Restriction'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    remarks = fields.Text(string='Remarks')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
    ], string='Status', default='draft', required=True)

    def action_confirm(self):
        for record in self:
            record.state = 'confirmed'
