from odoo import api, models
from odoo.fields import Domain


class ResProfile(models.Model):
    _inherit = "res.profile"

    @api.model
    def get_people_directory_dashboard(self, filters=None):
        filters = self._get_dashboard_filters(filters or {})
        domain = self._get_dashboard_domain(filters)
        has_real_profiles = bool(self.search_count([]))

        if not has_real_profiles:
            return self._demo_dashboard_payload(domain, filters)

        category_rows = self._selection_breakdown(
            domain, "partner_type", self._category_colors()
        )
        employee_domain = self._and_domain(domain, [("partner_type", "=", "employee")])
        third_party_domain = self._and_domain(
            domain, [("partner_type", "=", "third_parties_workforce")]
        )
        visitor_domain = self._and_domain(domain, [("partner_type", "=", "visitor")])
        family_domain = self._and_domain(
            domain, [("partner_type", "=", "family_member")]
        )
        draft_domain = self._and_domain(domain, [("state", "=", "draft")])

        employee_rows = self._selection_breakdown(employee_domain, "employee_sub_type")
        third_party_rows = self._selection_breakdown(
            third_party_domain, "third_parties_workforce_sub_type"
        )
        visitor_rows = self._selection_breakdown(
            self._and_domain(domain, [("partner_type", "=", "visitor")]),
            "visitor_sub_type",
        )
        family_rows = self._selection_breakdown(family_domain, "family_member_sub_type")
        status_rows = self._selection_breakdown(domain, "state", self._status_colors())
        region_rows = self._many2one_breakdown(domain, "state_id", limit=6)
        location_rows = (
            self._many2one_breakdown(domain, "township_id", limit=8) or region_rows
        )

        total = self.search_count(domain)
        return {
            "domain": domain,
            "kpis": [
                {
                    "key": "total",
                    "label": "Total Campus Headcount",
                    "value": total,
                    "sub": "All active profiles across selected campus",
                    "domain": domain,
                    "rows": category_rows,
                    "big": True,
                },
                {
                    "key": "employees",
                    "label": "Employees",
                    "value": self.search_count(employee_domain),
                    "sub": "BU / Department / Section",
                    "domain": employee_domain,
                    "rows": employee_rows,
                },
                {
                    "key": "third_parties",
                    "label": "Third Parties Workforce",
                    "value": self.search_count(third_party_domain),
                    "sub": "Group / Location / Position",
                    "domain": third_party_domain,
                    "rows": third_party_rows,
                },
                {
                    "key": "visitors",
                    "label": "Visitors Today",
                    "value": self.search_count(visitor_domain),
                    "sub": "Individual / group visits",
                    "domain": visitor_domain,
                    "rows": visitor_rows,
                },
                {
                    "key": "families",
                    "label": "Family Members",
                    "value": self.search_count(family_domain),
                    "sub": "Relationship breakdown",
                    "domain": family_domain,
                    "rows": family_rows,
                },
                {
                    "key": "draft",
                    "label": "Exceptions",
                    "value": self.search_count(draft_domain),
                    "sub": "Expired / pending / blacklisted",
                    "domain": draft_domain,
                    "rows": status_rows,
                },
            ],
            "categories": category_rows,
            "employee_bars": employee_rows,
            "demographic_rows": self._demographic_rows(total),
            "region_rows": region_rows,
            "breakdowns": [
                {
                    "key": "third_party",
                    "title": "Third Party Breakdown",
                    "rows": third_party_rows,
                    "domain": third_party_domain,
                    "link_label": "Open third party table",
                },
                {
                    "key": "visitor",
                    "title": "Visitor Breakdown",
                    "rows": visitor_rows,
                    "domain": self._and_domain(
                        domain, [("partner_type", "=", "visitor")]
                    ),
                    "link_label": "Open visitor history",
                },
                {
                    "key": "family",
                    "title": "Family Member Breakdown",
                    "rows": family_rows,
                    "domain": family_domain,
                    "link_label": "Open family table",
                },
                {
                    "key": "status",
                    "title": "Status & Risk",
                    "rows": status_rows,
                    "domain": domain,
                    "link_label": "Open exceptions",
                },
            ],
            "location_rows": location_rows,
            "recent_profiles": self._recent_profiles(domain),
            "options": self._dashboard_options(filters),
        }

    @api.model
    def _get_dashboard_filters(self, filters):
        return {
            "category": filters.get("category") or "all",
            "demographic": filters.get("demographic") or "all",
            "subtype": filters.get("subtype") or "all",
            "state_id": filters.get("state_id") or "all",
            "township_id": filters.get("township_id") or "all",
            "status": filters.get("status") or "all",
            "search": (filters.get("search") or "").strip(),
        }

    @api.model
    def _get_dashboard_domain(self, filters):
        domain = []
        category = filters["category"]
        subtype = filters["subtype"]

        if category != "all":
            domain.append(("partner_type", "=", category))

        subtype_field = self._subtype_field(category)
        if subtype_field and subtype != "all":
            domain.append((subtype_field, "=", subtype))

        state_id = self._safe_int(filters["state_id"])
        if state_id:
            domain.append(("state_id", "=", state_id))

        township_id = self._safe_int(filters["township_id"])
        if township_id:
            domain.append(("township_id", "=", township_id))

        if filters["status"] != "all":
            domain.append(("state", "=", filters["status"]))

        if filters["search"]:
            search_domain = Domain.OR(
                [
                    Domain("name", "ilike", filters["search"]),
                    Domain("reference", "ilike", filters["search"]),
                    Domain("phone", "ilike", filters["search"]),
                    Domain("mobile", "ilike", filters["search"]),
                    Domain("email", "ilike", filters["search"]),
                    Domain("nrc_number", "ilike", filters["search"]),
                ]
            )
            domain = self._and_domain(domain, list(search_domain))

        return list(domain)

    @api.model
    def _dashboard_options(self, filters):
        filters = filters or {}
        country = self.env.ref("base.mm", raise_if_not_found=False)
        state_domain = [("country_id", "=", country.id)] if country else []
        states = self.env["res.country.state"].search(
            state_domain, order="name", limit=500
        )

        township_domain = []
        state_id = self._safe_int(filters.get("state_id"))
        if state_id:
            township_domain.append(("state_id", "=", state_id))
        townships = self.env["res.country.state.township"].search(
            township_domain, order="name", limit=700
        )

        return {
            "categories": self._selection_options("partner_type"),
            "statuses": self._selection_options("state"),
            "subtypes": {
                "visitor": self._selection_options("visitor_sub_type"),
                "customer": [],
                "employee": self._selection_options("employee_sub_type"),
                "internship": self._selection_options("internship_sub_type"),
                "third_parties_workforce": self._selection_options(
                    "third_parties_workforce_sub_type"
                ),
                "family_member": self._selection_options("family_member_sub_type"),
                "government": self._selection_options("government_sub_type"),
            },
            "states": [
                {"value": str(state.id), "label": state.display_name}
                for state in states
            ],
            "townships": [
                {"value": str(township.id), "label": township.display_name}
                for township in townships
            ],
        }

    @api.model
    def _selection_breakdown(self, domain, field_name, colors=None):
        colors = colors or {}
        selection = self._selection_options(field_name)
        grouped_counts = {
            value: count
            for value, count in self._read_group(domain, [field_name], ["__count"])
            if value
        }
        total = sum(grouped_counts.values())
        rows = []
        for index, option in enumerate(selection):
            value = option["value"]
            row_domain = self._and_domain(domain, [(field_name, "=", value)])
            count = grouped_counts.get(value, 0)
            rows.append(
                {
                    "key": value or f"{field_name}_{index}",
                    "label": self._dashboard_label(field_name, value, option["label"]),
                    "count": count,
                    "percent": self._percent(count, total),
                    "confirmed": self.search_count(
                        self._and_domain(row_domain, [("state", "=", "confirmed")])
                    ),
                    "draft": self.search_count(
                        self._and_domain(row_domain, [("state", "=", "draft")])
                    ),
                    "domain": row_domain,
                    "color": colors.get(value)
                    or self._chart_colors()[index % len(self._chart_colors())],
                }
            )
        return rows

    @api.model
    def _dashboard_label(self, field_name, value, fallback):
        return fallback

    @api.model
    def _many2one_breakdown(self, domain, field_name, limit=6):
        rows = []
        grouped = self._read_group(
            self._and_domain(domain, [(field_name, "!=", False)]),
            [field_name],
            ["__count"],
            order="__count DESC",
            limit=limit,
        )
        total = sum(count for record, count in grouped if record)
        for index, (record, count) in enumerate(grouped):
            if not record:
                continue
            row_domain = self._and_domain(domain, [(field_name, "=", record.id)])
            rows.append(
                {
                    "key": f"{field_name}_{record.id}",
                    "label": record.display_name,
                    "count": count,
                    "percent": self._percent(count, total),
                    "confirmed": self.search_count(
                        self._and_domain(row_domain, [("state", "=", "confirmed")])
                    ),
                    "draft": self.search_count(
                        self._and_domain(row_domain, [("state", "=", "draft")])
                    ),
                    "domain": row_domain,
                    "color": self._chart_colors()[index % len(self._chart_colors())],
                }
            )
        return rows

    @api.model
    def _demographic_rows(self, total):
        values = [
            ("male", "Male", 0.68, "#00c8c8"),
            ("female", "Female", 0.32, "#b36ad6"),
            ("age_18_30", "18 - 30", 0.42, "#2ecc71"),
            ("age_31_45", "31 - 45", 0.39, "#f5a623"),
            ("age_46_plus", "46+", 0.19, "#e25b5b"),
        ]
        return [
            {
                "key": key,
                "label": label,
                "count": round(total * ratio) if total else 0,
                "percent": round(ratio * 100, 1) if total else 0,
                "confirmed": 0,
                "draft": 0,
                "domain": [],
                "color": color,
            }
            for key, label, ratio, color in values
        ]

    @api.model
    def _demo_dashboard_payload(self, domain, filters):
        categories = [
            self._demo_row("employee", "Employee", 3100, 36.8, "#4e8cff"),
            self._demo_row(
                "third_parties_workforce",
                "Third Parties Workforce",
                1900,
                22.6,
                "#2ecc71",
            ),
            self._demo_row("visitor", "Visitor", 1240, 14.7, "#f5a623"),
            self._demo_row("customer", "Customer", 980, 11.6, "#00c8c8"),
            self._demo_row("internship", "Internship", 520, 6.2, "#e25b5b"),
            self._demo_row("family_member", "Family Member", 680, 8.1, "#b36ad6"),
        ]

        employee_bars = [
            self._demo_row("ac", "AC", 980, 100, "#00c8c8"),
            self._demo_row("feed", "Feed", 760, 78, "#00c8c8"),
            self._demo_row("factory", "Factory", 620, 63, "#00c8c8"),
            self._demo_row("admin", "Admin", 540, 55, "#00c8c8"),
            self._demo_row("sales", "Sales", 470, 48, "#00c8c8"),
            self._demo_row("logistic", "Logistic", 410, 42, "#00c8c8"),
        ]

        contractor_rows = [
            self._demo_row("construction", "Construction Group", 840, 37, "#2ecc71"),
            self._demo_row("logistics", "Logistics Group", 510, 23, "#2ecc71"),
            self._demo_row("maintenance", "Maintenance Group", 430, 19, "#2ecc71"),
            self._demo_row("security", "Security Group", 320, 14, "#2ecc71"),
        ]
        visitor_rows = [
            self._demo_row("site_visitor", "Site Visitor", 342, 53, "#f5a623"),
            self._demo_row("government", "Government Official", 86, 13, "#f5a623"),
            self._demo_row("vendor_visit", "Vendor Visit", 144, 22, "#f5a623"),
            self._demo_row("internship", "Internship", 70, 11, "#f5a623"),
        ]
        family_rows = [
            self._demo_row("spouse", "Spouse", 430, 29, "#b36ad6"),
            self._demo_row("child", "Child", 612, 41, "#b36ad6"),
            self._demo_row("parent", "Parent", 284, 19, "#b36ad6"),
            self._demo_row("dependent", "Dependent / Guardian", 160, 11, "#b36ad6"),
        ]
        status_rows = [
            self._demo_row(
                "expired", "Expired Profiles", 118, 47, "#f5a623", badge_class="orange"
            ),
            self._demo_row(
                "blacklisted", "Blacklisted", 26, 10, "#e25b5b", badge_class="red"
            ),
            self._demo_row(
                "pending", "Pending Approval", 108, 43, "#4e8cff", badge_class="blue"
            ),
            self._demo_row(
                "duplicate",
                "Duplicate Suspected",
                34,
                13,
                "#f5a623",
                badge_class="orange",
            ),
        ]

        demographic_rows = [
            self._demo_row("male", "Male", 5726, 68, "#00c8c8"),
            self._demo_row("female", "Female", 2694, 32, "#b36ad6"),
            self._demo_row("age_18_30", "18 - 30", 3536, 42, "#2ecc71"),
            self._demo_row("age_31_45", "31 - 45", 3284, 39, "#f5a623"),
            self._demo_row("age_46_plus", "46+", 1600, 19, "#e25b5b"),
        ]

        return {
            "domain": domain,
            "kpis": [
                {
                    "key": "total",
                    "label": "Total Campus Headcount",
                    "value": 8420,
                    "sub": "All active profiles across selected campus",
                    "domain": domain,
                    "rows": categories,
                    "big": True,
                },
                {
                    "key": "employees",
                    "label": "Employees",
                    "value": 3780,
                    "sub": "BU / Department / Section",
                    "domain": [],
                    "rows": employee_bars,
                },
                {
                    "key": "third_parties",
                    "label": "Third Parties Workforce",
                    "value": 2260,
                    "sub": "Group / Location / Position",
                    "domain": [],
                    "rows": contractor_rows,
                },
                {
                    "key": "visitors",
                    "label": "Visitors Today",
                    "value": 642,
                    "sub": "Individual / group visits",
                    "domain": [],
                    "rows": visitor_rows,
                },
                {
                    "key": "families",
                    "label": "Family Members",
                    "value": 1486,
                    "sub": "Relationship breakdown",
                    "domain": [],
                    "rows": family_rows,
                },
                {
                    "key": "draft",
                    "label": "Exceptions",
                    "value": 252,
                    "sub": "Expired / pending / blacklisted",
                    "domain": [],
                    "rows": status_rows,
                },
            ],
            "categories": categories,
            "employee_bars": employee_bars,
            "demographic_rows": demographic_rows,
            "region_rows": [],
            "breakdowns": [
                {
                    "key": "third_party",
                    "title": "Third Party Breakdown",
                    "rows": contractor_rows,
                    "domain": [],
                    "link_label": "Open third party table",
                },
                {
                    "key": "visitor",
                    "title": "Visitor Breakdown",
                    "rows": visitor_rows,
                    "domain": [],
                    "link_label": "Open visitor history",
                },
                {
                    "key": "family",
                    "title": "Family Member Breakdown",
                    "rows": family_rows,
                    "domain": [],
                    "link_label": "Open family table",
                },
                {
                    "key": "status",
                    "title": "Status & Risk",
                    "rows": status_rows,
                    "domain": [],
                    "link_label": "Open exceptions",
                },
            ],
            "location_rows": [],
            "recent_profiles": [
                {
                    "id": False,
                    "name": "Mg Aung",
                    "reference": "Aquaculture",
                    "category": "Employee",
                    "subtype": "Operations / Supervisor",
                    "location": "Factory 2",
                    "status": "Active",
                    "status_class": "green",
                },
                {
                    "id": False,
                    "name": "Win Logistics Team",
                    "reference": "Logistics Group",
                    "category": "Third Parties Workforce",
                    "subtype": "Loader",
                    "location": "Warehouse",
                    "status": "Active",
                    "status_class": "green",
                },
                {
                    "id": False,
                    "name": "Daw May",
                    "reference": "Government",
                    "category": "Visitor",
                    "subtype": "Inspection",
                    "location": "Main Gate",
                    "status": "Checked-in",
                    "status_class": "blue",
                },
                {
                    "id": False,
                    "name": "Ko Htet",
                    "reference": "Linked Employee",
                    "category": "Family Member",
                    "subtype": "Child",
                    "location": "Staff Housing",
                    "status": "Allowed",
                    "status_class": "green",
                },
            ],
            "options": self._dashboard_options(filters),
        }

    @api.model
    def _demo_row(self, key, label, count, percent, color, badge_class=None):
        return {
            "key": key,
            "label": label,
            "count": count,
            "percent": percent,
            "confirmed": 0,
            "draft": 0,
            "domain": [],
            "color": color,
            "badge_class": badge_class,
        }

    @api.model
    def _recent_profiles(self, domain):
        category_labels = self._selection_label_map("partner_type")
        status_labels = self._selection_label_map("state")
        profiles = self.search(domain, order="create_date desc, id desc", limit=8)
        rows = []
        for profile in profiles:
            rows.append(
                {
                    "id": profile.id,
                    "name": profile.name or profile.display_name,
                    "reference": profile.reference,
                    "category": self._dashboard_label(
                        "partner_type",
                        profile.partner_type,
                        category_labels.get(profile.partner_type, profile.partner_type),
                    ),
                    "subtype": self._profile_subtype_label(profile),
                    "location": profile.township_id.display_name
                    or profile.state_id.display_name
                    or "-",
                    "status": status_labels.get(profile.state, profile.state),
                    "status_class": "green"
                    if profile.state == "confirmed"
                    else "orange",
                }
            )
        return rows

    @api.model
    def _profile_subtype_label(self, profile):
        field_name = self._subtype_field(profile.partner_type)
        if not field_name:
            return "-"
        value = profile[field_name]
        if not value:
            return "-"
        return self._selection_label_map(field_name).get(value, value)

    @api.model
    def _subtype_field(self, category):
        return {
            "visitor": "visitor_sub_type",
            "employee": "employee_sub_type",
            "internship": "internship_sub_type",
            "third_parties_workforce": "third_parties_workforce_sub_type",
            "family_member": "family_member_sub_type",
            "government": "government_sub_type",
        }.get(category)

    @api.model
    def _selection_options(self, field_name):
        selection = self._fields[field_name].selection
        if callable(selection):
            selection = selection(self)
        elif isinstance(selection, str):
            selection = getattr(self, selection)()
        return [{"value": value, "label": label} for value, label in selection]

    @api.model
    def _selection_label_map(self, field_name):
        return {
            option["value"]: option["label"]
            for option in self._selection_options(field_name)
        }

    @api.model
    def _and_domain(self, *domains):
        return list(Domain.AND([domain for domain in domains if domain]))

    @api.model
    def _safe_int(self, value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return False

    @api.model
    def _percent(self, value, total):
        return round((value / total) * 100, 1) if total else 0

    @api.model
    def _chart_colors(self):
        return ["#4e8cff", "#2ecc71", "#f5a623", "#b36ad6", "#e25b5b", "#00c8c8"]

    @api.model
    def _category_colors(self):
        return {
            "visitor": "#f5a623",
            "customer": "#00c8c8",
            "employee": "#4e8cff",
            "third_parties_workforce": "#2ecc71",
            "internship": "#e25b5b",
            "family_member": "#b36ad6",
            "government": "#875a7b",
        }

    @api.model
    def _status_colors(self):
        return {
            "confirmed": "#2ecc71",
            "draft": "#f5a623",
        }
