# bpro HCM | HRMS

[![Test suite](https://github.com/BABUKOLLAM/bpro-hrms-hcm/actions/workflows/tests.yml/badge.svg)](https://github.com/BABUKOLLAM/bpro-hrms-hcm/actions/workflows/tests.yml)
[![License: LGPL-3.0](https://img.shields.io/badge/License-LGPL--3.0-blue.svg)](LICENSE)

A complete, India-ready Human Capital Management suite built on Odoo 18
Community — hire-to-retire in one platform, with statutory payroll
compliance built in, not bolted on.

Developed by **Dr. Babu** ([www.drbabu.in](https://www.drbabu.in)) &
**bpro Technologies** ([www.bpropms.com](https://www.bpropms.com)).
Contact: [care@bpropms.com](mailto:care@bpropms.com).

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
| `bpro_hcm_dashboard` | HCM-only executive dashboard — payroll, recruitment, attendance, exit and leave-liability KPIs at a glance |
| `bpro_employment_type` | Classifies each contract as Permanent, Fixed Term Contract, Trainee/Apprentice, Daily Wage, or Contract Labour — with real payroll differences, not just a label (Daily Wage computes from actual attendance days, not CTC) |
| `bpro_approval` | Shared threshold-approval policy primitive used by several modules above |

Payroll runs on the [OCA `payroll`](https://github.com/OCA/payroll) engine
(vendored here under `addons/payroll*`, LGPL-3), extended with the India
statutory rules above.

## Documentation

- [**Setup & Onboarding Guide**](docs/SETUP_GUIDE.md) — deploying this
  for a new client: installation, TLS/production deployment, backups,
  security hardening, statutory configuration (PF/ESI/PT/LWF/TDS),
  go-live checklist.
- [**User Manual**](docs/USER_MANUAL.md) — day-to-day usage for HR
  staff, department heads, and employees, covering every module from
  recruitment through exit.
- [**Known Limitations**](docs/KNOWN_LIMITATIONS.md) — what's
  deliberately not built yet, for the client's payroll/compliance team
  to knowingly accept before go-live.
- [**UAT Checklist**](docs/UAT_CHECKLIST.md) — the acceptance-testing
  script to run on staging before the first real payroll.
- [**Data Privacy Notes**](docs/DATA_PRIVACY.md) — what personal data
  this suite stores and what compliance review it needs (India DPDP
  Act 2023).

## Running it locally

Requires Docker.

```bash
docker compose up -d
docker compose exec odoo odoo -c /etc/odoo/odoo.conf -d bpro_hcm \
  -i bpro_hrms_portal,bpro_hcm_dashboard,bpro_leave,bpro_exit,bpro_ess,bpro_probation,bpro_hr_letters,bpro_overtime,bpro_shifts,bpro_statutory_filing,bpro_lms,bpro_pms,bpro_employment_type \
  --without-demo=all --stop-after-init
docker compose restart odoo
```

Then visit `http://localhost:8069`.

**Before any real use**: this is a development setup — plain HTTP, dev
credentials, no backups. See
[`docs/SETUP_GUIDE.md`](docs/SETUP_GUIDE.md) for TLS, production
config, and backups before putting real company data in.

## Production deployment

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Layers in a Caddy reverse proxy (automatic HTTPS) and a
production-sized Odoo config. Full walkthrough in
[`docs/SETUP_GUIDE.md`](docs/SETUP_GUIDE.md) §4.5.

## Backups

```bash
./scripts/backup_db.sh <db_name>        # back up
./scripts/restore_db.sh <backup_dir> <target_db_name>  # restore
```

Nothing runs automatically — schedule `backup_db.sh` via cron. See
[`docs/SETUP_GUIDE.md`](docs/SETUP_GUIDE.md) §4.6.

## Test suites

Every module except `bpro_hrms_portal` carries its own `tests/` (Odoo
`TransactionCase`) — 171 tests in total. This runs automatically on
every push via [GitHub Actions](.github/workflows/tests.yml); to run
it yourself against a throwaway database:

```bash
docker compose run --rm --no-deps odoo odoo -c /etc/odoo/odoo.conf -d hcm_test \
  --test-enable \
  --test-tags /bpro_approval,/bpro_attendance,/bpro_base,/bpro_employment_type,/bpro_ess,/bpro_exit,/bpro_hcm_dashboard,/bpro_hr,/bpro_hr_letters,/bpro_leave,/bpro_lms,/bpro_overtime,/bpro_payroll,/bpro_pms,/bpro_probation,/bpro_recruitment,/bpro_shifts,/bpro_statutory_filing \
  -i bpro_approval,bpro_attendance,bpro_base,bpro_employment_type,bpro_ess,bpro_exit,bpro_hcm_dashboard,bpro_hr,bpro_hr_letters,bpro_hrms_portal,bpro_leave,bpro_lms,bpro_overtime,bpro_payroll,bpro_pms,bpro_probation,bpro_recruitment,bpro_shifts,bpro_statutory_filing \
  --stop-after-init --without-demo=all
```

(`--test-tags` scopes to just this suite's own tests — a bare
`--test-enable` also runs every native Odoo module's own test suite,
which is a much longer wait for no extra signal.)

## License

[LGPL-3.0](LICENSE), matching the OCA payroll modules this suite
builds on.
