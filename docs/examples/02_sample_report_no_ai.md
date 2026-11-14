# Farm Records Report

*Generated 2026-11-12 10:26 from `agriculture_sample_records.csv`*

**View:** crops: Cassava, Maize, Pepper, Plantain, Tomato | dates: 2026-09-01 to 2026-09-19 | 12 record(s)

## 1. Data quality

12 row(s) read, 12 kept. No data-quality issues found.

## 2. Observed facts (calculated by Python from the records)

| Measure | Value |
|---|---|
| Total harvest | 480 kg |
| Recorded sales revenue | GHS 3,820 |
| Recorded expenses | GHS 1,280 |
| Recorded balance (revenue - recorded expenses) | GHS 2,540 |

*The recorded balance is not verified profit: the file may omit costs or other entries.*

### By crop

| Crop | Records | Harvest (kg) | Revenue (GHS) | Expenses (GHS) | Recorded balance (GHS) | Share of revenue |
|---|---|---|---|---|---|---|
| Tomato | 3 | 85.00 | 1,120.00 | 355.00 | 765.00 | 29.3% |
| Maize | 3 | 150.00 | 890.00 | 350.00 | 540.00 | 23.3% |
| Pepper | 2 | 45.00 | 880.00 | 205.00 | 675.00 | 23.0% |
| Cassava | 2 | 125.00 | 490.00 | 190.00 | 300.00 | 12.8% |
| Plantain | 2 | 75.00 | 440.00 | 180.00 | 260.00 | 11.5% |

- Highest recorded sales revenue: **Tomato** (GHS 1,120).
- Cassava: recorded revenue went from GHS 280 on 2026-09-03 to GHS 210 on 2026-09-12 (-70.00).
- Maize: recorded revenue went from GHS 330 on 2026-09-01 to GHS 260 on 2026-09-14 (-70.00).
- Pepper: recorded revenue went from GHS 480 on 2026-09-07 to GHS 400 on 2026-09-15 (-80.00).
- Plantain: recorded revenue went from GHS 260 on 2026-09-08 to GHS 180 on 2026-09-17 (-80.00).
- Tomato: recorded revenue went from GHS 520 on 2026-09-01 to GHS 150 on 2026-09-19 (-370.00).

## 3. Possible explanations (NOT verified by the records)

*Generic prompts for further checking; no AI explanation was generated for this view.*

- Compare the highest- and lowest-revenue crops against how much of each was harvested and sold.
- Check whether any costs (labour, seed, transport, fertiliser) are missing from the expenses column.
- Look at dates where revenue is low or zero and ask what happened on those days.
- Confirm whether harvested kg and sold kg are the same; the records do not say how much was sold.
- Add notes on prices, weather, buyers or market days to the records to explain changes.

## 4. Limitations

- Based only on the uploaded records; sales quantities, prices, yields per hectare and causes are not in the data.
- Blank, text or negative entries are left out of totals, not treated as zero.
- Recorded balance is revenue minus recorded expenses only.
