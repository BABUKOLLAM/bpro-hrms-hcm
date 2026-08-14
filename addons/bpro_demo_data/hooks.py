from datetime import date, datetime, time, timedelta

from odoo import tools


def post_init_hook(env):
    """Populates a small, believable 'click around and see it working'
    demo dataset - gated on the exact same tools.config['without_demo']
    flag Odoo's own native demo-loading logic checks (loading.py:401),
    so every install command already used throughout this repo
    (--without-demo=all, in the README, SETUP_GUIDE, and CI workflow)
    correctly skips this in every real/test install without any
    special-casing needed here.

    Dates are relative to "today" at install time (not hard-coded),
    so the demo always looks current whenever someone actually
    installs it, rather than being anchored to a fixed date that
    drifts into the past.
    """
    if tools.config.get("without_demo"):
        return

    company = env.company
    struct = env.ref("bpro_payroll.structure_india_ctc", raise_if_not_found=False)
    if not struct:
        return

    today = date.today()
    month_start = today.replace(day=1)

    department = env["hr.department"].create({
        "name": "Demo — Manufacturing", "company_id": company.id,
    })

    # --- One employee hired through the REAL recruitment workflow,
    # not a flat created record - proves the actual engine, not a
    # facsimile of it. ---
    job = env["hr.job"].create({
        "name": "Demo Production Supervisor", "department_id": department.id,
    })
    candidate = env["hr.candidate"].create({
        "partner_name": "Asha Menon", "email_from": "asha.menon.demo@example.com",
    })
    applicant = env["hr.applicant"].create({
        "candidate_id": candidate.id, "job_id": job.id,
    })
    offer = env["bpro.job.offer"].create({
        "applicant_id": applicant.id,
        "proposed_designation": "Production Supervisor",
        "proposed_ctc": 420000.0,
        "joining_date": today,
    })
    offer.action_send()
    offer.action_accept_from_portal()
    offer.action_finalize_hiring()
    supervisor = offer.employee_id
    supervisor.write({"department_id": department.id, "tz": "Asia/Kolkata"})
    # create_employee_from_applicant() (native hr_recruitment, called via
    # action_finalize_hiring above) only creates the hr.employee record -
    # a contract is a separate step HR does afterwards in real use, so
    # one has to be created here too, not looked up.
    env["hr.contract"].create({
        "name": f"{supervisor.name} contract",
        "employee_id": supervisor.id,
        "wage": 20000,
        "struct_id": struct.id,
        "employment_category": "permanent",
        "date_start": today,
        "state": "open",
        "ctc_annual": offer.proposed_ctc,
        "basic_percent": 50.0,
        "hra_percent": 40.0,
    })
    department.manager_id = supervisor

    # --- Four more employees, directly created, spanning the
    # remaining employment categories - the point here is showing
    # the VARIETY, not re-proving the hiring workflow each time. ---
    def make_contract(name, category, **extra):
        employee = env["hr.employee"].create({
            "name": name, "department_id": department.id,
            "company_id": company.id, "tz": "Asia/Kolkata",
        })
        vals = {
            "name": f"{name} contract", "employee_id": employee.id,
            "wage": 20000, "struct_id": struct.id,
            "employment_category": category,
            "date_start": month_start - timedelta(days=180),
            "state": "open",
        }
        vals.update(extra)
        contract = env["hr.contract"].create(vals)
        return employee, contract

    permanent_emp, permanent_contract = make_contract(
        "Ravi Kumar", "permanent",
        ctc_annual=360000.0, basic_percent=50.0, hra_percent=40.0,
    )

    ftc_end = month_start + timedelta(days=180)
    make_contract(
        "Divya Nair", "ftc",
        ctc_annual=300000.0, basic_percent=50.0, hra_percent=40.0,
        date_end=ftc_end,
    )

    make_contract(
        "Arjun Das", "trainee",
        ctc_annual=180000.0, basic_percent=60.0, hra_percent=20.0,
        pf_applicable=False, esi_applicable=False,
    )

    daily_wage_emp, daily_wage_contract = make_contract(
        "Suresh Pillai", "daily_wage", daily_wage_rate=600.0,
    )

    # --- Attendance for the Daily Wage employee this month, so their
    # Basic actually computes to something on a fresh payslip rather
    # than zero. ---
    Attendance = env["hr.attendance"].sudo()
    day = month_start
    added = 0
    while day <= today and added < 8:
        if day.weekday() < 6:  # skip Sundays
            Attendance.create({
                "employee_id": daily_wage_emp.id,
                "check_in": datetime.combine(day, time(3, 30)),
                "check_out": datetime.combine(day, time(12, 30)),
            })
            added += 1
        day += timedelta(days=1)

    # --- A computed, confirmed payslip for the Permanent employee -
    # calls the real engine (compute_sheet), so every figure on it is
    # exactly what production would produce, not hand-typed numbers
    # that could drift out of sync with the actual rules. ---
    payslip = env["hr.payslip"].create({
        "employee_id": permanent_emp.id, "contract_id": permanent_contract.id,
        "struct_id": struct.id,
        "date_from": month_start, "date_to": today,
        "name": f"Demo Payslip - {permanent_emp.name}",
    })
    payslip.compute_sheet()
    payslip.write({"state": "done"})

    # --- Earned Leave allocation, so the leave-liability KPI on the
    # dashboard and the Time Off screen both show something real. ---
    el_type = env.ref("bpro_leave.leave_type_earned", raise_if_not_found=False)
    if el_type:
        env["hr.leave.allocation"].sudo().create({
            "name": "Demo EL allocation",
            "employee_id": permanent_emp.id,
            "holiday_status_id": el_type.id,
            "number_of_days": 6,
            "state": "confirm",
        }).action_approve()
