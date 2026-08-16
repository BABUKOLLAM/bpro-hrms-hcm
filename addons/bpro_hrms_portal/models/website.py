from odoo import models

BRAND_NAME = "bpro HCM | HRMS"


class Website(models.Model):
    _inherit = "website"

    def _register_hook(self):
        super()._register_hook()
        # website.default_website ships with noupdate="1" (native Odoo
        # protects it from being reset by module upgrades), so a plain
        # XML data record can never update its name - confirmed the
        # hard way, it's silently skipped on both install and upgrade.
        # _register_hook runs on every registry load instead (install,
        # upgrade, and every server start), unaffected by noupdate,
        # which is what actually keeps this from drifting again.
        default_website = self.env.ref("website.default_website", raise_if_not_found=False)
        if default_website and default_website.name != BRAND_NAME:
            default_website.sudo().write({"name": BRAND_NAME})
