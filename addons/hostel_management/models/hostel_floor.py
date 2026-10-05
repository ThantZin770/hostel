# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HostelFloor(models.Model):
    _name = 'hostel.floor'
    _description = 'Hostel Floor'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    gender = fields.Selection(
        selection=[
            ('any', 'Any'),
            ('male', 'Male'),
            ('female', 'Female')
        ],
        string='Gender',
        default='any'
    )

    section_ids = fields.Many2one(
        'hostel.section',
        string='Section',
        required=True,
        ondelete='cascade'
    )

    building_id = fields.Many2one(
        'hostel.building',
        string='Building',
        related='section_ids.building_id',
        store=True,
        readonly=True,
    )

    unit_ids = fields.One2many(
        'hostel.unit',
        'floor_ids',  # 💡 ရှေ့က Unit ဖိုင်ထဲက Many2one field အမည်နဲ့ ကိုက်ညီရပါမယ်
        string='Units'
    )

    # 🔥 အစ်ကိုဖြစ်ချင်တဲ့အတိုင်း Floor ကို ရွေးလိုက်ရင် 6/AYY/04 လို့ ချက်ချင်းပြောင်းလဲပေါ်စေမည့် နှလုံးသား Logic
    @api.depends('name', 'code', 'section_ids.name', 'building_id.code')
    def _compute_display_name(self):
        for record in self:
            b_code = record.building_id.code or ''
            # Section Name ရှိရင် အတိုကောက် ရှေ့ ၃ လုံးကို စာလုံးအကြီး ပြောင်းယူပါတယ် (ဥပမာ- Ayarwaddy -> AYY)
            s_code = record.section_ids.name[:3].upper() if record.section_ids and record.section_ids.name else ''
            f_code = record.code or ''

            if b_code and f_code:
                # 6/AYY/04 ပုံစံမျိုး String သီကုံးပေးလိုက်ခြင်းဖြစ်ပါတယ်ဗျာ
                record.display_name = f"{b_code}/{s_code}/{f_code}"
            else:
                record.display_name = record.name or ''

    @api.onchange('section_ids')
    def _onchange_section_ids(self):
        if self.section_ids:
            self.building_id = self.section_ids.building_id
        else:
            self.building_id = False