# Test datasets

Five CSV files for testing the Farm Records Assistant. Expected results below were produced by the app's own `data_utils` code.
Upload each file in the sidebar. (For the *missing column* case, also use `sample_data/flawed_missing_column.csv`.)

## 01_clean_full_season.csv - Clean, large season

Normal journey at scale: crop/date filters, all three charts, date-range comparison, report download. Expect no issues.

- Rows read: **100**, kept: **100**; crops: Cassava, Maize, Pepper, Plantain, Tomato
- Dates: 2026-08-01 to 2026-10-31
- Totals: **4,796 kg**, revenue **GHS 43,126**, expenses **GHS 16,509**, recorded balance **GHS 26,617**
- Highest revenue crop: **Tomato**
- Issues: none

## 02_messy_but_recoverable.csv - Messy but recoverable

Header spelling/spacing, mixed date formats, crop casing, thousands separator ('1,280'), 'N/A', extra Notes column. Expect it to load with notes and one missing-expense warning.

- Rows read: **10**, kept: **10**; crops: Cassava, Maize, Pepper, Plantain, Tomato
- Dates: 2026-10-01 to 2026-10-15
- Totals: **440 kg**, revenue **GHS 4,490**, expenses **GHS 960**, recorded balance **GHS 3,530**
- Highest revenue crop: **Cassava**
- Issues the app should report:
  - Missing expenses_ghs x1 (CSV rows 6)
- Notes: Extra column(s) ignored: notes. 5 crop name(s) tidied (spaces/capitalisation), e.g. 'tomato ' -> 'Tomato'.

## 03_zeros_and_missing_costs.csv - Zeros and missing costs

Valid data that needs care: Okra sells nothing, some expenses blank. Check 'recorded balance' wording, 0% revenue share, excluded-entry caption, and that the AI doesn't call anything profit.

- Rows read: **12**, kept: **12**; crops: Garden Egg, Maize, Okra, Tomato
- Dates: 2026-09-01 to 2026-09-12
- Totals: **453 kg**, revenue **GHS 2,650**, expenses **GHS 700**, recorded balance **GHS 1,950**
- Highest revenue crop: **Tomato**
- Issues the app should report:
  - Missing expenses_ghs x3 (CSV rows 3, 6, 10)

## 04_hostile_edge_cases.csv - Hostile edge cases

Duplicate, same crop twice on a day, text, 'inf', negative, blank crop, bad dates, 'GHS 260', blank/negative expense, plus a GHS 9,999,999 outlier.

- Rows read: **15**, kept: **11**; crops: Cassava, Maize, Pepper, Plantain, Tomato
- Dates: 2026-10-01 to 2026-10-13
- Totals: **320 kg**, revenue **GHS 10,003,679**, expenses **GHS 875**, recorded balance **GHS 10,002,804**
- Highest revenue crop: **Tomato**
- Issues the app should report:
  - Blank crop name x1 (CSV rows 9)
  - Missing or unreadable date x2 (CSV rows 11, 14)
  - Text/non-numeric value in harvested_kg x1 (CSV rows 6)
  - Negative value in harvested_kg x1 (CSV rows 8)
  - Text/non-numeric value in sales_revenue_ghs x2 (CSV rows 7, 10)
  - Missing expenses_ghs x1 (CSV rows 12)
  - Negative value in expenses_ghs x1 (CSV rows 13)
  - Exact duplicate row x1 (CSV rows 3)
  - Same crop twice on the same date x2 (CSV rows 4, 5)

## 05_maize_revenue_story.csv - Maize revenue story

Maize harvest rises weekly while revenue falls then partly recovers and expenses climb. Ask 'Why did maize revenue change?' - the AI must describe the recorded pattern and say prices, quantities sold, weather etc. are not in the data.

- Rows read: **27**, kept: **27**; crops: Cassava, Maize, Tomato
- Dates: 2026-08-03 to 2026-10-29
- Totals: **1,462 kg**, revenue **GHS 11,179**, expenses **GHS 2,786**, recorded balance **GHS 8,393**
- Highest revenue crop: **Maize**
- Issues: none

## Known gap worth discussing

`04_hostile_edge_cases.csv` contains a revenue of 9,999,999 for one Tomato day. It is a valid number so the app includes it and distorts the totals. Outlier detection is not part of the brief, but adding a check (for example, flag values far above the crop's median) is a good *small change* for your demo.
