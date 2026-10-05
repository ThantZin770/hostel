# -*- coding: utf-8 -*-
from odoo import fields, models


class HostelRoomType(models.Model):
    _name = 'hostel.room.type'
    _description = 'Hostel Room Type'
    _order = 'sequence, name, id'

    name = fields.Char(string='Room Type', required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    description = fields.Text(string='Description')
