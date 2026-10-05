{
    "name": "People Directory Dashboard",
    "author": "Agga, GEAAI",
    "depends": ["base", "hr", "ica_mm_nrc", "contacts", "people_directory", "web"],
    "data": [
        "views/menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "people_directory_dashboard/static/src/people_directory_dashboard/people_directory_dashboard.js",
            "people_directory_dashboard/static/src/people_directory_dashboard/people_directory_dashboard.xml",
            "people_directory_dashboard/static/src/people_directory_dashboard/people_directory_dashboard.scss",
        ],
        "web.assets_web_dark": [
            "people_directory_dashboard/static/src/people_directory_dashboard/people_directory_dashboard.dark.scss",
        ],
    },
    "license": "LGPL-3",
}
