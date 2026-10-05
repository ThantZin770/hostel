{
    "name": "Purchase Return",
    "author": "Agga, IdeaCode Academy",
    "version": "19.0.1.0.0",
    "category": "Inventory/Purchase",
    "summary": "Purchase return request workflow linked to dispatch notes",
    "depends": ["hr", "purchase_dispatch_note", "demand_planning"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence.xml",
        "views/purchase_return_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
