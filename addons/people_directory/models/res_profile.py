from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResProfile(models.Model):
    _name = "res.profile"
    _description = "People Directory Profile"
    _inherits = {
        "res.partner": "partner_id",
    }

    reference = fields.Char(
        string="Global UID", default=lambda self: _("New"), readonly=True, copy=False
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
        ],
        default="draft",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        required=True,
        delegate=True,
        ondelete="cascade",
    )

    employee_id = fields.Many2one("hr.employee", string="Employee")

    partner_type = fields.Selection(
        [
            ("visitor", "Visitor"),
            ("customer", "Customer"),
            ("employee", "Employee"),
            ("internship", "Internship"),
            ("third_parties_workforce", "Third Parties Workforce"),
            ("family_member", "Family Member"),
            ("government", "Government"),
        ],
        string="Category",
        default="visitor",
        required=True,
    )

    visitor_sub_type = fields.Selection(
        [
            ("individual_visitor", "Individual Visitor"),
            ("company_visitor", "Company Visitor"),
            ("site_visitor", "Site Visitor"),
            ("other", "Other"),
        ],
        string="Sub Type",
        default="individual_visitor",
    )
    employee_sub_type = fields.Selection(
        [
            ("full_time", "Full Time"),
            ("labor", "Labor"),
            ("other", "Other"),
        ],
        string="Sub Type",
        default="full_time",
    )
    internship_sub_type = fields.Selection(
        [
            ("university", "University"),
            ("other", "Other"),
        ],
        string="Sub Type",
        default="university",
    )
    third_parties_workforce_sub_type = fields.Selection(
        [
            ("contractor", "Contractor"),
            ("vendor", "Vendor"),
            ("installer", "Installer"),
            ("other", "Other"),
            ("customer", "Customer"),
        ],
        string="Sub Type",
        default="contractor",
    )
    family_member_sub_type = fields.Selection(
        [
            ("employee_family_member", "Employees' Family Member"),
            ("third_party_family_member", "Third Party Family Member"),
            ("other", "Other"),
        ],
        string="Sub Type",
        default="employee_family_member",
    )
    government_sub_type = fields.Selection(
        [
            ("government", "Government"),
            ("other", "Other"),
        ],
        string="Sub Type",
        default="government",
    )

    profile_type = fields.Selection(
        [
            ("person", "Person"),
            ("company", "Company"),
            ("profile", "Profile"),
        ],
        default="person",
        required=True,
    )

    job_position = fields.Char(string="Job Position")
    manager_id = fields.Many2one("hr.employee", string="Manager")
    host_employee_ids = fields.Many2many(
        "hr.employee",
        "res_profile_host_employee_rel",
        "profile_id",
        "employee_id",
        string="Host Name",
    )

    nationality_id = fields.Many2one(
        "res.country",
        string="Nationality",
        default=lambda self: self._default_nationality(),
    )
    nationality_type = fields.Selection(
        [("citizen", "Citizen"), ("foreigner", "Foreigner")],
        string="Nationality Type",
        compute="_compute_nationality_type",
        store=True,
        readonly=True,
    )

    legal_name = fields.Char(string="Legal Name")
    viber = fields.Char(string="Viber")
    date_of_birth = fields.Date(string="Date of Birth")
    age = fields.Integer(string="Age", compute="_compute_age", store=True)

    religious_id = fields.Many2one("res.religious", string="Religious")

    id_type = fields.Selection(
        [("nrc", "NRC"), ("passport", "Passport")],
        string="ID Type",
        default="nrc",
    )
    passport_number = fields.Char(string="Passport Number")
    nrc_full_number = fields.Char(
        string="NRC Number", compute="_compute_nrc_full_number"
    )

    emergency_contact_ids = fields.One2many(
        "res.profile.emergency.contact",
        "profile_id",
        string="Emergency Contact Person",
    )

    relationship_type_id = fields.Many2one(
        "res.profile.relationship.type", string="Relationship Type"
    )
    employee_family_id = fields.Many2one("hr.employee", string="Employee")
    third_party_family_partner_id = fields.Many2one(
        "res.partner", string="Third Party Family Member"
    )

    business_unit_id = fields.Many2one("res.company", string="Business Unit")
    department_id = fields.Many2one("hr.department", string="Department")
    position_title = fields.Char(string="Position")
    join_date = fields.Date(string="Join Date")
    resume_manager_id = fields.Many2one("hr.employee", string="Manager")
    working_address = fields.Char(string="Working Address")

    work_experience_ids = fields.One2many(
        "res.profile.work.experience", "profile_id", string="Working Experiences"
    )
    skill_certification_ids = fields.One2many(
        "res.profile.skill.certification",
        "profile_id",
        string="Skills & Certifications",
    )
    driver_license_ids = fields.One2many(
        "res.profile.driver.license", "profile_id", string="Driver License"
    )
    education_ids = fields.One2many(
        "res.profile.education", "profile_id", string="Education"
    )

    academic_year = fields.Char(string="Academic Year")
    major_id = fields.Many2one("res.profile.major", string="Major / Specialization")
    manager_profile_id = fields.Many2one("res.profile", string="Manager Name")

    blood_group = fields.Selection(
        [
            ("a_pos", "A+"),
            ("a_neg", "A-"),
            ("b_pos", "B+"),
            ("b_neg", "B-"),
            ("ab_pos", "AB+"),
            ("ab_neg", "AB-"),
            ("o_pos", "O+"),
            ("o_neg", "O-"),
        ],
        string="Blood Group",
    )
    weight = fields.Float(string="Weight")
    height = fields.Float(string="Height")
    remark = fields.Text(string="Remark")

    is_mass = fields.Boolean(string="Is Mass")

    @api.model
    def _default_nationality(self):
        return self.env.ref("base.mm", raise_if_not_found=False)

    @api.depends("nationality_id")
    def _compute_nationality_type(self):
        myanmar = self.env.ref("base.mm", raise_if_not_found=False)
        myanmar_code = (myanmar.code or "").upper() if myanmar else "MM"
        for profile in self:
            country = profile.nationality_id
            if country and (country.code or "").upper() != myanmar_code:
                profile.nationality_type = "foreigner"
            else:
                profile.nationality_type = "citizen"

    @api.depends("date_of_birth")
    def _compute_age(self):
        today = date.today()
        for profile in self:
            if not profile.date_of_birth:
                profile.age = 0
                continue
            dob = profile.date_of_birth
            profile.age = (
                today.year
                - dob.year
                - (1 if (today.month, today.day) < (dob.month, dob.day) else 0)
            )

    @api.depends("state_code", "township_code", "nrc_number")
    def _compute_nrc_full_number(self):
        for profile in self:
            if profile.state_code and profile.township_code and profile.nrc_number:
                profile.nrc_full_number = f"{profile.state_code}/{profile.township_code}(နိုင်){profile.nrc_number}"
            else:
                profile.nrc_full_number = False

    @api.onchange("partner_type")
    def _onchange_partner_type(self):
        subtype_fields = {
            "visitor": "visitor_sub_type",
            "employee": "employee_sub_type",
            "internship": "internship_sub_type",
            "third_parties_workforce": "third_parties_workforce_sub_type",
            "family_member": "family_member_sub_type",
            "government": "government_sub_type",
        }
        subtype_defaults = {
            "visitor_sub_type": "individual_visitor",
            "employee_sub_type": "full_time",
            "internship_sub_type": "university",
            "third_parties_workforce_sub_type": "contractor",
            "family_member_sub_type": "employee_family_member",
            "government_sub_type": "government",
        }
        for profile in self:
            current_subtype_field = subtype_fields.get(profile.partner_type)
            for field_name in subtype_fields.values():
                if field_name != current_subtype_field:
                    profile[field_name] = False
            if current_subtype_field and not profile[current_subtype_field]:
                profile[current_subtype_field] = subtype_defaults[current_subtype_field]

    @api.onchange("nationality_id")
    def _onchange_nationality_id(self):
        myanmar = self.env.ref("base.mm", raise_if_not_found=False)
        myanmar_code = (myanmar.code or "").upper() if myanmar else "MM"
        for profile in self:
            country_code = (profile.nationality_id.code or "").upper()
            if country_code and country_code != myanmar_code:
                profile.id_type = "passport"
            elif profile.id_type == "passport":
                profile.id_type = "nrc"

    @api.onchange("nationality_type")
    def _onchange_nationality_type(self):
        for profile in self:
            if profile.nationality_type == "foreigner":
                profile.id_type = "passport"
            elif profile.id_type == "passport":
                profile.id_type = "nrc"

    @api.onchange("id_type")
    def _onchange_id_type(self):
        for profile in self:
            if profile.id_type == "passport":
                profile.nrc_number = False
            else:
                profile.passport_number = False

    @api.constrains("id_type", "nationality_type")
    def _check_foreigner_id_type(self):
        for profile in self:
            if (
                profile.nationality_type == "foreigner"
                and profile.id_type != "passport"
            ):
                raise ValidationError(
                    _("Foreigner nationality type must use Passport as ID Type.")
                )

    def action_create_profile(self):
        return {
            "name": _("Profile"),
            "type": "ir.actions.act_window",
            "res_model": "res.profile",
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
        }

    @api.model
    def _normalize_identity_vals(self, vals):
        normalized = dict(vals)
        nationality_type = normalized.get("nationality_type")
        if nationality_type == "foreigner":
            normalized["id_type"] = "passport"
        elif normalized.get("nationality_id"):
            country = self.env["res.country"].browse(normalized["nationality_id"])
            myanmar = self.env.ref("base.mm", raise_if_not_found=False)
            myanmar_code = (myanmar.code or "").upper() if myanmar else "MM"
            country_code = (country.code or "").upper()
            if country_code and country_code != myanmar_code:
                normalized["id_type"] = "passport"

        if normalized.get("id_type") == "passport":
            normalized.setdefault("nrc_number", False)
        elif "id_type" in normalized:
            normalized.setdefault("passport_number", False)
        return normalized

    @api.model_create_multi
    def create(self, vals_list):
        normalized_vals_list = [
            self._normalize_identity_vals(vals) for vals in vals_list
        ]
        for vals in normalized_vals_list:
            if vals.get("reference", _("New")) == _("New"):
                vals["reference"] = self.env["ir.sequence"].next_by_code(
                    "res.profile"
                ) or _("New")
        profiles = super().create(normalized_vals_list)

        for profile in profiles:
            if profile.nationality_type == "foreigner":
                profile.id_type = "passport"
            if profile.partner_type == "employee" and not profile.employee_id:
                employee = self.env["hr.employee"].create(
                    {
                        "name": profile.name,
                        "work_contact_id": profile.partner_id.id,
                        "work_email": profile.email,
                        "mobile_phone": profile.phone,
                    }
                )
                profile.employee_id = employee.id

        return profiles

    def write(self, vals):
        vals = self._normalize_identity_vals(vals)
        res = super().write(vals)
        foreigner_profiles = self.filtered(
            lambda profile: (
                profile.nationality_type == "foreigner"
                and profile.id_type != "passport"
            )
        )
        if foreigner_profiles:
            foreigner_profiles.write({"id_type": "passport"})
        return res


