# Known Limitations

This is a deliberate, honest list — every item here is a documented,
conscious scoping decision made during development, not a bug found
later. Review this with the client's payroll/compliance team **before
go-live** so each item is a knowing acceptance, not a surprise.

None of these affect the correctness of what *is* implemented — every
statutory calculation this suite performs is covered by automated
tests against hand-verified figures. These are things the suite
**doesn't yet do**.

---

## Payroll / statutory

### ESI contribution-period continuity is not enforced
Real ESIC eligibility is fixed for a full contribution period (April–
September or October–March) once an employee is covered — earning a
raise mid-period does not remove them from ESI until the *next*
period starts. This suite re-tests the wage-threshold each month
instead. In practice this only produces a wrong result for an
employee whose gross crosses the ESI threshold mid-period (a raise, or
a heavy Loss-of-Pay month pulling gross back under the threshold) —
most employees are unaffected. **Recommendation**: have payroll
manually flag and continue ESI contribution for anyone who crosses the
threshold mid-period, until this is built.

### ESI is not levied on overtime wages
Overtime pay is statutorily part of the ESI contribution *base* (it's
only excluded from the initial eligibility *test*). This suite's ESI
calculation is based on Gross, which does not include the OT amount —
so for employees with paid overtime, actual ESI contribution is
understated by a small margin. **Recommendation**: for organisations
paying overtime who also have ESI-covered employees, add a manual
adjustment or flag this for a near-term fix before relying on the ESI
filings for those employees.

### Statutory rate/slab data needs annual verification
PF/ESI rates, Professional Tax slabs, Labour Welfare Fund rates, TDS
slabs, and the gratuity cap are all seeded at the rates known at
build time. All of these are revised periodically by government
notification. **This software does not self-update them** — someone
needs to check and update the seeded config at least once a year
(TDS slabs, every financial year without exception).

### Professional Tax / Labour Welfare Fund coverage is partial
Seeded for Kerala, Tamil Nadu, Karnataka, and Andhra Pradesh only —
the four states the first deployment needed. A client operating
elsewhere needs new configuration records added (the calculation
engine supports any state; only the seed data is limited). See
`docs/SETUP_GUIDE.md` §5.2.

### Overtime pay is not correctly computed for Daily Wage contracts
`bpro_overtime`'s OT rate is derived from CTC-implied monthly gross
(`ctc_annual/12`), which is undefined for a Daily Wage contract — those
use `daily_wage_rate` instead, set by `bpro_employment_type`. A Daily
Wage employee's OT will compute to zero rather than error, which is
silently wrong rather than loudly wrong. **Recommendation**: don't
rely on the OT module for Daily Wage workers yet — compute their
overtime manually (Factories Act: their own daily rate ÷ working
hours, doubled) until a daily-rate-aware OT path is built.

### Contract Labour is flagged, not fully modelled
`bpro_employment_type`'s "Contract Labour" category defaults PF/ESI
off (the labour contractor's own establishment is normally the
responsible party, not the principal employer) but otherwise treats
it like any other contract in this system. In most real setups,
contract labour is paid through the contractor's own invoice, not run
through this payroll at all — if that's the client's actual practice,
these workers likely shouldn't be `hr.contract` records here in the
first place, just tracked elsewhere (site access/safety registers) if
tracked at all.

---

## Recruitment

### WhatsApp notifications are not wired up
Interview scheduling and offer delivery currently notify by email
only. The code has a single, clearly marked integration point where a
WhatsApp Business API send would plug in once the client has API
credentials (Meta Cloud API, Twilio, or Gupshup) — this was a
deliberate scoping decision, not an oversight, made when no such
account existed yet.

---

## Attendance

### No live biometric device connector
Attendance import is CSV/Excel-based (device-agnostic — works with
any device whose bundled software can export a daily log). There is
no live pull integration for any specific device brand. Building one
requires knowing the actual device model and whether it shares a
network with this Odoo instance — see `docs/SETUP_GUIDE.md` §5.4.

---

## Infrastructure (see `docs/SETUP_GUIDE.md` for the fixes)

- No automated backups until `scripts/backup_db.sh` is scheduled via
  cron on the actual deployment server.
- No TLS/HTTPS until `docker-compose.prod.yml` + `deploy/Caddyfile`
  are deployed with the client's real domain.
- No outbound email until an SMTP relay is configured.

---

## What this list is *not*

This is a technical scope document, not a legal or compliance opinion.
It does not constitute tax, legal, or statutory-compliance advice —
the client's own CA/compliance team should review payroll output
(especially PT/LWF/TDS figures and the ESI items above) before relying
on it for real statutory filings.
