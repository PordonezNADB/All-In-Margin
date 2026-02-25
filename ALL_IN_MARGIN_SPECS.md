# All-In Margin Calculator - Technical Specifications

## Project Overview
A web application that replicates Excel "All-In Margin Calculator" for calculating effective interest rates (IRR) and weighted average life for infrastructure loans.

## Input Parameters

### 1. Loan Amount
- **Label:** NADB Amount (USD)
- **Type:** Currency/Number
- **Example:** $1,300,000
- **Required:** Yes

### 2. Number of Periods
- **Label:** Number of Periods
- **Type:** Integer (1-360)
- **Example:** 50
- **Required:** Yes
- **Note:** This also sets Grace Periods automatically

### 3. Draw Period
- **Label:** Draw Period
- **Type:** Integer
- **Example:** 1
- **Required:** Yes
- **Help:** Period during which draws can occur

### 4. Amortization Profile
- **Label:** Amortization Profile
- **Type:** Dropdown
- **Options:** 
  - "Bullet" - Full repayment at end
  - "Ad-hoc" - Custom schedule (user editable)
- **Example:** "Ad-hoc"
- **Required:** Yes

### 5. Interest Payment Frequency
- **Label:** Interest Payment Frequency
- **Type:** Dropdown
- **Options:** "Monthly", "Quarterly", "Semiannually"
- **Example:** "Semiannually"
- **Required:** Yes
- **Impact:** Determines date increments AND IRR multiplier (12x, 4x, 2x)

### 6. Margin During Draw Period
- **Label:** Margin During Draw Period
- **Type:** Percentage (decimal)
- **Example:** 0.0158 (= 1.58%)
- **Required:** Yes

### 7. Margin After Draw Period
- **Label:** Margin After Draw Period
- **Type:** Percentage (decimal)
- **Example:** 0.0158
- **Required:** Yes

### 8. Step-Up (Optional)
- **Label:** Step Up
- **Type:** Percentage (decimal)
- **Example:** 0
- **Required:** No
- **Note:** Additional margin increase after step-up period

### 9. Step-Up Period (Optional)
- **Label:** Step Up Period
- **Type:** Integer
- **Example:** 0
- **Required:** No

### 10. Upfront Fee
- **Label:** Upfront Fee
- **Type:** Percentage (decimal)
- **Example:** 0 or 0.01 (1%)
- **Required:** No

### 11. Commitment Fee
- **Label:** Commitment Fee
- **Type:** Percentage (decimal)
- **Example:** 0
- **Required:** No
- **Note:** Charged on undrawn amount during draw period

### 12. Closing Date
- **Label:** Closing Date
- **Type:** Date
- **Example:** 2026-04-01
- **Required:** Yes

### 13. Disbursement Date
- **Label:** 1st Disbursement Date
- **Type:** Date
- **Example:** 2026-04-01
- **Required:** Yes

---

## Key Calculations

### All-In Margin (IRR)
**What it is:** Effective annual interest rate including interest spread + upfront fees + commitment fees

**Formula:** IRR(combined cash flows) × IRR_Multiplier
- IRR_Multiplier = 12 (Monthly) OR 4 (Quarterly) OR 2 (Semiannually)

**Example Output:** 1.5723% (for La Grulla)

### Weighted Average Life
**What it is:** Average time until principal is fully repaid, weighted by payment timing

**Formula:** SUM(Period × Payment% / Total) / 12 (to convert months to years)

**Example Output:** 14.688 years (for La Grulla)

### Components of All-In Margin
1. **IR Spread** - Base interest rate (from interest payments only)
2. **+ Upfront Fee Impact** - Incremental IRR from one-time upfront fee
3. **+ Commitment Fee Impact** - Incremental IRR from fee on undrawn amount
4. **= All-in Margin (IRR)** - Total effective rate

---

## Amortization Schedule Calculation

### Period-by-Period Logic

