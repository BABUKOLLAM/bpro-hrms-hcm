from datetime import date, datetime, time, timedelta

from odoo import api, fields, models


class BproHcmDashboard(models.TransientModel):
    _name = "bpro.hcm.dashboard"
    _description = "bpro HCM Dashboard"

    as_of_date = fields.Date(default=fields.Date.context_today, required=True)
    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.company.currency_id
    )

    payroll_mtd_gross = fields.Monetary(compute="_compute_kpis")
    payroll_pending_confirmation = fields.Integer(compute="_compute_kpis")
    recruitment_open_vacancies = fields.Integer(compute="_compute_kpis")
    recruitment_overdue_joining_reports = fields.Integer(compute="_compute_kpis")
    attendance_pending_exceptions = fields.Integer(compute="_compute_kpis")
    exit_open_requests = fields.Integer(compute="_compute_kpis")
    attrition_rate_pct = fields.Float(compute="_compute_kpis", digits=(16, 2))
    el_liability = fields.Monetary(compute="_compute_kpis")

    @api.depends("as_of_date")
    def _compute_kpis(self):
        for rec in self:
            data = self._get_kpi_data(self.env.company, rec.as_of_date)
            for field_name, value in data.items():
                rec[field_name] = value

    @api.model
    def _get_kpi_data(self, company, as_of_date):
        """Plain @api.model method, directly unit testable - same
        convention as the ERP-wide bpro_dashboard this repo was
        extracted from, kept for anyone porting KPIs back and forth."""
        month_start = as_of_date.replace(day=1)
        data = {}

        payslips_done = self.env["hr.payslip"].search([
            ("company_id", "=", company.id),
            ("state", "=", "done"),
            ("date_from", ">=", month_start),
            ("date_from", "<=", as_of_date),
        ])
        gross_lines = self.env["hr.payslip.line"].search([
            ("slip_id", "in", payslips_done.ids), ("code", "=", "GROSS"),
        ])
        data["payroll_mtd_gross"] = sum(gross_lines.mapped("total"))

        data["payroll_pending_confirmation"] = self.env["hr.payslip"].search_count([
            ("company_id", "=", company.id),
            ("state", "in", ("draft", "verify")),
        ])

        approved_requests = self.env["bpro.vacancy.request"].search([
            ("company_id", "=", company.id), ("state", "=", "approved"),
        ])
        data["recruitment_open_vacancies"] = len(
            approved_requests.filtered(
                lambda r: r.job_id.no_of_hired_employee < r.job_id.no_of_recruitment
            )
        )

        data["recruitment_overdue_joining_reports"] = self.env[
            "bpro.joining.report"
        ].search_count([
            ("employee_id.company_id", "=", company.id),
            ("state", "=", "pending"),
            ("sla_deadline", "<", as_of_date),
        ])

        data["attendance_pending_exceptions"] = self.env[
            "bpro.attendance.exception"
        ].search_count([
            ("employee_id.company_id", "=", company.id), ("state", "=", "pending"),
        ])

        data["exit_open_requests"] = self.env["bpro.exit.request"].search_count([
            ("company_id", "=", company.id),
            ("state", "in", ("submitted", "accepted", "settled")),
        ])

        headcount = self.env["hr.employee"].search_count([
            ("company_id", "=", company.id),
        ])
        exits_12m = self.env["bpro.exit.request"].search_count([
            ("company_id", "=", company.id),
            ("state", "=", "closed"),
            ("last_working_day", ">", as_of_date - timedelta(days=365)),
            ("last_working_day", "<=", as_of_date),
        ])
        data["attrition_rate_pct"] = (
            exits_12m / headcount * 100.0 if headcount else 0.0
        )

        el_liability = 0.0
        el_type = self.env.ref("bpro_leave.leave_type_earned", raise_if_not_found=False)
        if el_type:
            allocations = self.env["hr.leave.allocation"].search([
                ("employee_id.company_id", "=", company.id),
                ("holiday_status_id", "=", el_type.id),
                ("state", "=", "validate"),
            ])
            taken = self.env["hr.leave"].search([
                ("employee_id.company_id", "=", company.id),
                ("holiday_status_id", "=", el_type.id),
                ("state", "=", "validate"),
            ])
            balance_by_employee = {}
            for allocation in allocations:
                balance_by_employee[allocation.employee_id] = (
                    balance_by_employee.get(allocation.employee_id, 0.0)
                    + allocation.number_of_days
                )
            for leave in taken:
                balance_by_employee[leave.employee_id] = (
                    balance_by_employee.get(leave.employee_id, 0.0)
                    - leave.number_of_days
                )
            for employee, balance in balance_by_employee.items():
                if balance <= 0:
                    continue
                contract = self.env["hr.contract"].search(
                    [("employee_id", "=", employee.id), ("state", "=", "open")],
                    limit=1,
                )
                if contract:
                    monthly_basic = (
                        contract.ctc_annual / 12.0 * (contract.basic_percent / 100.0)
                    )
                    el_liability += balance * monthly_basic / 26.0
        data["el_liability"] = el_liability

        return data
