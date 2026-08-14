from odoo import tools
from odoo.tests.common import TransactionCase

from ..hooks import post_init_hook


class TestDemoData(TransactionCase):
    """The hook is gated on tools.config['without_demo'] - the exact flag
    Odoo's own native demo-loading code checks - so both branches of that
    gate need direct coverage, not just an install-doesn't-crash smoke
    test. Calling post_init_hook(env) directly (rather than reinstalling
    the module) keeps these tests fast and independent of the actual
    without_demo value the test runner itself was started with."""

    def setUp(self):
        super().setUp()
        self._original_without_demo = tools.config.get("without_demo")
        self.addCleanup(self._restore_without_demo)

    def _restore_without_demo(self):
        if self._original_without_demo is None:
            tools.config.pop("without_demo", None)
        else:
            tools.config["without_demo"] = self._original_without_demo

    def test_skips_when_without_demo_is_set(self):
        tools.config["without_demo"] = "all"
        post_init_hook(self.env)
        dept = self.env["hr.department"].search([
            ("name", "=", "Demo — Manufacturing"),
        ])
        self.assertFalse(dept)

    def test_populates_sample_company_when_demo_enabled(self):
        tools.config["without_demo"] = False
        post_init_hook(self.env)

        dept = self.env["hr.department"].search([
            ("name", "=", "Demo — Manufacturing"),
        ])
        self.assertTrue(dept)
        self.assertEqual(dept.manager_id.name, "Asha Menon")

        employees = self.env["hr.employee"].search([
            ("department_id", "=", dept.id),
        ])
        self.assertEqual(len(employees), 5)

        categories = {
            c.employee_id.name: c.employment_category
            for c in self.env["hr.contract"].search([
                ("employee_id", "in", employees.ids),
            ])
        }
        self.assertEqual(categories.get("Asha Menon"), "permanent")
        self.assertEqual(categories.get("Ravi Kumar"), "permanent")
        self.assertEqual(categories.get("Divya Nair"), "ftc")
        self.assertEqual(categories.get("Arjun Das"), "trainee")
        self.assertEqual(categories.get("Suresh Pillai"), "daily_wage")

        # Recruited-through-the-real-workflow supervisor needs a
        # contract too - create_employee_from_applicant() (native
        # hr_recruitment) only creates the hr.employee, not a contract.
        supervisor_contract = self.env["hr.contract"].search([
            ("employee_id.name", "=", "Asha Menon"),
        ])
        self.assertTrue(supervisor_contract)
        self.assertEqual(supervisor_contract.state, "open")

        trainee_contract = self.env["hr.contract"].search([
            ("employee_id.name", "=", "Arjun Das"),
        ])
        self.assertFalse(trainee_contract.pf_applicable)
        self.assertFalse(trainee_contract.esi_applicable)

        daily_wage_contract = self.env["hr.contract"].search([
            ("employee_id.name", "=", "Suresh Pillai"),
        ])
        self.assertTrue(
            self.env["hr.attendance"].search_count([
                ("employee_id", "=", daily_wage_contract.employee_id.id),
            ]) > 0
        )

        payslip = self.env["hr.payslip"].search([
            ("employee_id.name", "=", "Ravi Kumar"),
        ])
        self.assertEqual(payslip.state, "done")
        basic_line = payslip.line_ids.filtered(lambda l: l.code == "BASIC")
        self.assertEqual(basic_line.total, 15000.0)

        allocation = self.env["hr.leave.allocation"].search([
            ("employee_id.name", "=", "Ravi Kumar"),
        ])
        self.assertEqual(allocation.state, "validate")
