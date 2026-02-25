"""
All-In Margin Calculator - Flask Backend
NADB Infrastructure Finance Tool
Calculates effective interest rates (IRR) and weighted average life for loan transactions.
"""

from flask import Flask, render_template, request, jsonify, Response
from datetime import datetime
from dateutil.relativedelta import relativedelta
import numpy_financial as npf
import numpy as np
import csv
import io
import json
import math

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def parse_date(s):
    """Parse ISO date string to datetime."""
    return datetime.strptime(s, "%Y-%m-%d")


def period_date(start: datetime, period: int, frequency_months: int) -> datetime:
    """Return the date for a given period index (period 0 = start)."""
    return start + relativedelta(months=period * frequency_months)


def days_between(d1: datetime, d2: datetime) -> int:
    """Actual days between two dates."""
    return (d2 - d1).days


# ---------------------------------------------------------------------------
# Amortization profile
# ---------------------------------------------------------------------------

def adhoc_payment(loan_amount: float, period_months: int,
                  adhoc_table: list, use_percent: bool) -> float:
    """
    Look up the amortization payment for the given period_months offset.

    adhoc_table: list of {"month": int, "value": float} sorted by month.
    use_percent: if True, value is % of loan_amount (e.g. 1.5 → 1.5%); else dollar amount.
    Returns the payment amount for this period.
    """
    if not adhoc_table:
        return 0.0

    # Find the closest month <= period_months
    applicable = None
    for row in sorted(adhoc_table, key=lambda r: r["month"]):
        if row["month"] <= period_months:
            applicable = row
        else:
            break

    if applicable is None:
        return 0.0

    value = applicable["value"]
    if use_percent:
        return loan_amount * (value / 100.0)
    else:
        return value


# ---------------------------------------------------------------------------
# Core amortization schedule
# ---------------------------------------------------------------------------

def build_schedule(params: dict) -> list:
    """
    Build the full period-by-period amortization schedule.

    Returns a list of dicts, one per period (0 to num_periods inclusive).
    """
    loan_amount      = float(params["loan_amount"])
    num_periods      = int(params["num_periods"])
    draw_period      = int(params["draw_period"])
    grace_periods    = int(params.get("grace_periods", num_periods))
    frequency        = params["frequency"]           # Monthly | Quarterly | Semiannually
    margin_draw      = float(params["margin_draw"])   # decimal, e.g. 0.0158
    margin_after     = float(params["margin_after"])
    step_up          = float(params.get("step_up", 0))
    step_up_period   = int(params.get("step_up_period", 0))
    upfront_fee_rate = float(params.get("upfront_fee_rate", 0))
    commit_fee_rate  = float(params.get("commitment_fee_rate", 0))
    disbursement_str = params["disbursement_date"]
    amort_profile    = params["amortization_profile"]  # Bullet | Ad-hoc
    adhoc_table      = params.get("adhoc_table", [])    # [{month, value}]
    adhoc_use_pct    = params.get("adhoc_use_percent", True)

    freq_months = {"Monthly": 1, "Quarterly": 3, "Semiannually": 6}[frequency]
    disburse_dt = parse_date(disbursement_str)

    schedule = []
    balance = 0.0

    for p in range(num_periods + 1):
        row = {}
        row["period"] = p
        p_date = period_date(disburse_dt, p, freq_months)
        row["date"] = p_date.strftime("%Y-%m-%d")

        # Period 0: initial draw
        if p == 0:
            row["days"]           = 0
            row["beginning_bal"]  = 0.0
            row["draws"]          = loan_amount
            row["amortization"]   = 0.0
            row["interest"]       = 0.0
            row["upfront_fee"]    = loan_amount * upfront_fee_rate
            row["commitment_fee"] = 0.0
            row["ending_bal"]     = loan_amount
            balance = loan_amount

        else:
            prev_date = period_date(disburse_dt, p - 1, freq_months)
            days = days_between(prev_date, p_date)
            row["days"] = days

            beginning_bal = balance
            row["beginning_bal"] = beginning_bal

            # No draws after period 0 in this model
            row["draws"] = 0.0

            # Margin: draw vs. post-draw, plus optional step-up
            if p <= draw_period:
                margin = margin_draw
            else:
                margin = margin_after
            if step_up_period > 0 and p >= step_up_period:
                margin += step_up

            # Interest accrual (during grace periods)
            if p <= grace_periods and beginning_bal > 0:
                interest = margin * beginning_bal * (days / 360.0)
            else:
                interest = 0.0
            row["interest"] = round(interest, 6)

            # Upfront fee: only at period 0 (already handled above)
            row["upfront_fee"] = 0.0

            # Commitment fee: on undrawn balance during draw period
            if p <= draw_period:
                undrawn = max(loan_amount - beginning_bal, 0.0)
                commit_fee = undrawn * commit_fee_rate * (days / 360.0)
            else:
                commit_fee = 0.0
            row["commitment_fee"] = round(commit_fee, 6)

            # Amortization
            if amort_profile == "Bullet":
                if p == num_periods:
                    amort = beginning_bal   # Full repayment at final period
                else:
                    amort = 0.0
            else:
                # Ad-hoc: look up by month offset from disbursement date
                period_months_offset = (
                    (p_date.year - disburse_dt.year) * 12
                    + (p_date.month - disburse_dt.month)
                )
                amort = adhoc_payment(loan_amount, period_months_offset,
                                      adhoc_table, adhoc_use_pct)
                # Cap to remaining balance (never let balance go negative)
                amort = min(amort, beginning_bal)

            row["amortization"] = round(amort, 6)

            ending_bal = beginning_bal + row["draws"] - amort
            row["ending_bal"] = round(max(ending_bal, 0.0), 6)
            balance = row["ending_bal"]

        schedule.append(row)

    return schedule


