# bpro HCM | HRMS

A complete, India-ready Human Capital Management suite built on Odoo 18
Community — hire-to-retire in one platform, with statutory payroll
compliance built in, not bolted on.

Developed by **Dr. Babu** ([www.drbabu.in](https://www.drbabu.in)) &
**bpro Technologies** ([www.bpropms.com](https://www.bpropms.com)).

## What's in the suite

| Module | Covers |
|---|---|
| `bpro_base` | Four-tier security model (Employee → HOD → Client HR → Super Admin) shared by every module below |
| `bpro_hr` | Employee lifecycle gaps: departure/login deactivation, threshold-gated expense approval, employment history |
| `bpro_payroll` | Full India statutory payroll — PF, ESI, multi-state Professional Tax, Labour Welfare Fund, TDS (new & old regime) with Form 16, on a flexible-benefit CTC structure |
| `bpro_recruitment` | Vacancy requisition → interview panel → tokenised offer portal → one-click hiring finalization with auto employee codes |
| `bpro_attendance` | Device-agnostic punch-log import, automatic unexplained-absence detection and HR review |
| `bpro_leave` | India leave types (Earned/Casual/Sick/Maternity/Paternity) with Loss-of-Pay proration flowing straight into payroll — PF/ESI included |
| `bpro_exit` | Resignation workflow, clearance checklist, gratuity + EL-encashment Full & Final settlement |
| `bpro_probation` | Automatic probation on hire, due-decision reminders, confirmation letter |
| `bpro_hr_letters` | Salary certificate, address proof, experience/relieving, increment letters |
| `bpro_overtime` | Overtime pay (Factories Act double-rate) or compensatory-off conversion |
| `bpro_shifts` | Dated, overlap-checked shift assignment and rotation |
| `bpro_statutory_filing` | Monthly compliance exports: EPFO ECR, ESIC contribution, per-state PT summary, Form 24Q data, bank salary advice |
| `bpro_ess` | Employee self-service: own payslips, absence flags, assets, self-filed resignation |
| `bpro_lms` | Learning management with auto-enrolled induction |
| `bpro_pms` | Goals, review cycles, appraisals |
| `bpro_hrms_portal` | Branded public landing page and login experience |
| `bpro_approval` | Shared threshold-approval policy primitive used by several modules above |

Payroll runs on the [OCA `payroll`](https://github.com/OCA/payroll) engine
(vendored here under `addons/payroll*`, LGPL-3), extended with the India
statutory rules above.

## Running it locally

Requires Docker.

```bash
docker compose up -d
docker compose exec odoo odoo -c /etc/odoo/odoo.conf -d bpro_hcm \
  -i bpro_hrms_portal,bpro_leave,bpro_exit,bpro_ess,bpro_probation,bpro_hr_letters,bpro_overtime,bpro_shifts,bpro_statutory_filing,bpro_lms,bpro_pms \
  --without-demo=all --stop-after-init
docker compose restart odoo
```

Then visit `http://localhost:8069`.

**Before any real use**: change `admin_passwd` in `config/odoo.conf` and the
Postgres credentials in `docker-compose.yml` — both ship with development
defaults.

## Test suites

Every module carries its own `tests/` (Odoo `TransactionCase`). Run the
full suite against a throwaway database:

```bash
docker compose exec odoo odoo -c /etc/odoo/odoo.conf -d bpro_hcm_test \
  --test-enable -i bpro_ess,bpro_hrms_portal,bpro_statutory_filing,bpro_probation,bpro_hr_letters,bpro_overtime,bpro_shifts \
  --stop-after-init --without-demo=all
```

## License

LGPL-3, matching the OCA payroll modules this suite builds on.
