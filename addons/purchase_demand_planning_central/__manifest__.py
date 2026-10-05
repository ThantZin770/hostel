{
    "name": "Demand Planning Central",
    "author": "Agga, IdeaCode Academy",
    "depends": ["purchase_demand_planning", "purchase", "web"],
    "data": [
        "security/ir.model.access.csv",
        "views/purchase_demand_plan_views.xml",
        "views/central_demand_planning_views.xml",
        "wizards/purchase_demand_create_rfq_wizard_views.xml",
        "views/menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "purchase_demand_planning_central/static/src/central_demand_planning/**/*",
        ],
    },
    "license": "LGPL-3",
}
