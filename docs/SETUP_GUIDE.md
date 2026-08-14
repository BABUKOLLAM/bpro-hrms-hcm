# bpro HCM | HRMS — Setup & Onboarding Guide

Audience: whoever is deploying this suite for a new organisation (the
bpro team, an implementation partner, or a technically confident admin
on the client's own side). If you're an end user looking for how to
*use* the system day to day, see [`USER_MANUAL.md`](USER_MANUAL.md)
instead.

---

## 1. What you're deploying

This is an Odoo 18 Community installation with 18 custom modules
(`addons/bpro_*`) plus three vendored OCA modules (`addons/payroll*`)
that supply the payroll engine native Odoo Community doesn't include.
Each client gets **their own separate database** — this is a
single-tenant deployment model, not a shared multi-tenant SaaS. There
is no cross-client data sharing to worry about; a fresh `docker compose
up` gives you a clean slate every time.

---

## 2. Prerequisites

- A server (or laptop, for evaluation) with **Docker** and **Docker
  Compose** installed.
- For production: a domain name and a reverse proxy that terminates
  TLS (Caddy, Nginx, or similar) in front of Odoo's port 8069. This
  repo does not ship a reverse-proxy config — add one before exposing
  the instance to the internet.
- Roughly **4 GB RAM minimum** for a small deployment (under ~50
  employees); scale up for larger headcounts or if you enable more
  worker processes.

---

## 3. First boot

```bash
git clone https://github.com/BABUKOLLAM/bpro-hrms-hcm.git
cd bpro-hrms-hcm
docker compose up -d
```

Wait for Postgres to report healthy (`docker compose ps`), then
install the full module set into a named database:

```bash
docker compose exec odoo odoo -c /etc/odoo/odoo.conf -d <client_db_name> \
  -i bpro_hrms_portal,bpro_hcm_dashboard,bpro_leave,bpro_exit,bpro_ess,bpro_probation,\
bpro_hr_letters,bpro_overtime,bpro_shifts,bpro_statutory_filing,bpro_lms,bpro_pms \
  --without-demo=all --stop-after-init
docker compose restart odoo
```

That single `-i` list pulls in every other module transitively
(`bpro_payroll`, `bpro_recruitment`, `bpro_attendance`, `bpro_hr`,
`bpro_base`, the vendored payroll engine, and native Odoo HR modules)
through their own dependency chains — you don't need to list those
separately.

Replace `<client_db_name>` with something identifiable, e.g.
`acme_manufacturing_prod`. Visit `http://localhost:8069`, select that
database, and log in with the master password you set in step 4 to
create your first real user.

---

## 4. Before this touches real data — security hardening

The repo ships with **development defaults that must be changed**
before any real company data goes in:

| File | Setting | Change to |
|---|---|---|
| `config/odoo.conf` | `admin_passwd` | A strong, unique password — this is the database-manager master password, separate from any user login |
| `docker-compose.yml` | `POSTGRES_PASSWORD`, `PASSWORD` | A strong, unique Postgres password (keep both values identical to each other) |

Also set `list_db = False` in `config/odoo.conf` once the client
database exists, so the database-selection screen doesn't advertise
every database on the server to anyone who visits the login page.

---

## 5. Company setup checklist

Work through this in order. Every item below is a *company policy or
statutory* value — none of it is guessed by the software; each field
has a sensible default and an explanatory tooltip, but a real
deployment must confirm each one against the client's actual
situation.

### 5.1 Company record & branding
- **Settings → General Settings → Companies**: legal name, registered
  address, PAN, TAN (for TDS/Form 16), logo.
- If replacing bpro's own branding in the landing/login pages
  (`bpro_hrms_portal`), see §8 below.

### 5.2 Statutory payroll configuration (`bpro_payroll`)
Under **Settings → Companies → [company] → Payroll** tabs:

- **PF**: wage ceiling, employee/employer/EPS/EDLI/admin rates. Seeded
  at the standard EPFO figures — confirm current rates before go-live,
  they're revised by notification from time to time.
- **ESI**: wage threshold, employee/employer rates. Same caveat.
- **Professional Tax** (`bpro.pt.config`, one record per state): this
  suite ships **pre-seeded slabs for Kerala, Tamil Nadu, Karnataka,
  and Andhra Pradesh only**, because that's what the first deployment
  needed. **A client operating in any other state needs a new
  `bpro.pt.config` record added** (Payroll menu → PT Configuration) —
  the engine handles any state, the seed data just doesn't cover every
  state yet. Verify the seeded four against the current-year slabs too.
- **Labour Welfare Fund** (`bpro.lwf.config`): seeded for Karnataka,
  Tamil Nadu, Andhra Pradesh. Kerala LWF depends on establishment
  type/board rather than a flat rate — add it once that's confirmed
  for the specific client. Other states: add as needed, same as PT.
- **TDS**: regime slabs (new & old) seeded for the current financial
  year — **re-seed at the start of each financial year** when the
  Union Budget revises slabs. Each employee separately declares New or
  Old regime on their contract.
- **Gratuity cap** (`bpro_exit`, company settings): seeded at the
  current statutory ceiling (₹20,00,000) — this moves by government
  notification, check it's still current.

### 5.3 Leave & attendance policy
- **Probation period** (`bpro_probation`, company settings): default 6
  months — company policy, adjust freely.
- **Exit notice period** (`bpro_exit`, company settings): default 30
  days — company policy, adjust freely.
- **Overtime compensation** (`bpro_overtime`, company settings): choose
  *Pay* (at a configurable multiplier, seeded 2.0× per the Factories
  Act) or *Compensatory Off*.
- **Leave types** (`bpro_leave`): Earned Leave is seeded as a
  worked-time accrual approximating the Factories Act's "1 day per 20
  worked" rule. Casual and Sick Leave have **no statutory minimum for
  factories** — the seeded day counts are a starting point, not a
  legal requirement; set them to the client's actual policy.
- **State public holidays**: not seeded at all — each state's National
  & Festival Holidays Act sets a different count (Kerala 13, Tamil
  Nadu 9, Karnataka 10, Andhra Pradesh 8, as examples). Load the
  client's actual holiday list into each work location's working
  calendar (**Employees → Configuration → Working Schedules**) before
  go-live, or attendance-exception detection will flag real holidays
  as absences.
- **Shifts** (`bpro_shifts`): two example calendars are seeded (Shift A
  06:00–14:00, Shift B 14:00–22:00, Mon–Sat). A **night shift crossing
  midnight needs its own calendar built deliberately** — Odoo working
  calendars are per-day, so a 22:00–06:00 shift is two attendance
  lines, not seeded blind here.

### 5.4 Attendance capture
`bpro_attendance` ships a **device-agnostic CSV/XLSX import** — it
does not include a live connector to any specific biometric device
brand. If the client has a punch device, confirm:
1. The device brand/model and whether its bundled software can export
   a daily CSV/Excel log (columns: badge ID, date, check-in, check-out)
   — if so, the seeded import wizard works as-is.
2. Whether the device is on the same network as this Odoo instance. If
   Odoo is cloud-hosted and the device is only reachable from the
   client's own site network, a live pull integration needs a local
   middleware agent — that's custom work per device, not included.

Each employee needs a **Badge ID** set (Employees → [employee] →
HR Settings) matching whatever identifier the device export uses.

### 5.5 Employee master data
Before running the first payroll:
- Set **PAN** on every employee (required for TDS/Form 16).
- Set **UAN** and **ESI Number** on every employee who's covered
  (`bpro_statutory_filing` — needed for the ECR/ESIC exports;
  employees missing these are excluded from those files and reported,
  not silently dropped, but it's better to fill them in first).
- Set a **bank account** on every employee (needed for the bank salary
  advice export).
- Confirm each employee's **contract**: CTC, Basic %, HRA %, PF/ESI
  applicability, PT state, LWF state, TDS regime.

---

## 6. Go-live checklist (summary)

- [ ] `admin_passwd` and Postgres credentials changed from defaults
- [ ] `list_db = False` set once the real database exists
- [ ] Reverse proxy + TLS in front of Odoo (production only)
- [ ] Company legal details, PAN, TAN, logo set
- [ ] PF/ESI rates confirmed current
- [ ] PT/LWF config exists for every state the client operates in
- [ ] TDS slabs confirmed for the current financial year
- [ ] Gratuity cap confirmed current
- [ ] Probation months, notice period, OT policy set to client's actual policy
- [ ] Casual/Sick leave day-counts set to client's actual policy
- [ ] State public holiday calendars loaded per work location
- [ ] Shift calendars built for every shift the client actually runs (including night shifts, if any)
- [ ] Attendance capture method confirmed (CSV import is the default; live device integration is separate custom work if needed)
- [ ] Every employee has PAN, UAN, ESI number (if covered), bank account, Badge ID
- [ ] A test payroll run for one employee, reviewed by the client's own payroll person, before running it for everyone

---

## 7. Verifying the install

Run the full automated test suite against a throwaway database — this
exercises every statutory calculation (PF/ESI/PT/LWF/TDS math, LOP
proration, gratuity, EL encashment) against hand-verified expected
values, so a clean run is real evidence the engine is computing
correctly on this deployment's Odoo/Postgres versions:

```bash
docker compose exec odoo odoo -c /etc/odoo/odoo.conf -d verify_test \
  --test-enable -i bpro_ess,bpro_hrms_portal,bpro_hcm_dashboard,bpro_statutory_filing,\
bpro_probation,bpro_hr_letters,bpro_overtime,bpro_shifts \
  --stop-after-init --without-demo=all
```

Look for `0 failed, 0 error(s)` in the output, then drop the throwaway
database.

---

## 8. White-labelling (optional)

`bpro_hrms_portal` carries bpro's own branding (name, logo mark,
credits) on the public landing and login pages. To rebrand for a
client or reseller:
- `addons/bpro_hrms_portal/views/landing_templates.xml` and
  `login_templates.xml` — text, links, module descriptions.
- `addons/bpro_hrms_portal/static/src/scss/hrms_portal.scss` — colours
  and the logo mark styling.
- Settings → General Settings → company logo (used inside the app and
  on the login card).

---

## 9. Support model

This repository does not itself define a support/licensing agreement.
Before handing a deployment to a client as a paid product, decide and
document separately: warranty scope, support-response expectations,
and how statutory-rate updates (PF/ESI/PT/TDS revisions) will be kept
current for that client over time — these change periodically by
government notification and are not something the software
self-updates.
