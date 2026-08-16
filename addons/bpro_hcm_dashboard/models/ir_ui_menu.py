from odoo import models

# Hire-to-retire order for the top-level app switcher, instead of
# whatever order modules happened to install in. Most of these root
# menus belong to native Odoo/OCA modules and ship with noupdate="1"
# (confirmed directly on a different fix: an XML data record silently
# does nothing against a noupdate="1" target, on install or upgrade),
# so a plain XML override can't reorder them - _register_hook runs on
# every registry load instead, unaffected by noupdate.
APP_ORDER = {
    "bpro_hcm_dashboard.menu_bpro_hcm_dashboard_root": 10,   # overview, first
    "hr_recruitment.menu_hr_recruitment_root": 20,           # hiring starts here
    "hr.menu_hr_root": 30,                                   # core employee records
    "hr_attendance.menu_hr_attendance_root": 40,
    "hr_holidays.menu_hr_holidays_root": 50,                 # Time Off
    "payroll.payroll_menu_root": 60,
    "hr_expense.menu_hr_expense_root": 70,
    "bpro_pms.menu_pms_root": 80,                             # performance
    "website_slides.website_slides_menu_root": 90,            # eLearning / LMS
    "calendar.mail_menu_calendar": 100,
    "mail.menu_root_discuss": 110,
    "spreadsheet_dashboard.spreadsheet_dashboard_menu_root": 120,
    "account.menu_finance": 130,                              # Invoicing
    "website.menu_website_configuration": 140,
}


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    def _register_hook(self):
        super()._register_hook()
        for xmlid, seq in APP_ORDER.items():
            menu = self.env.ref(xmlid, raise_if_not_found=False)
            if menu and menu.sequence != seq:
                menu.sudo().write({"sequence": seq})
