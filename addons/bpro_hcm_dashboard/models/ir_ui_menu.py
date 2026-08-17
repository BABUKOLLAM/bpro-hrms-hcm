from odoo import models

# The app switcher used to list every HR-related root menu (Recruitment,
# Employees, Attendances, Time Off, Payroll, Expenses, My HR) as its own
# separate top-level icon, mixed in among unrelated apps like Contacts
# and Surveys - 8 HR entries out of ~17 total. Consolidated: those 7
# root menus are re-parented under this module's own root (renamed
# "Human Resources" in the view XML), so each becomes a section inside
# one app instead of its own icon - full original submenu tree intact,
# just moved. Most of the reparented menus belong to native Odoo/OCA
# modules and ship with noupdate="1" (confirmed directly on a different
# fix: an XML data record silently does nothing against a noupdate="1"
# target, on install or upgrade), so a plain XML override can't move or
# reorder them - _register_hook runs on every registry load instead,
# unaffected by noupdate.
HR_ROOT = "bpro_hcm_dashboard.menu_bpro_hcm_dashboard_root"

# xmlid -> sequence as a section within the consolidated Human
# Resources app (hire-to-retire order; the dashboard itself, sequence
# 1, is defined directly in bpro_hcm_dashboard_views.xml).
REPARENT_UNDER_HR = {
    "hr_recruitment.menu_hr_recruitment_root": 10,   # hiring starts here
    "hr.menu_hr_root": 20,                            # core employee records
    "hr_attendance.menu_hr_attendance_root": 30,
    "hr_holidays.menu_hr_holidays_root": 40,          # Time Off
    "payroll.payroll_menu_root": 50,
    "hr_expense.menu_hr_expense_root": 60,
    "bpro_ess.menu_bpro_ess_root": 70,                # My HR / self-service, last
}

# Remaining top-level apps in the switcher, ordered.
APP_ORDER = {
    HR_ROOT: 10,                                              # overview, first
    "bpro_pms.menu_pms_root": 20,                              # performance
    "website_slides.website_slides_menu_root": 30,             # eLearning / LMS
    "calendar.mail_menu_calendar": 40,
    "mail.menu_root_discuss": 50,
    "spreadsheet_dashboard.spreadsheet_dashboard_menu_root": 60,
    "account.menu_finance": 70,                                # Invoicing
    "website.menu_website_configuration": 80,
}


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    def _register_hook(self):
        super()._register_hook()
        hr_root = self.env.ref(HR_ROOT, raise_if_not_found=False)
        if hr_root:
            # The app root must stay action-less so clicking it opens the
            # "Human Resources" home menu, not a specific view. XML
            # updates only ever ADD an action here, never clear one -
            # <menuitem> loading skips any attribute simply omitted from
            # the tag, so a stale action from an earlier version of this
            # file survives every later upgrade unless force-cleared here
            # (confirmed the hard way: setting one action="..." on this
            # exact root, in a since-reverted edit, then removing the
            # attribute again, left the stale action in place through a
            # full module upgrade).
            if hr_root.action:
                hr_root.sudo().write({"action": False})
            for xmlid, seq in REPARENT_UNDER_HR.items():
                menu = self.env.ref(xmlid, raise_if_not_found=False)
                if menu and (menu.parent_id.id != hr_root.id or menu.sequence != seq):
                    menu.sudo().write({"parent_id": hr_root.id, "sequence": seq})
        for xmlid, seq in APP_ORDER.items():
            menu = self.env.ref(xmlid, raise_if_not_found=False)
            if menu and menu.sequence != seq:
                menu.sudo().write({"sequence": seq})
