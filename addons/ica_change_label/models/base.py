from lxml import etree

from odoo import api, models


class BaseModel(models.AbstractModel):
    _inherit = "base"

    @api.model
    def get_view(self, view_id=None, view_type="form", **options):
        result = super().get_view(view_id=view_id, view_type=view_type, **options)

        # ARCH only exists for XML views (form, tree, search, kanban)
        arch = result.get("arch")
        if not arch:
            return result

        # Parse XML
        root = etree.fromstring(arch)

        # Find both <field name="company_id"> and any inheriting field
        for field in root.xpath("//field[@name='company_id']"):
            field.set("string", "Business Unit")

        for field in root.xpath("//field[@name='company_ids']"):
            field.set("string", "Business Units")

        # Return modified arch
        # (remove \t just like your original code)
        result["arch"] = etree.tostring(root, encoding="unicode").replace("\t", "")

        return result
