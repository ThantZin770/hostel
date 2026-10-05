# -*- coding: utf-8 -*-
from odoo import models, fields, api


# =================================================================
# ၁။ ROOM MODEL (အခန်းမော်ဒယ်)
# =================================================================
class HostelRoom(models.Model):
    _name = 'hostel.room'
    _description = 'Hostel Room'

    name = fields.Char(string='Room Name', required=True)
    code = fields.Char(string='Code', required=True)
    capacity = fields.Integer(string='Capacity', default=0)
    current_occupancy = fields.Integer(string='Current Occupancy', default=0)

    # Configuration / States
    allocation_mode = fields.Selection([('bed', 'Bed Based'), ('room', 'Room Based')], string='Allocation Mode',
                                       default='bed')
    room_type_id = fields.Many2one('hostel.room.type', string='Room Type')
    state = fields.Selection([
        ('available', 'Available'),
        ('maintenance', 'Maintenance'),
        ('blocked', 'Blocked'),
        ('cleaning', 'Cleaning Required')
    ], string='State', default='available')
    active = fields.Boolean(string='Active', default=True)
    use_gender_restriction = fields.Boolean(string='Use Floor Gender Restriction', default=True)
    effective_gender_restriction = fields.Char(string='Effective Gender Restriction', default='Any')
    notes = fields.Char(string='Notes', default=None)

    # 🔗 Relational Fields
    unit_ids = fields.Many2one('hostel.unit', string='Unit', required=True, ondelete='cascade')
    floor_ids = fields.Many2one('hostel.floor', string='Floor', required=True, ondelete='cascade')
    section_ids = fields.Many2one('hostel.section', string='Section', required=True, ondelete='cascade')
    building_id = fields.Many2one('hostel.building', string='Building', required=True, ondelete='cascade')

    # bed_ids = fields.One2many('hostel.bed', 'room_ids', string='Beds')

    # 🔥 Unit ကို select လိုက်တာနဲ့ Floor, Section, Building ၃ ခုလုံး Auto တွဲကျလာမည့် Logic
    @api.onchange('unit_ids')
    def _onchange_unit_id(self):
        if self.unit_ids:
            self.floor_ids = self.unit_ids.floor_ids
            self.section_ids = self.unit_ids.floor_ids.section_ids
            self.building_id = self.unit_ids.floor_ids.building_id
        else:
            self.floor_ids = False
            self.section_ids = False
            self.building_id = False


# =================================================================
# ၂။ UNIT DISPLAY NAME INHERITANCE (ယူနစ် Dropdown ပြင်ဆင်ချက်)
# =================================================================
class HostelUnitInherit(models.Model):
    _inherit = 'hostel.unit'

    # 🔥 အစ်ကိုဖြစ်ချင်တဲ့အတိုင်း Dropdown ထဲမှာ 6/AYY/04/406 လို့ ပေါ်စေမည့် နှလုံးသား Logic
    @api.depends('name', 'floor_ids.code', 'building_id.code', 'section_ids.name')
    def _compute_display_name(self):
        for record in self:
            b_code = record.building_id.code or ''
            # Section Name ရဲ့ ရှေ့ ၃ လုံးကို အကြီးစာလုံးပြောင်းယူခြင်း (ဥပaddy -> AYY)
            s_code = record.section_ids.name[:3].upper() if record.section_ids else ''
            f_code = record.floor_ids.code or ''
            u_name = record.name or ''

            if b_code and f_code:
                # အားလုံးစုံလျှင် Hierarchy လမ်းကြောင်းအတိုင်း သီကုံးပေးပါသည်
                record.display_name = f"{b_code}/{s_code}/{f_code}/{u_name}"
            else:
                record.display_name = u_name
