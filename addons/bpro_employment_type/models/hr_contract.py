from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrContract(models.Model):
    _inherit = "hr.contract"

    employment_category = fields.Selection(
        [
            ("permanent", "Permanent"),
            ("ftc", "Fixed Term Contract (FTC)"),
            ("trainee", "Trainee / Apprentice"),
            ("daily_wage", "Daily Wage"),
            ("contract_labour", "Contract Labour (via Contractor)"),
        ],
        default="permanent",
        required=True,
        tracking=True,
        help="What KIND of engagement this is - separate from "
        "bpro_probation's probation_state, which tracks whether the "
        "initial trial period has ended (applies regardless of "
        "category). A Fixed Term Contract hire can still be on "
        "probation within their FTC term.",
    )
    daily_wage_rate = fields.Float(
        string="Daily Wage Rate",
        help="Per-day rate for Daily Wage contracts. Basic is computed "
        "as this x actual attendance days worked in the payslip period "
        "- not the CTC/12-prorated figure every other category uses.",
    )

    @api.onchange("employment_category")
    def _onchange_employment_category_defaults(self):
        for rec in self:
            if rec.employment_category == "trainee":
                # Registered apprentices under the Apprentices Act 1961
                # are generally outside PF/ESI coverage - default off,
                # HR can turn back on for a company's own broader,
                # informal use of "trainee" that isn't a registered
                # apprenticeship.
                rec.pf_applicable = False
                rec.esi_applicable = False
            elif rec.employment_category == "contract_labour":
                # Statutorily the labour contractor's own
                # establishment is normally the responsible party, not
                # the principal employer - see KNOWN_LIMITATIONS.md,
                # this category is flagged, not fully modelled.
                rec.pf_applicable = False
                rec.esi_applicable = False

    @api.constrains("employment_category", "date_end")
    def _check_ftc_has_end_date(self):
        for rec in self:
            if rec.employment_category == "ftc" and not rec.date_end:
                raise ValidationError(
                    "A Fixed Term Contract must have a Contract End "
                    "Date set - that IS the legal definition of a "
                    "fixed term."
                )

    @api.constrains("employment_category", "daily_wage_rate")
    def _check_daily_wage_rate(self):
        for rec in self:
            if rec.employment_category == "daily_wage" and rec.daily_wage_rate <= 0:
                raise ValidationError(
                    "A Daily Wage contract needs a Daily Wage Rate "
                    "greater than zero."
                )