# ---------------------------------------------------------------------------
# Cash flow arrays & IRR
# ---------------------------------------------------------------------------

def build_cashflow_arrays(schedule: list, draw_period: int) -> dict:
    """
    Build the four cash flow arrays (T, U, V, Z) from the amortization schedule.

    From lender's perspective:
      positive = inflow (interest received, principal repaid)
      negative = outflow (loan disbursed)

    Column T: IR Spread (interest + principal only, no fees)
    Column U: T + Upfront Fee
    Column V: U + Commitment Fee (= All-in Margin)
    Column Z: V + Reserve (not implemented in MVP; same as V)
    """
    col_T, col_U, col_V = [], [], []

    for row in schedule:
        cf_base = row["interest"] + row["amortization"] - row["draws"]
        col_T.append(cf_base)
        col_U.append(cf_base + row["upfront_fee"])
        col_V.append(cf_base + row["upfront_fee"] + row["commitment_fee"])

    return {"T": col_T, "U": col_U, "V": col_V}


def annualized_irr(cashflows: list, frequency: str) -> float:
    """Calculate IRR and annualize by payment frequency multiplier."""
    multiplier = {"Monthly": 12, "Quarterly": 4, "Semiannually": 2}[frequency]
    try:
        arr = np.array(cashflows, dtype=float)
        if np.all(arr == 0):
            return 0.0
        irr_per_period = npf.irr(arr)
        if irr_per_period is None or np.isnan(irr_per_period):
            return 0.0
        return irr_per_period * multiplier
    except Exception:
        return 0.0


def calculate_irr_components(schedule: list, params: dict) -> dict:
    """Return the IRR component breakdown."""
    draw_period = int(params["draw_period"])
    frequency   = params["frequency"]

    cfs = build_cashflow_arrays(schedule, draw_period)

    ir_spread   = annualized_irr(cfs["T"], frequency)
    irr_with_uf = annualized_irr(cfs["U"], frequency)
    irr_all_in  = annualized_irr(cfs["V"], frequency)

    upfront_impact    = irr_with_uf - ir_spread
    commitment_impact = irr_all_in - irr_with_uf

    return {
        "ir_spread":         round(ir_spread * 100, 6),       # as %
        "upfront_impact":    round(upfront_impact * 100, 6),
        "commitment_impact": round(commitment_impact * 100, 6),
        "all_in_margin":     round(irr_all_in * 100, 6),
    }


