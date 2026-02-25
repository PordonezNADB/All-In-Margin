# All-In Margin Calculator: From Excel to Claude Code
## Executive Summary & Workflow

---

## What You're Building

A web application that replicates your Excel "All-In Margin Calculator" for calculating effective interest rates and loan repayment timelines. Instead of updating Excel spreadsheets, analysts will input parameters into a form and get instant results with an interactive dashboard.

**Key Outputs:**
- **All-in Margin (%)** - Effective annual interest rate including all fees and spreads, calculated as IRR
- **Weighted Average Life (years)** - Average time until principal is fully repaid
- **Detailed Amortization Schedule** - Period-by-period breakdown of draws, interest, fees, and balances

**Key Capability:**
- Users can edit custom amortization profiles on the fly (choose month ranges and corresponding payment percentages or dollar amounts)

---

## Why Three Files?

| File | Purpose | Use Case |
|------|---------|----------|
| **all_in_margin_calculator_specs.json** | Technical bible with all formulas, business rules, and example data | Reference for Claude Code when building calculations |
| **amortization_profile_template.csv** | Example amortization schedule that users can customize | Show Claude Code what user-editable data looks like |
| **CLAUDE_CODE_BUILD_GUIDE.md** | Step-by-step prompts and explanations for Claude Code | Copy-paste into Claude Code terminal |
| **FORMULA_REFERENCE_CARD.md** | Code snippets and formulas in Python | Quick lookup when debugging calculations |

---

## Workflow: Getting From Excel to Working App

### Phase 1: Setup (15 minutes)
```
1. Open Claude Code in your terminal
2. Copy the INITIAL BRIEF from CLAUDE_CODE_BUILD_GUIDE.md (Stage 1)
3. Paste into Claude Code
4. Wait for Claude Code to ask clarifying questions
```

### Phase 2: Form & Structure (45-60 minutes)
Claude Code will build:
- HTML/React form with all 13 input fields
- Python backend framework to handle calculations
- Dropdown/toggle logic for "Bullet" vs "Ad-hoc" amortization

**Your job:** Tell Claude Code if the form layout looks good, or ask for changes.

Example feedback:
```
"Can you add a 'Reset' button that clears all fields? 
Also, the date pickers should default to today's date if possible."
```

### Phase 3: Amortization Schedule (60-90 minutes)
Claude Code builds the core calculation engine:
- Period date calculation (respecting Monthly/Quarterly/Semiannual frequency)
- Draws and amortization (handling both Bullet and Ad-hoc profiles)
- Interest, upfront fee, and commitment fee calculations
- Running balance tracking

**Your job:** Use the La Grulla example to validate:
```
Check that:
✓ Dates increment correctly (every 6 months for Semiannual)
✓ Draws total to $1.3M
✓ Interest is calculated correctly (~10k per period)
✓ Ending balance reaches ~zero by final period
```

If something's wrong, paste 5 sample rows and ask Claude Code to fix.

### Phase 4: IRR Calculations (30-45 minutes)
Claude Code implements the IRR engine:
- Separate cash flow arrays (T, U, V, Z columns from Excel)
- IRR solver using numpy-financial
- Component breakdown (IR Spread, Upfront Fee Impact, Commitment Fee Impact)
- Weighted Average Life calculation

**Your job:** Validate outputs match Excel:
```
Expected: All-in Margin = 1.57%, WAL = 14.69 years
Got: All-in Margin = [your number], WAL = [your number]

If off: "The IRR is calculating to [X]% but should be ~1.57%. 
Here are the first 5 cashflow values I'm getting: [paste]"
```

### Phase 5: Dashboard & Export (30-45 minutes)
Claude Code adds:
- Summary cards showing All-in Margin breakdown
- Weighted Average Life display
- Amortization table with formatting
- CSV export button

**Your job:** Polish the UI:
```
"Can you make the All-in Margin card bigger and highlight the final number? 
Also, add thousands separators to the currency columns in the table."
```

### Phase 6: Testing & Refinement (30-60 minutes)
Test with multiple scenarios:
- La Grulla (already defined above)
- Your own past project (if you have the inputs handy)
- Edge cases: $0 fees, bullet amortization, etc.

---

## Key Prompts You'll Use

### When Starting (Copy from Build Guide)
```
"I'm building an All-In Margin Calculator web application..."
[Full initial brief]
```

### When Claude Code Asks About Formulas
```
"Here's how the amortization schedule is built..."
[Data specification prompt]
```

### When IRR Isn't Working
```
"The All-in Margin I'm getting is [X]% but should be ~1.57%..."
[IRR calculation prompt]
```

### For Weighted Average Life
```
"Weighted Average Life (WAL) is the average time-to-repayment..."
[WAL calculation prompt]
```

### For UI Refinements
```
"Can you add [feature]? Here's what I'm thinking..."
[Your specific request]
```

---

## Red Flags & How to Fix Them

