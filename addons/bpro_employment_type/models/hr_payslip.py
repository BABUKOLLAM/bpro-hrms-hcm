from datetime import datetime, time

from pytz import timezone as pytz_timezone, UTC

from odoo import models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def bpro_daily_wage_days_worked(self, employee):
        """Distinct calendar days with an attendance record in this
        payslip's period - the wage basis for a Daily Wage contract.
        Same tz-safe boundary handling as bpro_overtime's bpro_ot_hours
        (naive datetimes are UTC to the ORM, so the local period edges
        must be converted or a day near month-end lands in the wrong
        month) and the same local-date-from-UTC-check_in conversion as
        R5.1's attendance-exception detection (an early-morning local
        check-in before ~05:30 IST would otherwise land on the
        previous UTC calendar day)."""
        self.ensure_one()
        tz = pytz_timezone(employee.tz or "Asia/Kolkata")
        start = tz.localize(datetime.combine(self.date_from, time.min)).astimezone(UTC).replace(tzinfo=None)
        end = tz.localize(datetime.combine(self.date_to, time.max)).astimezone(UTC).replace(tzinfo=None)
        attendances = self.env["hr.attendance"].sudo().search([
            ("employee_id", "=", employee.id),
            ("check_in", ">=", start),
            ("check_in", "<=", end),
        ])
        days = {
            UTC.localize(att.check_in).astimezone(tz).date()
            for att in attendances
        }
        return len(days)