class ResReligious(models.Model):
    _name = "res.religious"
    _description = "Religious"

    name = fields.Char(required=True)


class ResProfileRelationshipType(models.Model):
    _name = "res.profile.relationship.type"
    _description = "Profile Relationship Type"

    name = fields.Char(required=True)


class ResProfileMajor(models.Model):
    _name = "res.profile.major"
    _description = "Profile Major"

    name = fields.Char(required=True)


class ResProfileEmergencyContact(models.Model):
    _name = "res.profile.emergency.contact"
    _description = "Profile Emergency Contact"

    profile_id = fields.Many2one("res.profile", required=True, ondelete="cascade")
    name = fields.Char(required=True)
    phone = fields.Char()
    relative_text = fields.Char(string="Relatives")


class ResProfileWorkExperience(models.Model):
    _name = "res.profile.work.experience"
    _description = "Profile Work Experience"

    profile_id = fields.Many2one("res.profile", required=True, ondelete="cascade")
    company_name = fields.Char(required=True)
    position = fields.Char()
    start_date = fields.Date()
    end_date = fields.Date()
    description = fields.Text()


class ResProfileSkillCertification(models.Model):
    _name = "res.profile.skill.certification"
    _description = "Profile Skill Certification"

    profile_id = fields.Many2one("res.profile", required=True, ondelete="cascade")
    name = fields.Char(required=True)
    level = fields.Selection(
        [
            ("basic", "Basic"),
            ("intermediate", "Intermediate"),
            ("advanced", "Advanced"),
            ("expert", "Expert"),
        ]
    )
    issued_by = fields.Char()
    issue_date = fields.Date()
    expiry_date = fields.Date()
    note = fields.Text()


class ResProfileDriverLicense(models.Model):
    _name = "res.profile.driver.license"
    _description = "Profile Driver License"

    profile_id = fields.Many2one("res.profile", required=True, ondelete="cascade")
    license_type = fields.Char(required=True)
    license_number = fields.Char(required=True)
    issue_date = fields.Date()
    expiry_date = fields.Date()
    note = fields.Text()


class ResProfileEducation(models.Model):
    _name = "res.profile.education"
    _description = "Profile Education"

    profile_id = fields.Many2one("res.profile", required=True, ondelete="cascade")
    institution = fields.Char(required=True)
    degree = fields.Char()
    year_from = fields.Char(string="Year From")
    year_to = fields.Char(string="Year To")
    note = fields.Text()
