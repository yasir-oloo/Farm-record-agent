"""Regenerates the non-AI output examples in docs/examples from the sample data.

Run:  python scripts/generate_examples.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import data_utils as du  # noqa: E402
import report as rp  # noqa: E402

OUT = ROOT / "docs" / "examples"
OUT.mkdir(parents=True, exist_ok=True)


def load(name):
    return du.clean_records(du.read_csv_bytes((ROOT / "sample_data" / name).read_bytes()))


def view_summary(df, crops=None):
    crops = crops or sorted(df["crop"].unique())
    start, end = df["date"].min(), df["date"].max()
    view = du.filter_records(df, crops, start, end)
    return du.summarize(view, crops, start, end)


# 1. Normal journey: starter file
df, q = load("agriculture_sample_records.csv")
s = view_summary(df)
(OUT / "01_starter_summary.json").write_text(json.dumps(s["totals"], indent=2))
(OUT / "02_sample_report_no_ai.md").write_text(rp.build_report(s, q, "agriculture_sample_records.csv", None))
(OUT / "03_maize_filter_summary.json").write_text(json.dumps(
    {k: view_summary(df, ["Maize"])[k] for k in ("filters", "records_in_view", "totals", "by_crop")}, indent=2))

# 2. Data quality: deliberately flawed file
df2, q2 = load("flawed_records.csv")
lines = [f"# Data check: flawed_records.csv", "",
         f"{q2.rows_in} rows read, {q2.rows_kept} kept.", "",
         "| Check | Found | CSV rows | How it was handled |", "|---|---|---|---|"]
lines += [f"| {i['Check']} | {i['Found']} | {i['CSV rows']} | {i['How it was handled']} |" for i in q2.issues]
lines += ["", "Totals after handling: " + json.dumps(view_summary(df2)["totals"])]
(OUT / "04_flawed_file_quality_check.md").write_text("\n".join(lines) + "\n")

# 3. Missing column: blocked with an explanation
_, q3 = load("flawed_missing_column.csv")
(OUT / "05_missing_column_error.md").write_text("# flawed_missing_column.csv\n\n" + "\n".join(q3.errors) + "\n")
print("Wrote examples to", OUT)
