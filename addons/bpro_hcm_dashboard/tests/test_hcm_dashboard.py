from datetime import date, timedelta

from odoo.tests.common import TransactionCase


class TestHcmDashboard(TransactionCase):
    """The standalone-repo dashboard - same KPI shapes as the ERP-wide
    bpro_dashboard this suite was extracted from, re-verified here since
    this module has its own, narrower dependency set."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.struct = cls.env.ref("bpro_payroll.structure_india_ctc")

    def _kpi(self):
        today = date.today()
        return self.env["bpro.hcm.dashboard"]._get_kpi_data(self.company, today)

    def test_no_data_gives_zeroes(self):
        other_company = self.env["res.company"].create({"name": "Empty HCM Co"})
        data = self.env["bpro.hcm.dashboard"]._get_kpi_data(other_company, date.today())
        self.assertEqual(data["payroll_mtd_gross"], 0.0)
        self.assertEqual(data["payroll_pending_confirmation"], 0)
        self.assertEqual(data["recruitment_open_vacancies"], 0)
        self.assertEqual(data["recruitment_overdue_joining_reports"], 0)
        self.assertEqual(data["attendance_pending_exceptions"], 0)
        self.assertEqual(data["exit_open_requests"], 0)
        self.assertEqual(data["attrition_rate_pct"], 0.0)
        self.assertEqual(data["el_liability"], 0.0)

    def test_payroll_mtd_gross_and_pending(self):
        employee = self.env["hr.employee"].create({
            "name": "Dashboard Payroll Employee", "company_id": self.company.id,
        })
        contract = self.env["hr.contract"].create({
            "name": "Dashboard contract", "employee_id": employee.id,
            "wage": 20000, "ctc_annual": 240000.0,
            "basic_percent": 50.0, "hra_percent": 40.0,
            "struct_id": self.struct.id, "date_start": date(2026, 1, 1),
            "state": "open",
        })
        today = date.today()
        done_slip = self.env["hr.payslip"].create({
            "employee_id": employee.id, "contract_id": contract.id,
            "struct_id": self.struct.id,
            "date_from": today.replace(day=1), "date_to": today,
            "name": "Dashboard done slip",
        })
        done_slip.compute_sheet()
        done_slip.write({"state": "done"})
        draft_slip = self.env["hr.payslip"].create({
            "employee_id": employee.id, "contract_id": contract.id,
            "struct_id": self.struct.id,
            "date_from": today.replace(day=1), "date_to": today,
            "name": "Dashboard draft slip",
        })
        draft_slip.compute_sheet()
        data = self._kpi()
        gross_line = done_slip.line_ids.filtered(lambda l: l.code == "GROSS")
        self.assertAlmostEqual(data["payroll_mtd_gross"], gross_line.total, places=2)
        self.assertEqual(data["payroll_pending_confirmation"], 1)

    def test_attendance_and_exit_kpis(self):
        employee = self.env["hr.employee"].create({
            "name": "Dashboard Exception Employee", "company_id": self.company.id,
        })
        self.env["bpro.attendance.exception"].create({
            "employee_id": employee.id, "date": date.today() - timedelta(days=1),
        })
        self.assertEqual(self._kpi()["attendance_pending_exceptions"], 1)

        user = self.env["res.users"].create({
            "name": "Dashboard Exit User", "login": "dashboard-hcm-exit@test.example",
            "email": "dashboard-hcm-exit@test.example",
        })
        exit_employee = self.env["hr.employee"].create({
            "name": "Dashboard Exit Employee", "company_id": self.company.id,
            "user_id": user.id,
        })
        self.env["hr.contract"].create({
            "name": "Dashboard exit contract", "employee_id": exit_employee.id,
            "wage": 20000, "ctc_annual": 240000.0,
            "basic_percent": 50.0, "hra_percent": 40.0,
            "date_start": date.today() - timedelta(days=6 * 365), "state": "open",
        })
        exit_request = self.env["bpro.exit.request"].create(
            {"employee_id": exit_employee.id}
        )
        exit_request.action_submit()
        self.assertEqual(self._kpi()["exit_open_requests"], 1)

    def test_el_liability_matches_fnf_formula(self):
        employee = self.env["hr.employee"].create({
            "name": "Dashboard EL Employee", "company_id": self.company.id,
        })
        self.env["hr.contract"].create({
            "name": "Dashboard EL contract", "employee_id": employee.id,
            "wage": 20000, "ctc_annual": 240000.0,
            "basic_percent": 50.0, "hra_percent": 40.0,
            "date_start": date.today(), "state": "open",
        })
        el_type = self.env.ref("bpro_leave.leave_type_earned")
        self.env["hr.leave.allocation"].create({
            "name": "Dashboard EL alloc", "employee_id": employee.id,
            "holiday_status_id": el_type.id, "number_of_days": 13,
            "state": "confirm",
        }).action_approve()
        # 13 days x 10000/26 = 5000 - same s79(11) formula as bpro_exit's F&F.
        self.assertAlmostEqual(self._kpi()["el_liability"], 5000.0, places=2)
