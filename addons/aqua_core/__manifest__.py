{
    "name": "Aquaculture Core",
    "version": "19.0.1.0.0",
    "category": "Agriculture/Aquaculture",
    "summary": "Core aquaculture company, farm, batch, lifecycle, and traceability management",
    "description": """
Aquaculture Core provides the foundational database and traceability layer for real-world aquaculture operations.

It supports:
- Group company hierarchy
- Aquaculture operating companies
- Farms
- Ponds, tanks, cages, hatchery tanks, nursery areas, and processing areas
- Species
- Lifecycle stages
- Global biological traceability IDs
- Parallel batches
- Batch split, separation, merge, and stage transfer
- Water quality records
- Input consumption records
- Batch events for mortality, health, treatment, harvest, and problems
""",
    "depends": [
        "base",
        "mail",
        "product",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/aqua_sequence.xml",
        "data/aqua_stage_data.xml",
        "views/aqua_menu.xml",
        "views/res_company_views.xml",
        "views/aqua_species_views.xml",
        "views/aqua_stage_views.xml",
        "views/aqua_farm_views.xml",
        "views/aqua_production_unit_views.xml",
        "views/aqua_global_trace_views.xml",
        "views/aqua_batch_views.xml",
        "views/aqua_batch_relation_views.xml",
        "views/aqua_batch_event_views.xml",
        "views/aqua_water_quality_views.xml",
        "views/aqua_input_consumption_views.xml",
        "views/aqua_batch_wizard_views.xml",
    ],
    "demo": [
        "demo/aqua_demo_data.xml",
    ],
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}