For each period (0 to # of Periods):

**Period 0 (Initial):**
- Date = Disbursement Date
- Draws = 100% of loan amount
- Amortization = 0
- Balance = Loan Amount

**Period N (N > 0):**
- Date = Previous Date + Frequency Months
  - Monthly: +1 month
  - Quarterly: +3 months
  - Semiannually: +6 months
- Days = Actual days between current and previous date
- Interest = IF(Period ≤ Grace Periods, Margin × Balance × Days/360, 0)
- Upfront Fee = IF(Period = Draw Period AND Date = Disburse Date, Loan × Upfront%, 0)
- Commitment Fee = IF(Period ≤ Draw Period, (Loan - Balance) × Commitment% × Days/360, 0)
- Amortization = Get from Profile (Bullet or Ad-hoc)
- Ending Balance = Beginning Balance + Draws - Amortization

### Bullet Amortization
```
Period 0: Draw full amount, amortization = 0
Period 1-N: Amortization = 0
Period N (final): Amortization = Full remaining balance
```

### Ad-Hoc Amortization
User provides custom table with Month → Amortization % pairs:
```
Example:
Month 0 → 0%
Month 33 → 1%
Month 45 → 2%
Month 57 → 3%
...etc
```

For each period:
1. Calculate month = (Period_Year - Start_Year) × 12 + (Period_Month - Start_Month)
2. Find closest month ≤ period_month in the table
3. Get amortization % for that month
4. Payment = Loan Amount × Amortization%

---

## Cash Flow Arrays (For IRR Calculation)

These are the 4 separate cash flow arrays used to calculate different versions of IRR:

### Column T: IR Spread (Base Interest Only)
```
IF(Period ≤ Draw Period):
  CF = Interest - Draws + Amortization
ELSE:
  CF = 0
```

### Column U: IR Spread + Upfront Fee
```
CF = Column T + Upfront Fee Payment
```

### Column V: All Fees (Complete)
```
CF = Column U + Commitment Fee
```

### Column Z: Net of Reserves (If Applicable)
```
Reserve = -(Ending Balance) × Probability of Default × Loss Given Default
CF = Column V + Reserve
```

---

## Calculation Formulas (Python Implementation)

### Interest Calculation
```
if period <= grace_periods:
    interest = margin * beginning_balance * (days_in_period / 360)
else:
    interest = 0
```

### Upfront Fee
```
if period <= draw_period AND period < grace_period AND date == disbursement_date:
    upfront_fee = loan_amount * upfront_fee_rate
else:
    upfront_fee = 0
```

### Commitment Fee
```
if period <= draw_period:
    undrawn = loan_amount - cumulative_draws
    commitment_fee = undrawn * commitment_rate * (days_in_period / 360)
else:
    commitment_fee = 0
```

### IRR Calculation
```
import numpy_financial as npf

irr_value = npf.irr(cashflows)  # Returns decimal (e.g., 0.00786)
annualized_irr = irr_value * irr_multiplier
# irr_multiplier: 12 (monthly), 4 (quarterly), 2 (semiannually)
```

### Weighted Average Life
```
total_principal = sum(all amortization payments)
weighted_sum = 0

for each period:
    if amortization > 0:
        weight = period_number * (amortization / total_principal)
        weighted_sum += weight

wal_years = weighted_sum / 12
```

---

## Validation Rules

1. **Draws Match Total:** SUM(all draws) = NADB Amount → Status "OK" or "Review Draw"
2. **Balance Never Negative:** Ending Balance ≥ 0 for all periods
3. **IRR Convergence:** IRR calculation returns valid number (not NaN)

---

## Example: La Grulla

**Inputs:**
- NADB Amount: $1,300,000
- Number of Periods: 50
- Draw Period: 1
- Grace Periods: 50
- Amortization: Ad-hoc
- Frequency: Semiannually
- Margin During Draw: 1.58%
- Margin After Draw: 1.58%
- Upfront Fee: 0%
- Commitment Fee: 0%
- Closing Date: April 1, 2026
- Disbursement Date: April 1, 2026

**Expected Outputs:**
- All-in Margin: 1.5723% (±0.05%)
- Weighted Average Life: 14.688 years (±0.1%)
- Validation Status: OK

---

## Ad-Hoc Amortization Profile Table

Users can customize this table:

| Month | Amortization Amount or % | Description |
|-------|--------------------------|-------------|
| 0 | 0 | Initial period - no amortization |
| 33 | 1% | Year 2.75 |
| 45 | 2% | Year 3.75 |
| 57 | 3% | Year 4.75 |
| ... | ... | ... |
| 297 | 23% | Year 24.75 |

Users can:
- Edit existing rows
- Add new rows
- Change values (% or $)
- Delete rows (with validation)

---

## Implementation Notes

**Date Handling:**
- Use Python `datetime` + `dateutil.relativedelta` for robust date math
- EOMONTH equivalent: `date + relativedelta(months=increment)`

**Financial Precision:**
- Use `decimal.Decimal` for currency calculations
- Store rates as decimals (0.0158, not 1.58)
- Keep full precision internally, round only for display

**IRR Solver:**
- Use `numpy_financial.irr()` or `scipy.optimize.fsolve()`
- Provide error handling for NaN/convergence failures
- If calculation fails, default to 0

---
