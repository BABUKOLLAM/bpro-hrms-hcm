from datetime import date, datetime, time

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestEmploymentType(TransactionCase):
    """Employment category classification and its effect on payroll -
    the one axis (Daily Wage) with real computation stakes gets a
    hand-calculated payslip check; the rest are validation/default
    checks."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.struct = cls.env.ref("bpro_payroll.structure_india_ctc")

    def _make_employee(self, name):
        return self.env["hr.employee"].create({"name": name, "tz": "Asia/Kolkata"})

    def test_ftc_requires_end_date(self):
        employee = self._make_employee("FTC Employee")
        with self.assertRaises(ValidationError):
            self.env["hr.contract"].create({
                "name": "FTC contract", "employee_id": employee.id,
                "wage": 20000, "ctc_annual": 240000.0,
                "basic_percent": 50.0, "hra_percent": 40.0,
                "employment_category": "ftc",
                "date_start": date(2026, 1, 1), "state": "open",
            })
        # With an end date, it's fine.
        contract = self.env["hr.contract"].create({
            "name": "FTC contract 2", "employee_id": employee.id,
            "wage": 20000, "ctc_annual": 240000.0,
            "basic_percent": 50.0, "hra_percent": 40.0,
            "employment_category": "ftc",
            "date_start": date(2026, 1, 1), "date_end": date(2026, 12, 31),
            "state": "open",
        })
        self.assertEqual(contract.employment_category, "ftc")

    def test_daily_wage_requires_positive_rate(self):
        employee = self._make_employee("Daily Wage Rate Employee")
        with self.assertRaises(ValidationError):
            self.env["hr.contract"].create({
                "name": "Daily wage contract", "employee_id": employee.id,
                "wage": 500, "employment_category": "daily_wage",
                "daily_wage_rate": 0.0,
                "date_start": date(2026, 1, 1), "state": "open",
            })

    def test_trainee_defaults_pf_esi_off(self):
        employee = self._make_employee("Trainee Employee")
        contract = self.env["hr.contract"].new({
            "employee_id": employee.id, "employment_category": "trainee",
        })
        contract._onchange_employment_category_defaults()
        self.assertFalse(contract.pf_applicable)
        self.assertFalse(contract.esi_applicable)

    def test_contract_labour_defaults_pf_esi_off(self):
        employee = self._make_employee("Contract Labour Employee")
        contract = self.env["hr.contract"].new({
            "employee_id": employee.id, "employment_category": "contract_labour",
        })
        contract._onchange_employment_category_defaults()
        self.assertFalse(contract.pf_applicable)
        self.assertFalse(contract.esi_applicable)

    def test_permanent_unaffected(self):
        """The default category must reproduce bpro_leave's own
        LOP-multiplied CTC formula exactly - this module's override of
        rule_basic must not silently change behaviour for the common
        case."""
        employee = self._make_employee("Permanent Employee")
        contract = self.env["hr.contract"].create({
            "name": "Permanent contract", "employee_id": employee.id,
            "wage": 20000, "ctc_annual": 240000.0,
            "basic_percent": 50.0, "hra_percent": 40.0,
            "struct_id": self.struct.id, "date_start": date(2026, 1, 1),
            "state": "open",
        })
        self.assertEqual(contract.employment_category, "permanent")
        payslip = self.env["hr.payslip"].create({
            "employee_id": employee.id, "contract_id": contract.id,
            "struct_id": self.struct.id,
            "date_from": date(2026, 8, 1), "date_to": date(2026, 8, 31),
            "name": "Permanent slip",
        })
        payslip.compute_sheet()
        basic = next(l.total for l in payslip.line_ids if l.code == "BASIC")
        self.assertAlmostEqual(basic, 10000.0, places=2)  # full month, no LOP

    def test_daily_wage_basic_is_rate_times_days_worked(self):
        employee = self._make_employee("Daily Wage Employee")
        contract = self.env["hr.contract"].create({
            "name": "Daily wage contract", "employee_id": employee.id,
            "wage": 500, "employment_category": "daily_wage",
            "daily_wage_rate": 600.0,
            "struct_id": self.struct.id, "date_start": date(2026, 1, 1),
            "state": "open",
        })
        # 3 days of attendance in the payslip period.
        for day in (3, 4, 5):
            self.env["hr.attendance"].create({
                "employee_id": employee.id,
                "check_in": datetime.combine(date(2026, 8, day), time(3, 30)),
                "check_out": datetime.combine(date(2026, 8, day), time(12, 30)),
            })
        payslip = self.env["hr.payslip"].create({
            "employee_id": employee.id, "contract_id": contract.id,
            "struct_id": self.struct.id,
            "date_from": date(2026, 8, 1), "date_to": date(2026, 8, 31),
            "name": "Daily wage slip",
        })
        days_worked = payslip.bpro_daily_wage_days_worked(employee)
        self.assertEqual(days_worked, 3)
        payslip.compute_sheet()
        basic = next(l.total for l in payslip.line_ids if l.code == "BASIC")
        self.assertAlmostEqual(basic, 600.0 * 3, places=2)
        # HRA still derives correctly from this Basic - no special
        # case needed there.
        hra = next(l.total for l in payslip.line_ids if l.code == "HRA")
        self.assertAlmostEqual(hra, 600.0 * 3 * 0.40, places=2)

    def test_daily_wage_not_double_prorated_by_lop_factor(self):
        """A Daily Wage employee with a confirmed attendance exception
        on a day they didn't attend must NOT have Basic reduced twice
        (once by days_worked already excluding it, again by
        LOP_FACTOR) - LOP_FACTOR must be bypassed for this category."""
        employee = self._make_employee("Daily Wage LOP Employee")
        contract = self.env["hr.contract"].create({
            "name": "Daily wage LOP contract", "employee_id": employee.id,
            "wage": 500, "employment_category": "daily_wage",
            "daily_wage_rate": 600.0,
            "struct_id": self.struct.id, "date_start": date(2026, 1, 1),
            "state": "open",
        })
        self.env["hr.attendance"].create({
            "employee_id": employee.id,
            "check_in": datetime.combine(date(2026, 8, 3), time(3, 30)),
            "check_out": datetime.combine(date(2026, 8, 3), time(12, 30)),
        })
        # A confirmed exception on a day the employee did NOT attend -
        # already correctly excluded from days_worked (=1); LOP_FACTOR
        # must not ALSO shrink the result.
        self.env["bpro.attendance.exception"].create({
            "employee_id": employee.id, "date": date(2026, 8, 4),
            "state": "confirmed_absent",
        })
        payslip = self.env["hr.payslip"].create({
            "employee_id": employee.id, "contract_id": contract.id,
            "struct_id": self.struct.id,
            "date_from": date(2026, 8, 1), "date_to": date(2026, 8, 31),
            "name": "Daily wage LOP slip",
        })
        payslip.compute_sheet()
        basic = next(l.total for l in payslip.line_ids if l.code == "BASIC")
        self.assertAlmostEqual(basic, 600.0 * 1, places=2)
