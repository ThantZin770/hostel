# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HostelUnit(models.Model):
    _name = 'hostel.unit'
    _description = 'Hostel Unit'

    name = fields.Char(string='Unit Name', required=True)

    floor_ids = fields.Many2one(
        'hostel.floor',
        string='Floor',
        required=True,
        ondelete='cascade'
    )

    section_ids = fields.Many2one(
        'hostel.section',
        string='Section',
        related='floor_ids.section_ids',
        store=True,
        readonly=True,
    )

    building_id = fields.Many2one(
        'hostel.building',
        string='Building',
        related='floor_ids.building_id',
        store=True,
        readonly=True,
    )

    room_ids = fields.One2many(
        'hostel.room',
        'unit_ids',  # 💡 Room ဖိုင်ထဲက Many2one field အမည်နဲ့ ကိုက်ညီအောင် ပြင်ပေးထားပါတယ်ဗျာ
        string='Rooms',
    )

    # 🔥 Floor ကို select လိုက်တာနဲ့ Section နှင့် Building ပါ မျက်နှာပြင်ပေါ် ချက်ချင်း Auto တွဲကျလာစေမည့် Logic
    @api.onchange('floor_ids')
    def _onchange_floor_ids(self):
        if self.floor_ids:
            self.section_ids = self.floor_ids.section_ids
            self.building_id = self.floor_ids.building_id
        else:
            self.section_ids = False
            self.building_id = False

    # 🔥 အစ်ကိုဖြစ်ချင်တဲ့အတိုင်း Dropdown ထဲမှာ 6/AYY/04/406 လို့ ပုံစံမျိုး လှလှပပ ပေါ်စေမည့် Logic
    @api.depends('name', 'floor_ids.code', 'building_id.code')
    def _compute_display_name(self):
        for record in self:
            b_code = record.building_id.code or ''
            s_code = record.section_ids.name[:3].upper() if record.section_ids and record.section_ids.name else ''
            f_code = record.floor_ids.code or ''
            u_name = record.name or ''

            if b_code and f_code:
                # 6/AYY/04/406 ဆိုပြီး Hierarchy လမ်းကြောင်းတစ်ခုလုံး သီကုံးပေးလိုက်ခြင်းဖြစ်ပါတယ်ဗျာ
                record.display_name = f"{b_code}/{s_code}/{f_code}/{u_name}"
            else:
                record.display_name = u_name