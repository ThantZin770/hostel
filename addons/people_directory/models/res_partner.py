from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    # company_type = fields.Selection(
    #     selection_add=[
    #         ("group", "Group"),
    #         ("vip", "VIP"),
    #         ("vvip", "VVIP"),
    #         ("government", "Government"),
    #     ]
    # )
    #
    # partner_type = fields.Selection(
    #     [
    #         ("public_sector", "Public Sector"),
    #         ("third_parties_workforce", "Third Parties Workforce"),
    #         ("family_member", "Family Member"),
    #         ("other", "Other"),
    #     ],
    #     default="public_sector",
    # )
    # public_sector_type = fields.Selection(
    #     [
    #         # public_sector
    #         ("site_visitor", "Site Visitor"),
    #         ("internship", "Internship"),
    #     ],
    #     default="site_visitor",
    # )
    # third_parties_workforce_type = fields.Selection(
    #     [
    #         # third_parties_workforce
    #         ("contractor", "Contractor"),
    #         ("vendor", "Vendor"),
    #         ("supplier", "Supplier"),
    #         ("installer", "Installer"),
    #     ],
    #     default="contractor",
    # )
    # family_member_type = fields.Selection(
    #     [
    #         ("employee_family_member", "Employee Family Member"),
    #         ("contractor_family_member", "Contractor Family Member"),
    #     ]
    # )
    # other_remark = fields.Text(string="Other Remark")
