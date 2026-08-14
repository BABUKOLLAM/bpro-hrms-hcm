# Data Privacy Notes

This document is a **technical inventory and starting point**, not a
legal opinion. This suite stores sensitive personal data — before
going live with real employee data, the client's own legal/compliance
function should review this against India's **Digital Personal Data
Protection Act, 2023 (DPDP Act)** and any other applicable regulation.
Nothing here should be treated as a substitute for that review.

---

## What personal data this suite stores, and where

| Data | Where | Module |
|---|---|---|
| Name, contact details, address | `hr.employee` | native Odoo / `bpro_hr` |
| PAN, UAN, ESI number | `hr.employee` | `bpro_payroll`, `bpro_statutory_filing` |
| Bank account number, IFSC | `res.partner.bank` (linked to the employee) | `bpro_statutory_filing` (bank advice), `bpro_ess` |
| Aadhar number | `bpro.job.offer` (candidate-submitted during onboarding) | `bpro_recruitment` |
| Salary, CTC, payslip figures | `hr.contract`, `hr.payslip` | `bpro_payroll` |
| Attendance timestamps, location metadata (if using native web check-in) | `hr.attendance` | `bpro_attendance` |
| Health-adjacent inference (Sick Leave usage, though not diagnosis) | `hr.leave` | `bpro_leave` |
| Performance ratings, appraisal notes | `bpro.pms.*` | `bpro_pms` |
| Exit reason, F&F figures | `bpro.exit.request` | `bpro_exit` |

None of this is unusual for HR software — it's what any payroll/HCM
system necessarily holds. The point of listing it explicitly is so
whoever does the compliance review knows exactly what's in scope,
rather than having to reverse-engineer it from the code.

---

## Access control already in place

The suite's four-tier permission model (`bpro_base`) already limits
who can see what:

- **Employee**: their own data only (payslips, leave, attendance,
  assets) — enforced by row-level security rules, not just hidden
  menus.
- **HOD**: their own department's data, mostly read-only.
- **HR**: full access, since HR necessarily needs to see everyone's
  data to do payroll/compliance.
- **Super Admin**: unrestricted, for whoever administers the system.

This is a real access-control boundary (Odoo's `ir.rule` row-level
security, not just view-level hiding) — verified by the automated test
suite (`bpro_ess` tests specifically check that an employee genuinely
cannot read another employee's payslip via a direct query, not just
that the menu is hidden).

---

## What this suite does *not* currently provide

- **No data retention / auto-deletion policy.** Employee records,
  once created, persist indefinitely — there's no automated process
  for purging data for employees who left years ago, even if a
  retention policy says it should be. If the client's policy requires
  this, it needs to be built or handled manually.
- **No encryption at rest** beyond whatever the underlying Postgres/
  filesystem setup provides — this suite doesn't add its own
  field-level encryption for PAN/Aadhar/bank data. If the client's
  policy requires encryption at rest for specific fields, that's
  additional work, not something toggled on here.
- **No consent-capture workflow.** The DPDP Act requires informed
  consent for processing personal data in scope. Candidates/employees
  submitting data through the recruitment portal or ESS are not shown
  a consent notice by this software — if required, that's a
  client-facing addition to build.
- **No data-subject-access-request (DSAR) tooling.** If an employee
  formally requests a copy of, or the deletion of, their personal
  data, there's no one-click export/erasure feature — it would be done
  manually through the standard Odoo interface (which can export any
  record's data, but there's no purpose-built "erase this person's
  data" workflow).

---

## Practical recommendations before go-live

1. Put the infrastructure protections from `SETUP_GUIDE.md` in place
   first — TLS in transit, backups, and a changed admin password are
   the baseline; without them, discussing DPDP compliance is
   premature.
2. Have the client confirm who internally is the designated data
   handler/DPO-equivalent contact, and make sure that person has
   reviewed this document and the access-control model above.
3. Decide on a retention policy for departed employees' data (how long
   to keep it, in what form) and note it — even if enforcement stays
   manual for now.
4. If the client operates in a regulated sector with additional
   requirements beyond the DPDP Act, get that sector-specific review
   done separately — this document only addresses general
   HR-data handling.
