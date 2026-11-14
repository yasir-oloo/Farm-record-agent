import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import pytest

import main as ai_client
import data_utils as du

DATA = Path(__file__).resolve().parents[1] / "sample_data"


def load(name):
    return du.clean_records(du.read_csv_bytes((DATA / name).read_bytes()))


def summary_for(df):
    crops = sorted(df["crop"].unique())
    return du.summarize(df, crops, df["date"].min(), df["date"].max())


def test_starter_totals_match_brief():
    df, q = load("agriculture_sample_records.csv")
    assert q.ok and not q.issues
    t = summary_for(df)["totals"]
    assert t["harvested_kg"] == 480
    assert t["sales_revenue_ghs"] == 3820
    assert t["expenses_ghs"] == 1280
    assert t["recorded_balance_ghs"] == 2540


def test_missing_column_blocks_totals():
    df, q = load("flawed_missing_column.csv")
    assert df is None and not q.ok
    assert "expenses_ghs" in q.errors[0]


def test_flawed_file_is_flagged_and_handled():
    df, q = load("flawed_records.csv")
    assert q.ok and q.rows_in == 10 and q.rows_kept == 7
    checks = " | ".join(i["Check"] for i in q.issues)
    for expected in ["Blank crop", "unreadable date", "Text/non-numeric value in harvested_kg",
                     "Negative value in harvested_kg", "Missing sales_revenue_ghs",
                     "Text/non-numeric value in expenses_ghs", "Exact duplicate"]:
        assert expected in checks
    t = summary_for(df)["totals"]  # bad entries excluded, never counted as zero
    assert (t["harvested_kg"], t["sales_revenue_ghs"], t["expenses_ghs"]) == (215, 2090, 630)


def test_text_in_numeric_column_only():
    raw = pd.DataFrame({"date": ["2026-01-01"], "crop": ["Maize"], "harvested_kg": ["lots"],
                        "sales_revenue_ghs": ["10"], "expenses_ghs": ["5"]})
    df, q = du.clean_records(raw)
    assert df is None and "harvested_kg" in q.errors[0]


def test_filters_keep_table_cards_and_chart_consistent():
    df, _ = load("agriculture_sample_records.csv")
    view = du.filter_records(df, ["Maize"], "2026-09-01", "2026-09-30")
    s = du.summarize(view, ["Maize"], "2026-09-01", "2026-09-30")
    table = du.crop_table(view)
    assert s["totals"]["sales_revenue_ghs"] == table["sales_revenue_ghs"].sum() == 890
    assert s["highest_revenue_crop"]["crop"] == "Maize"


def test_compare_ranges():
    df, _ = load("agriculture_sample_records.csv")
    out = du.compare_ranges(df, ("2026-09-01", "2026-09-07"), ("2026-09-08", "2026-09-19"))
    assert out.loc["Records", "Range A"] + out.loc["Records", "Range B"] == 12


def test_ai_output_check_flags_invented_numbers():
    df, _ = load("agriculture_sample_records.csv")
    s = summary_for(df)
    assert ai_client.unverified_figures("Revenue was GHS 3,820 and expenses GHS 1,280.", s) == []
    assert "9,999" in ai_client.unverified_figures("Revenue was GHS 9,999.", s)