# ---------------------------------------------------------------------------
# Weighted Average Life
# ---------------------------------------------------------------------------

def calculate_wal(schedule: list, frequency_months: int) -> float:
    """
    WAL = SUM(period_months × amortization / total_amortization) / 12

    period_months = period_index × frequency_months
    """
    total_amort = sum(row["amortization"] for row in schedule)
    if total_amort == 0:
        return 0.0

    weighted = 0.0
    for row in schedule:
        if row["amortization"] > 0:
            period_months_offset = row["period"] * frequency_months
            weighted += period_months_offset * (row["amortization"] / total_amort)

    return round(weighted / 12.0, 4)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate(schedule: list, loan_amount: float) -> dict:
    total_draws = sum(row["draws"] for row in schedule)
    total_amort = sum(row["amortization"] for row in schedule)
    final_bal   = schedule[-1]["ending_bal"]

    draw_ok   = abs(total_draws - loan_amount) <= 1.0
    neg_bal   = any(row["ending_bal"] < -0.01 for row in schedule)

    return {
        "draws_total":   round(total_draws, 2),
        "amort_total":   round(total_amort, 2),
        "final_balance": round(final_bal, 2),
        "draw_status":   "OK" if draw_ok else "Review Draw",
        "balance_ok":    not neg_bal,
    }


# ---------------------------------------------------------------------------
# Flask routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/calculate", methods=["POST"])
def calculate():
    try:
        params = request.get_json(force=True)

        freq_months = {"Monthly": 1, "Quarterly": 3, "Semiannually": 6}[params["frequency"]]

        schedule   = build_schedule(params)
        irr_comps  = calculate_irr_components(schedule, params)
        wal        = calculate_wal(schedule, freq_months)
        validation = validate(schedule, float(params["loan_amount"]))

        # Serialize schedule rows (round display values)
        sched_out = []
        for row in schedule:
            sched_out.append({
                "period":          row["period"],
                "date":            row["date"],
                "days":            row["days"],
                "beginning_bal":   round(row["beginning_bal"], 2),
                "draws":           round(row["draws"], 2),
                "amortization":    round(row["amortization"], 2),
                "interest":        round(row["interest"], 2),
                "upfront_fee":     round(row["upfront_fee"], 2),
                "commitment_fee":  round(row["commitment_fee"], 2),
                "ending_bal":      round(row["ending_bal"], 2),
            })

        return jsonify({
            "success":    True,
            "schedule":   sched_out,
            "irr":        irr_comps,
            "wal":        wal,
            "validation": validation,
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/export/csv", methods=["POST"])
def export_csv():
    try:
        params = request.get_json(force=True)
        freq_months = {"Monthly": 1, "Quarterly": 3, "Semiannually": 6}[params["frequency"]]

        schedule = build_schedule(params)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Period", "Date", "Days",
            "Beginning Balance", "Draws", "Amortization",
            "Interest", "Upfront Fee", "Commitment Fee", "Ending Balance"
        ])
        for row in schedule:
            writer.writerow([
                row["period"],
                row["date"],
                row["days"],
                round(row["beginning_bal"], 2),
                round(row["draws"], 2),
                round(row["amortization"], 2),
                round(row["interest"], 2),
                round(row["upfront_fee"], 2),
                round(row["commitment_fee"], 2),
                round(row["ending_bal"], 2),
            ])

        csv_data = output.getvalue()
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=amortization_schedule.csv"}
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


if __name__ == "__main__":
    app.run(debug=True, port=5000)
