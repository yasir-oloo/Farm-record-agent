"""Loading, validating, cleaning, filtering and summarising farm records.

Every number shown in the app is calculated here with pandas. The AI never
calculates totals; it only explains the summaries produced by this module.
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = ["date", "crop", "harvested_kg", "sales_revenue_ghs", "expenses_ghs"]
NUMERIC_COLUMNS = ["harvested_kg", "sales_revenue_ghs", "expenses_ghs"]
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MISSING_TOKENS = {"", "na", "n/a", "nan", "null", "none", "-"}
MAX_ROWS_LISTED = 5


class DataError(Exception):
    """A problem with the uploaded file that is safe to show to the user."""


@dataclass
class QualityReport:
    """Result of checking an upload: blocking errors plus a table of issues."""

    rows_in: int = 0
    rows_kept: int = 0
    errors: list[str] = field(default_factory=list)
    issues: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def add_issue(self, check: str, count: int, rows: str, handling: str) -> None:
        self.issues.append(
            {"Check": check, "Found": int(count), "CSV rows": rows, "How it was handled": handling}
        )


# --------------------------------------------------------------------------- #
# Loading and cleaning
# --------------------------------------------------------------------------- #
def read_csv_bytes(data: bytes) -> pd.DataFrame:
    """Read raw CSV bytes as text so we can detect bad values ourselves."""
    if not data:
        raise DataError("The file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise DataError("The file is larger than 5 MB. Please upload a smaller CSV.")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("latin-1")
    try:
        raw = pd.read_csv(io.StringIO(text), dtype=str, skipinitialspace=True, keep_default_na=False)
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
        raise DataError(
            "This doesn't look like a valid CSV file. Check that it is comma-separated "
            f"and has a header row ({type(exc).__name__})."
        ) from exc
    if raw.empty:
        raise DataError("The file has a header row but no data rows.")
    return raw


def _rows(frame: pd.DataFrame, mask: pd.Series) -> str:
    rows = frame.loc[mask, "_row"].tolist()
    text = ", ".join(str(r) for r in rows[:MAX_ROWS_LISTED])
    return text + (" ..." if len(rows) > MAX_ROWS_LISTED else "")


def _parse_dates(series: pd.Series) -> pd.Series:
    values = series.astype(object).where(series.notna(), None)
    try:
        parsed = pd.to_datetime(values, errors="coerce", format="mixed")
    except (TypeError, ValueError):  # older pandas without format="mixed"
        parsed = pd.to_datetime(values, errors="coerce")
    return parsed.dt.normalize()


def clean_records(raw: pd.DataFrame) -> tuple[pd.DataFrame | None, QualityReport]:
    """Validate and clean raw records. Returns (clean_df or None, report).

    Handling policy:
      * Missing required column / column with no valid numbers -> stop, explain.
      * Blank crop or unreadable date -> row removed (it cannot be placed).
      * Text, blank or negative number -> entry left blank, row kept, and that
        entry is excluded from its total (it is NOT treated as zero).
      * Exact duplicate rows -> first kept, extras removed.
      * Same crop twice on one day -> kept but flagged for review.
    """
    report = QualityReport(rows_in=len(raw))
    df = raw.copy()
    df.columns = [re.sub(r"\s+", "_", str(c).strip().lower()) for c in df.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        report.errors.append(
            f"Required column(s) missing: {', '.join(missing)}. Totals cannot be shown without "
            f"them. Expected columns: {', '.join(REQUIRED_COLUMNS)}."
        )
        return None, report
    extra = [c for c in df.columns if c not in REQUIRED_COLUMNS]
    if extra:
        report.notes.append(f"Extra column(s) ignored: {', '.join(extra)}.")

    df = df[REQUIRED_COLUMNS].copy()
    df["_row"] = df.index + 2  # line number in the CSV file (header is line 1)
    for col in REQUIRED_COLUMNS:
        s = df[col].astype("string").str.strip()
        df[col] = s.mask(s.str.lower().isin(MISSING_TOKENS))

    # Crop: blank rows cannot be grouped, so remove them; tidy spelling/case.
    blank_crop = df["crop"].isna()
    if blank_crop.any():
        report.add_issue("Blank crop name", blank_crop.sum(), _rows(df, blank_crop), "Row removed.")
        df = df[~blank_crop].copy()
    tidy = df["crop"].str.replace(r"\s+", " ", regex=True).str.title()
    changed = int((tidy != df["crop"]).sum())
    if changed:
        report.notes.append(f"{changed} crop name(s) tidied (spaces/capitalisation), e.g. 'tomato ' -> 'Tomato'.")
    df["crop"] = tidy.astype(str)

    # Dates
    df["date"] = _parse_dates(df["date"])
    bad_date = df["date"].isna()
    if bad_date.any():
        report.add_issue("Missing or unreadable date", bad_date.sum(), _rows(df, bad_date),
                         "Row removed (use YYYY-MM-DD).")
        df = df[~bad_date].copy()

    # Numbers
    for col in NUMERIC_COLUMNS:
        original = df[col]
        blank = original.isna()
        numeric = pd.to_numeric(original.str.replace(",", "", regex=False), errors="coerce")
        numeric = numeric.astype(float)
        not_number = (numeric.isna() & ~blank) | (~np.isfinite(numeric) & ~numeric.isna())
        negative = numeric < 0
        left_out = f"Entry left blank; row kept; excluded from the {col} total (not counted as zero)."
        if blank.any():
            report.add_issue(f"Missing {col}", blank.sum(), _rows(df, blank), left_out)
        if not_number.any():
            report.add_issue(f"Text/non-numeric value in {col}", not_number.sum(),
                             _rows(df, not_number), left_out)
        if negative.any():
            report.add_issue(f"Negative value in {col}", negative.sum(), _rows(df, negative),
                             left_out.replace("Entry left blank", "Entry treated as invalid and left blank"))
        df[col] = numeric.mask(not_number | negative)
        if df[col].notna().sum() == 0:
            report.errors.append(
                f"Column '{col}' has no valid numbers, so its total cannot be calculated. "
                "Fix the values (plain numbers, no text) and upload again."
            )
    if report.errors:
        return None, report

    # Duplicates
    dup = df.duplicated(subset=REQUIRED_COLUMNS, keep="first")
    if dup.any():
        report.add_issue("Exact duplicate row", dup.sum(), _rows(df, dup), "First copy kept; extras removed.")
        df = df[~dup].copy()
    repeat = df.duplicated(subset=["date", "crop"], keep=False)
    if repeat.any():
        report.add_issue("Same crop twice on the same date", repeat.sum(), _rows(df, repeat),
                         "Kept (not exact duplicates) - please check they are not double entries.")

    if df.empty:
        report.errors.append("No usable rows remain after checking. See the issues above.")
        return None, report

    df = df.drop(columns="_row").sort_values(["date", "crop"]).reset_index(drop=True)
    report.rows_kept = len(df)
    return df, report


# --------------------------------------------------------------------------- #
# Filtering and summaries
# --------------------------------------------------------------------------- #
def filter_records(df: pd.DataFrame, crops: list[str], start, end) -> pd.DataFrame:
    mask = (df["crop"].isin(crops) & (df["date"] >= pd.Timestamp(start)) & (df["date"] <= pd.Timestamp(end)))
    return df.loc[mask].reset_index(drop=True)


def crop_table(df: pd.DataFrame) -> pd.DataFrame:
    """Per-crop totals - the single source for the table, the chart and the AI summary."""
    cols = ["crop", "records", "harvested_kg", "sales_revenue_ghs", "expenses_ghs",
            "recorded_balance_ghs", "revenue_share_pct"]
    if df.empty:
        return pd.DataFrame(columns=cols)
    t = df.groupby("crop", as_index=False).agg(
        records=("crop", "size"), harvested_kg=("harvested_kg", "sum"),
        sales_revenue_ghs=("sales_revenue_ghs", "sum"), expenses_ghs=("expenses_ghs", "sum"))
    t["recorded_balance_ghs"] = t["sales_revenue_ghs"] - t["expenses_ghs"]
    total = t["sales_revenue_ghs"].sum()
    t["revenue_share_pct"] = (t["sales_revenue_ghs"] / total * 100) if total > 0 else 0.0
    t = t.sort_values(["sales_revenue_ghs", "crop"], ascending=[False, True]).reset_index(drop=True)
    return t.round(2)


def _top(t: pd.DataFrame, col: str) -> dict | None:
    if t.empty:
        return None
    row = t.sort_values([col, "crop"], ascending=[False, True]).iloc[0]
    return {"crop": row["crop"], col: float(row[col])}


def summarize(df: pd.DataFrame, crops: list[str], start, end) -> dict:
    """Everything the AI is allowed to see about the current filtered view."""
    t = crop_table(df)
    totals = {
        "harvested_kg": round(float(df["harvested_kg"].sum()), 2),
        "sales_revenue_ghs": round(float(df["sales_revenue_ghs"].sum()), 2),
        "expenses_ghs": round(float(df["expenses_ghs"].sum()), 2),
    }
    totals["recorded_balance_ghs"] = round(totals["sales_revenue_ghs"] - totals["expenses_ghs"], 2)

    changes = []
    for crop, g in df.dropna(subset=["sales_revenue_ghs"]).groupby("crop"):
        g = g.sort_values("date")
        if len(g) >= 2:
            first, last = g.iloc[0], g.iloc[-1]
            changes.append({
                "crop": crop, "first_date": str(first["date"].date()),
                "first_revenue_ghs": float(first["sales_revenue_ghs"]),
                "last_date": str(last["date"].date()),
                "last_revenue_ghs": float(last["sales_revenue_ghs"]),
                "change_ghs": round(float(last["sales_revenue_ghs"] - first["sales_revenue_ghs"]), 2)})

    daily = {}
    for crop, g in df.groupby("crop"):
        daily[crop] = [
            {"date": str(r.date.date()), "harvested_kg": _num(r.harvested_kg),
             "sales_revenue_ghs": _num(r.sales_revenue_ghs), "expenses_ghs": _num(r.expenses_ghs)}
            for r in g.sort_values("date").tail(40).itertuples()]

    return {
        "filters": {
            "crops": sorted(crops),
            "date_from": str(pd.Timestamp(start).date()),
            "date_to": str(pd.Timestamp(end).date()),
        },
        "records_in_view": int(len(df)),
        "totals": totals,
        "entries_left_out_of_totals_because_blank_or_invalid": {
            c: int(df[c].isna().sum()) for c in NUMERIC_COLUMNS},
        "by_crop": t.to_dict(orient="records"),
        "highest_revenue_crop": _top(t, "sales_revenue_ghs"),
        "highest_expense_crop": _top(t, "expenses_ghs"),
        "highest_harvest_crop": _top(t, "harvested_kg"),
        "revenue_change_first_to_last_record_by_crop": changes,
        "recorded_daily_values_by_crop": daily,
    }


def _num(x) -> float | None:
    return None if pd.isna(x) else float(x)


def compare_ranges(df: pd.DataFrame, a: tuple, b: tuple) -> pd.DataFrame:
    """Optional extension: totals for two date ranges side by side."""
    def block(rng):
        sub = df[(df["date"] >= pd.Timestamp(rng[0])) & (df["date"] <= pd.Timestamp(rng[1]))]
        return {"Records": len(sub), "Harvest (kg)": sub["harvested_kg"].sum(),
                "Sales revenue (GHS)": sub["sales_revenue_ghs"].sum(),
                "Recorded expenses (GHS)": sub["expenses_ghs"].sum()}
    ra, rb = block(a), block(b)
    out = pd.DataFrame({"Range A": ra, "Range B": rb})
    out["Change (B - A)"] = out["Range B"] - out["Range A"]
    out["Change %"] = [(c / x * 100) if x else None for x, c in zip(out["Range A"], out["Change (B - A)"])]
    return out.round(2)


# --------------------------------------------------------------------------- #
# Formatting
# --------------------------------------------------------------------------- #
def fmt_ghs(x: float) -> str:
    return f"GHS {x:,.2f}".replace(".00", "")


def fmt_kg(x: float) -> str:
    return f"{x:,.2f}".replace(".00", "") + " kg"