| Issue | Likely Cause | Fix |
|-------|--------------|-----|
| All-in Margin is 10x too high/low | Rate stored as percentage instead of decimal (1 vs 0.01) | Check: Is upfront fee 0 or 0.01? Should be 0 |
| Dates are incrementing by months, not periods | Not using the frequency multiplier | Check: Are you adding 1, 3, or 6 months based on frequency? |
| Balance goes negative in later periods | Amortization is too aggressive | Check: Is amortization_rate being applied as % to total, or $ amount? |
| IRR calculation returns 0 or error | Cashflow array structure is wrong | Check: First value should be negative (outflow), rest positive (inflows) |
| Interest looks too low | Not multiplying by (days/360) | Check: Interest = margin × balance × (days / 360), not margin × balance |
| Weighted Average Life is huge | Division error in months-to-years conversion | Check: Are you dividing by 12 at the end? |

---

## Estimated Timeline

| Phase | Time | Complexity |
|-------|------|-----------|
| Phase 1: Setup | 15 min | ⭐ |
| Phase 2: Form & Structure | 45-60 min | ⭐⭐ |
| Phase 3: Amortization Schedule | 60-90 min | ⭐⭐⭐ |
| Phase 4: IRR Calculations | 30-45 min | ⭐⭐⭐⭐ |
| Phase 5: Dashboard & Export | 30-45 min | ⭐⭐ |
| Phase 6: Testing & Refinement | 30-60 min | ⭐⭐ |
| **TOTAL** | **3-4 hours** | Average ⭐⭐⭐ |

This assumes Claude Code understands the financial concepts and you're iterating on calculations.

---

## What Claude Code Does Well

✅ Build forms and handle user input  
✅ Implement financial formulas once you explain them  
✅ Manage complex calculations and data structures  
✅ Create responsive HTML/React UIs  
✅ Generate export functionality (CSV, PDF)  
✅ Debug calculation logic when you provide examples  

## What You'll Need to Handle

❌ Explaining financial business logic clearly (interest accrual, fee timing, etc.)  
❌ Testing against your Excel file (Claude Code can't read .xlsx)  
❌ Validating accuracy with real project numbers  
❌ User acceptance and feedback (Claude Code can't interview users)  
❌ Deployment and security (Claude Code generates code, you deploy it)  

---

## Getting Started Right Now

1. **Copy the Initial Brief** from Stage 1 of CLAUDE_CODE_BUILD_GUIDE.md
2. **Open Claude Code** in your terminal
3. **Paste** the brief and hit Enter
4. **Wait** for Claude Code to ask clarifying questions (it might ask about reserves, day count conventions, etc.)
5. **Answer** any questions using the specs in all_in_margin_calculator_specs.json
6. **Start building** - Claude Code will generate skeleton code

---

## Success Criteria

You'll know it's done when:

- [ ] Form accepts all 13 input parameters
- [ ] La Grulla example produces All-in Margin ≈ 1.57% ± 0.05%
- [ ] La Grulla example produces WAL ≈ 14.69 years ± 0.1 years
- [ ] Amortization table shows 50 periods with dates 6 months apart
- [ ] Ad-hoc amortization toggle works and allows editing the schedule
- [ ] All-in Margin shows component breakdown
- [ ] Validation shows "OK" when draws equal total amount
- [ ] CSV export works and opens in Excel
- [ ] UI is clean and easy to use (no crashes, responsive on mobile if needed)

---

## Next Steps

1. **Read CLAUDE_CODE_BUILD_GUIDE.md completely** - You'll refer to it during development
2. **Keep FORMULA_REFERENCE_CARD.md open** - Copy Python snippets as needed
3. **Review all_in_margin_calculator_specs.json** - Understand the business logic
4. **Launch Claude Code and start the Initial Brief** - The journey begins!

---

## Questions Before You Start?

Some things to clarify with Claude Code early (it will ask):

1. **Reserves:** Should the app calculate reserve impacts, or just show them as optional?
2. **Date precision:** Does the app need to match Excel's date handling exactly?
3. **Rounding:** Should output be rounded to 2 decimals, 4 decimals, or exact precision?
4. **Frequency:** Can a loan have mixed frequencies (e.g., quarterly draws, monthly payments)?
5. **Export:** Should exported CSV match Excel format exactly, or just be usable data?

**Recommended answer:** For MVP, keep it simple - match the La Grulla example exactly, worry about edge cases later.

---

## Support from Claude Code

During development, Claude Code can help with:
- "Is this date calculation correct?" → Paste the code
- "Why is the IRR off?" → Paste 10 periods of cashflows
- "How do I format this table?" → Describe what you want
- "Can I add a chart?" → "Yes, using Chart.js/Plotly"

**In each case, provide:**
- What you're trying to do (1 sentence)
- The relevant code or data (5-10 lines max)
- What you expected vs. what you got

---

Good luck! You've got a solid specification, clear examples, and Claude Code has the chops to build this. The financial logic is the hardest part, but you've already figured that out in Excel—now it's just translating it to Python.

**You've got this. 🚀**
