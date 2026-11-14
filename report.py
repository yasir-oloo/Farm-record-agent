"""Builds the downloadable Markdown report, keeping facts and possibilities apart."""
from __future__ import annotations

from datetime import datetime

from data_utils import QualityReport, fmt_kg, fmt_ghs

GENERIC_CHECKLIST = """- Compare the highest- and lowest-revenue crops against how much of each was harvested and sold.
- Check whether any costs (labour, seed, transport, fertiliser) are missing from the expenses column.
- Look at dates where revenue is low or zero and ask what happened on those days.
- Confirm whether harvested kg and sold kg are the same; the records do not say how much was sold.
- Add notes on prices, weather, buyers or market days to the records to explain changes."""


def build_report(summary: dict, quality: QualityReport | None, source_name: str,
                 ai_text: str | None) -> str:
    t, f = summary["totals"], summary["filters"]
    lines = [
        "# Farm Records Report", "",
        f"*Generated {datetime.now():%Y-%m-%d %H:%M} from `{source_name}`*", "",
        f"**View:** crops: {', '.join(f['crops']) or 'none'} | dates: {f['date_from']} to {f['date_to']} "
        f"| {summary['records_in_view']} record(s)", "",
        "## 1. Data quality", "",
    ]
    if quality and quality.issues:
        lines += [f"{quality.rows_in} row(s) read, {quality.rows_kept} kept after checks. Issues found:", ""]
        lines += ["| Check | Found | CSV rows | How it was handled |", "|---|---|---|---|"]
        lines += [f"| {i['Check']} | {i['Found']} | {i['CSV rows']} | {i['How it was handled']} |" for i in quality.issues]
    elif quality:
        lines.append(f"{quality.rows_in} row(s) read, {quality.rows_kept} kept. No data-quality issues found.")
    left_out = summary["entries_left_out_of_totals_because_blank_or_invalid"]
    if any(left_out.values()):
        lines += ["", "In the current view, blank/invalid entries are excluded from totals: "
                  + ", ".join(f"{k}: {v}" for k, v in left_out.items() if v) + "."]

    lines += ["", "## 2. Observed facts (calculated by Python from the records)", "",
              "| Measure | Value |", "|---|---|",
              f"| Total harvest | {fmt_kg(t['harvested_kg'])} |",
              f"| Recorded sales revenue | {fmt_ghs(t['sales_revenue_ghs'])} |",
              f"| Recorded expenses | {fmt_ghs(t['expenses_ghs'])} |",
              f"| Recorded balance (revenue - recorded expenses) | {fmt_ghs(t['recorded_balance_ghs'])} |", "",
              "*The recorded balance is not verified profit: the file may omit costs or other entries.*", "",
              "### By crop", "",
              "| Crop | Records | Harvest (kg) | Revenue (GHS) | Expenses (GHS) | Recorded balance (GHS) | Share of revenue |",
              "|---|---|---|---|---|---|---|"]
    lines += [f"| {c['crop']} | {c['records']} | {c['harvested_kg']:,.2f} | {c['sales_revenue_ghs']:,.2f} | "
              f"{c['expenses_ghs']:,.2f} | {c['recorded_balance_ghs']:,.2f} | {c['revenue_share_pct']:.1f}% |"
              for c in summary["by_crop"]]
    top = summary["highest_revenue_crop"]
    if top:
        lines += ["", f"- Highest recorded sales revenue: **{top['crop']}** ({fmt_ghs(top['sales_revenue_ghs'])})."]
    for c in summary["revenue_change_first_to_last_record_by_crop"]:
        lines.append(f"- {c['crop']}: recorded revenue went from {fmt_ghs(c['first_revenue_ghs'])} on "
                     f"{c['first_date']} to {fmt_ghs(c['last_revenue_ghs'])} on {c['last_date']} "
                     f"({'+' if c['change_ghs'] >= 0 else ''}{c['change_ghs']:,.2f}).")

    lines += ["", "## 3. Possible explanations (NOT verified by the records)", ""]
    if ai_text:
        lines += ["*Written by Google Gemini from the summary above. These are possibilities to investigate, "
                  "not conclusions.*", "", ai_text]
    else:
        lines += ["*Generic prompts for further checking; no AI explanation was generated for this view.*", "",
                  GENERIC_CHECKLIST]

    lines += ["", "## 4. Limitations", "",
              "- Based only on the uploaded records; sales quantities, prices, yields per hectare and causes are not in the data.",
              "- Blank, text or negative entries are left out of totals, not treated as zero.",
              "- Recorded balance is revenue minus recorded expenses only."]
    return "\n".join(lines) + "\n"
