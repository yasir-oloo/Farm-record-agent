# Data check: flawed_records.csv

10 rows read, 7 kept.

| Check | Found | CSV rows | How it was handled |
|---|---|---|---|
| Blank crop name | 1 | 9 | Row removed. |
| Missing or unreadable date | 1 | 7 | Row removed (use YYYY-MM-DD). |
| Text/non-numeric value in harvested_kg | 1 | 5 | Entry left blank; row kept; excluded from the harvested_kg total (not counted as zero). |
| Negative value in harvested_kg | 1 | 8 | Entry treated as invalid and left blank; row kept; excluded from the harvested_kg total (not counted as zero). |
| Missing sales_revenue_ghs | 1 | 6 | Entry left blank; row kept; excluded from the sales_revenue_ghs total (not counted as zero). |
| Text/non-numeric value in expenses_ghs | 1 | 10 | Entry left blank; row kept; excluded from the expenses_ghs total (not counted as zero). |
| Exact duplicate row | 1 | 3 | First copy kept; extras removed. |

Totals after handling: {"harvested_kg": 215.0, "sales_revenue_ghs": 2090.0, "expenses_ghs": 630.0, "recorded_balance_ghs": 1460.0}
