{
    "name": "bpro HCM Dashboard",
    "summary": "One-glance HR/payroll KPI dashboard for the standalone bpro HCM suite",
    "description": """
A lightweight capstone dashboard for this repo's own HCM modules only -
unlike the ERP-wide bpro_dashboard this suite was extracted from,
this one has zero dependency outside bpro_payroll, bpro_recruitment,
bpro_attendance, bpro_leave and bpro_exit, so it installs cleanly in a
pure-HCM deployment with no Sales/Manufacturing/Finance modules present.

* Payroll: this month's confirmed gross payout, and payslips still
  awaiting confirmation (draft/verify) - a live "is payroll closed for
  the month" signal.
* Recruitment: open vacancies still short of target headcount, overdue
  joining reports past their SLA.
* Attendance: pending absence-exception reviews.
* Exit: open separation requests in flight, trailing-12-month attrition
  rate.
* Leave: Earned Leave encashment liability, computed with the exact
  same s79(11) formula bpro_exit's own F&F settlement uses, so the two
  figures can never disagree.
""",
    "version": "18.0.1.0.0",
    "category": "Human Resources",
    "author": "Dr. Babu & bpro Technologies",
    "website": "https://www.bpropms.com",
    "license": "LGPL-3",
    "depends": ["bpro_payroll", "bpro_recruitment", "bpro_attendance", "bpro_leave", "bpro_exit"],
    "data": [
        "security/ir.model.access.csv",
        "views/bpro_hcm_dashboard_views.xml",
    ],
    "installable": True,
    "application": True,
}
