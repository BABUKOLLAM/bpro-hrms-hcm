{
    "name": "bpro Theme & Language Switcher",
    "summary": "Always-visible Day/Night/Auto theme and language selector in the backend systray",
    "description": """
Adds a persistent systray icon (next to the user avatar, visible on
every backend screen) with two controls:

* Language - lists every active language on this database, switches
  the current user's language and reloads.
* Theme - Day / Night / Auto. Day and Night set Odoo's own native
  `color_scheme` cookie, which the webclient already uses server-side
  to choose between its light and dark CSS bundles (confirmed by
  reading web/views/webclient_templates.xml directly rather than
  assuming) - so every screen, native and custom, gets proper dark
  styling for free. Auto has no native Odoo equivalent: it reads the
  OS's prefers-color-scheme on load and keeps the cookie in sync,
  including live if the OS preference changes without a reload.
""",
    "version": "18.0.1.0.0",
    "category": "Hidden",
    "author": "Team bpro",
    "website": "https://bpropms.com",
    "license": "LGPL-3",
    "depends": ["web"],
    "assets": {
        "web.assets_backend": [
            "bpro_theme_switcher/static/src/theme_utils.js",
            "bpro_theme_switcher/static/src/theme_lang_systray.js",
            "bpro_theme_switcher/static/src/theme_lang_systray.xml",
            "bpro_theme_switcher/static/src/theme_lang_systray.scss",
        ],
    },
    "installable": True,
    "auto_install": False,
}
