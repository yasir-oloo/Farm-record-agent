"""Farm Records Assistant - Streamlit app (dark research-platform style).

Journey: Upload farm records -> Check the numbers -> Explore the story.
Python does every calculation; Gemini (through LangChain) only explains the summaries.
"""
from __future__ import annotations

import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

import data_utils as du
import main as ai
import report as rp

BASE = Path(__file__).parent
SAMPLE = BASE / "sample_data" / "agriculture_sample_records.csv"
FLAWED = BASE / "sample_data" / "flawed_records.csv"
MAX_CHAT_MESSAGES = 20
EXAMPLE_QUESTIONS = [
    "Which crop generated the most recorded sales revenue? What were our recorded expenses, and what should I look at more closely?",
    "Why did maize revenue change?",
    "Which crop has the highest recorded balance?",
]
CYAN, ORANGE, GREEN = "#48CAE4", "#F4A261", "#52B788"

# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================
st.set_page_config(page_title="Farm Records Assistant", page_icon="🌾", layout="wide",
                   initial_sidebar_state="expanded")

# ============================================================
# 2. PROFESSIONAL CSS DESIGN
# ============================================================
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #07111F, #0A1628, #0D1B2E); color: #EAF2FF; }
.block-container { max-width: 1200px; padding-top: 2rem; padding-bottom: 2rem; }
[data-testid="stSidebar"] { background: #081321; border-right: 1px solid #1B2D44; }
[data-testid="stSidebar"] * { color: #DCE8F7; }
h1, h2, h3 { color: #FFFFFF !important; font-weight: 800 !important; }
p { color: #A9BCD3; line-height: 1.7; }
.brand { color: #48CAE4; font-size: 12px; font-weight: 800; letter-spacing: 3px; }
.hero-title { color: #FFFFFF; font-size: 34px; font-weight: 800; }
.hero-description { color: #A9BCD3; font-size: 15px; }
div[data-testid="stTextInput"] input {
    background: #0D1B2E !important; color: #FFFFFF !important; border: 1px solid #263D59 !important;
    border-radius: 12px !important; min-height: 50px; }
div[data-testid="stTextInput"] input:focus { border-color: #48CAE4 !important; box-shadow: 0 0 0 2px rgba(72,202,228,0.15); }
div.stButton > button, div.stDownloadButton > button {
    background: linear-gradient(135deg, #00B4D8, #0077B6); color: white; border: none; border-radius: 12px;
    min-height: 48px; font-weight: 700; transition: 0.3s; }
div.stButton > button:hover, div.stDownloadButton > button:hover { background: #48CAE4; color: #FFFFFF; transform: translateY(-2px); }
[data-testid="stVerticalBlockBorderWrapper"] { background: #10233A; border: 1px solid #263D59; border-radius: 16px; }
[data-testid="stMetric"] { background: #10233A; border: 1px solid #263D59; border-radius: 16px; padding: 16px 18px; }
[data-testid="stMetricValue"] { color: #FFFFFF; font-weight: 800; }
[data-testid="stMetricLabel"] p { color: #A9BCD3; font-weight: 600; }
.stTabs [data-baseweb="tab"] { color: #A9BCD3; font-weight: 700; }
.stTabs [aria-selected="true"] { color: #48CAE4; }
hr { border-color: #263D59 !important; }
[data-testid="stAlert"] { border-radius: 12px; }
.custom-footer { text-align: center; color: #8197B2; font-size: 12px; }
@media (max-width: 768px) { .hero-title { font-size: 24px; } .block-container { padding: 1rem; } }
</style>
""", unsafe_allow_html=True)


# ============================================================
# 3. STATE, LOADING AND CACHING
# ============================================================
@st.cache_data(show_spinner=False)
def read_static_file(path: str) -> bytes:
    """Sample files are public and static, so they are safe to cache."""
    return Path(path).read_bytes()


@st.cache_resource(show_spinner=False)
def get_llm():
    """The LangChain Gemini model (holds no farm data). Raises AIError if the key is missing."""
    return ai.create_llm()


STATE_DEFAULTS = {"clean_df": None, "quality": None, "source_name": None, "signature": None,
                  "load_error": None, "chat": [], "report_ai": None, "question": "",
                  "answer_cache": {}, "auto_run": False, "uploader_key": 0}


def init_state() -> None:
    for key, value in STATE_DEFAULTS.items():
        st.session_state.setdefault(key, value.copy() if isinstance(value, (list, dict)) else value)


def reset_all() -> None:
    next_key = st.session_state.get("uploader_key", 0) + 1
    st.session_state.clear()
    st.session_state["uploader_key"] = next_key


def load_records(data: bytes, name: str, signature) -> None:
    """Validate + clean a CSV and keep the private result in session state only."""
    for k in ("flt_crops", "flt_dates"):
        st.session_state.pop(k, None)
    st.session_state.update(source_name=name, signature=signature, chat=[], report_ai=None, answer_cache={},
                            clean_df=None, quality=None, load_error=None)
    try:
        clean, quality = du.clean_records(du.read_csv_bytes(data))
    except du.DataError as exc:
        st.session_state.load_error = str(exc)
        return
    st.session_state.clean_df, st.session_state.quality = clean, quality


def pick_question(text: str) -> None:
    st.session_state.question = text
    st.session_state.auto_run = True


# ============================================================
# 4. SIDEBAR
# ============================================================
def sidebar():
    with st.sidebar:
        st.markdown("# 🌾")
        st.markdown("<p class='brand'>AI FARM RECORDS PLATFORM</p>", unsafe_allow_html=True)
        st.markdown("## Farm Records Assistant")
        st.caption("Checked numbers. Clear charts. Plain-language answers.")
        st.divider()

        st.markdown("### 📂 1 · Your records")
        uploaded = st.file_uploader("Upload a farm CSV", type=["csv"],
                                    key=f"uploader_{st.session_state.uploader_key}",
                                    help="Columns: " + ", ".join(du.REQUIRED_COLUMNS))
        if uploaded is not None:
            sig = ("upload", uploaded.file_id)
            if st.session_state.signature != sig:
                load_records(uploaded.getvalue(), uploaded.name, sig)
        if st.button("Load the sample farm data", width="stretch"):
            load_records(read_static_file(str(SAMPLE)), SAMPLE.name, ("sample",))
            st.session_state.uploader_key += 1  # clears the uploader
            st.rerun()
        st.download_button("⬇ Sample CSV", read_static_file(str(SAMPLE)), SAMPLE.name, "text/csv", width="stretch")
        st.download_button("⬇ Flawed CSV (to test the checks)", read_static_file(str(FLAWED)), FLAWED.name,
                           "text/csv", width="stretch")

        selection = None
        df = st.session_state.clean_df
        if df is not None:
            st.divider()
            st.markdown("### 🎛️ 2 · Filters")
            crops_all = sorted(df["crop"].unique())
            lo, hi = df["date"].min().date(), df["date"].max().date()
            crops = st.multiselect("Crops", crops_all, default=crops_all, key="flt_crops")
            dates = st.date_input("Date range", value=(lo, hi), min_value=lo, max_value=hi, key="flt_dates")
            if isinstance(dates, tuple) and len(dates) == 2:
                selection = (crops, dates[0], dates[1])
            else:
                st.info("Pick an end date to apply the range.")

        st.divider()
        st.markdown("### 🟢 System Status")
        if ai.is_configured():
            st.success("Gemini Ready")
            st.caption(f"Model: {ai.model_name()}")
        else:
            st.warning("Gemini key not set. Everything works except AI answers.")
        st.caption("Powered by LangChain, Gemini & Streamlit")
        st.button("🔄 Reset everything", on_click=reset_all, width="stretch")
        st.caption("Version 1.0.0")
    return selection


# ============================================================
# 5. HEADER AND START SCREEN
# ============================================================
def header() -> None:
    st.markdown("<p class='brand'></p>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("<h1 class='hero-title'>Farm Records Assistant 🌾</h1>", unsafe_allow_html=True)
        st.markdown("<p class='hero-description'>Turn a simple farm spreadsheet into checked summaries, matching "
                    "charts and plain-language answers about what was recorded.</p>", unsafe_allow_html=True)
        q = st.session_state.quality
        if q is not None and q.ok:
            st.success(f"RECORDS LOADED · {q.rows_kept} rows from {st.session_state.source_name}")
        elif q is not None:
            st.error("FILE NEEDS ATTENTION · see the data check below")
        else:
            st.info("WAITING FOR RECORDS · upload a CSV or load the sample from the sidebar")
    st.divider()


def policy_expander() -> None:
    with st.expander("How the app handles problems in your data"):
        st.markdown(
            "- **Missing column / a column with no valid numbers:** we stop and explain, instead of showing misleading totals.\n"
            "- **Blank crop or unreadable date:** the row is removed (it can't be placed).\n"
            "- **Text, blank or negative numbers:** the entry is left blank and excluded from that total (never counted as zero); the row is kept.\n"
            "- **Exact duplicate rows:** the first is kept, extras removed.\n"
            "- **Same crop twice on a day:** kept, but flagged for you to check.\n"
            "- **Recorded balance** = revenue − recorded expenses. It is **not** verified profit.")


def start_screen() -> None:
    c1, c2, c3 = st.columns(3)
    with c1.container(border=True):
        st.markdown("### ① Upload\nUpload a CSV of harvests, sales and expenses.")
    with c2.container(border=True):
        st.markdown("### ② Check\nWe validate it and flag missing values, duplicates and odd numbers.")
    with c3.container(border=True):
        st.markdown("### ③ Explore\nFilter, see charts, ask questions and download a report.")
    st.markdown("**Required columns:** `" + "`, `".join(du.REQUIRED_COLUMNS) + "` (one row per crop per day; harvest in kg; money in GHS).")
    st.code("date,crop,harvested_kg,sales_revenue_ghs,expenses_ghs\n2026-09-01,Maize,60,330,120", language="csv")
    st.markdown("**Example question:** " + EXAMPLE_QUESTIONS[0])
    policy_expander()


# ============================================================
# 6. TAB 1 - CHECK RECORDS
# ============================================================
def quality_tab() -> None:
    q, df = st.session_state.quality, st.session_state.clean_df
    st.markdown("<p class='brand'>DATA QUALITY CHECK</p>", unsafe_allow_html=True)
    for err in q.errors:
        st.error(err)
    if q.ok:
        if q.issues:
            st.warning(f"{q.rows_in} rows read, {q.rows_kept} kept. Issues were found and handled as shown below.")
            st.dataframe(pd.DataFrame(q.issues), hide_index=True, width="stretch")
        else:
            st.success(f"{q.rows_in} rows read, {q.rows_kept} kept. No data-quality issues found.")
        for note in q.notes:
            st.caption("ℹ️ " + note)
        st.markdown("**Cleaned records**")
        st.dataframe(df.assign(date=df["date"].dt.date), hide_index=True, width="stretch")
    policy_expander()


# ============================================================
# 7. TAB 2 - SUMMARY AND CHARTS
# ============================================================
def style_chart(chart: alt.Chart) -> alt.Chart:
    return (chart.configure(background="transparent")
            .configure_axis(labelColor="#A9BCD3", titleColor="#DCE8F7", gridColor="#1B2D44",
                            domainColor="#263D59", tickColor="#263D59")
            .configure_title(color="#FFFFFF", fontSize=15, anchor="start")
            .configure_legend(labelColor="#DCE8F7", titleColor="#DCE8F7", orient="bottom")
            .configure_view(stroke=None))


def kpi_cards(summary: dict) -> None:
    t = summary["totals"]
    a, b, c, d = st.columns(4)
    a.metric("Total harvest", du.fmt_kg(t["harvested_kg"]))
    b.metric("Recorded sales revenue", du.fmt_ghs(t["sales_revenue_ghs"]))
    c.metric("Recorded expenses", du.fmt_ghs(t["expenses_ghs"]))
    d.metric("Recorded balance", du.fmt_ghs(t["recorded_balance_ghs"]),
             help="Revenue minus recorded expenses. NOT verified profit - the file may omit costs.")
    left = {k: v for k, v in summary["entries_left_out_of_totals_because_blank_or_invalid"].items() if v}
    if left:
        st.caption("⚠️ Blank/invalid entries excluded from totals: " + ", ".join(f"{k}: {v}" for k, v in left.items()))
    st.caption("Recorded balance = revenue − recorded expenses. It is not verified profit.")


def summary_tab(view: pd.DataFrame, summary: dict) -> None:
    st.markdown("<p class='brand'>RECORDED SUMMARY</p>", unsafe_allow_html=True)
    kpi_cards(summary)
    table = du.crop_table(view)
    order = table["crop"].tolist()
    money = table.melt(id_vars="crop", value_vars=["sales_revenue_ghs", "expenses_ghs"],
                       var_name="measure", value_name="ghs")
    money["measure"] = money["measure"].map({"sales_revenue_ghs": "Recorded sales revenue",
                                             "expenses_ghs": "Recorded expenses"})
    st.altair_chart(style_chart(
        alt.Chart(money).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X("crop:N", title="Crop", sort=order), xOffset="measure:N",
            y=alt.Y("ghs:Q", title="Amount (GHS)"),
            color=alt.Color("measure:N", title="", scale=alt.Scale(
                domain=["Recorded sales revenue", "Recorded expenses"], range=[CYAN, ORANGE])),
            tooltip=["crop", "measure", alt.Tooltip("ghs:Q", title="GHS", format=",.2f")])
        .properties(title="Recorded sales revenue vs recorded expenses by crop", height=340)), width="stretch")
    totals = money.groupby("measure")["ghs"].sum()
    t = summary["totals"]
    ok = (abs(totals.get("Recorded sales revenue", 0) - t["sales_revenue_ghs"]) < 0.01
          and abs(totals.get("Recorded expenses", 0) - t["expenses_ghs"]) < 0.01)
    st.caption(("✅ " if ok else "❌ ") + "Chart values add up to the summary cards above.")

    c1, c2 = st.columns(2)
    c1.altair_chart(style_chart(
        alt.Chart(table).mark_bar(color=GREEN, cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X("crop:N", title="Crop", sort=order), y=alt.Y("harvested_kg:Q", title="Harvest (kg)"),
            tooltip=["crop", alt.Tooltip("harvested_kg:Q", title="kg", format=",.1f")])
        .properties(title="Harvest by crop (kg)", height=280)), width="stretch")
    daily = view.groupby(["date", "crop"], as_index=False)["sales_revenue_ghs"].sum()
    c2.altair_chart(style_chart(
        alt.Chart(daily).mark_line(point=True).encode(
            x=alt.X("date:T", title="Date"), y=alt.Y("sales_revenue_ghs:Q", title="Revenue (GHS)"),
            color=alt.Color("crop:N", title="Crop"),
            tooltip=["crop", "date:T", alt.Tooltip("sales_revenue_ghs:Q", title="GHS", format=",.2f")])
        .properties(title="Recorded sales revenue over time", height=280)), width="stretch")

    st.markdown("**By crop (same figures as the cards and charts)**")
    st.dataframe(table.rename(columns={
        "crop": "Crop", "records": "Records", "harvested_kg": "Harvest (kg)", "sales_revenue_ghs": "Revenue (GHS)",
        "expenses_ghs": "Expenses (GHS)", "recorded_balance_ghs": "Recorded balance (GHS)",
        "revenue_share_pct": "Share of revenue (%)"}), hide_index=True, width="stretch")
    with st.expander("Filtered records"):
        st.dataframe(view.assign(date=view["date"].dt.date), hide_index=True, width="stretch")
    with st.expander("Optional: compare two date ranges"):
        df = st.session_state.clean_df
        lo, hi = df["date"].min().date(), df["date"].max().date()
        a = st.date_input("Range A", value=(lo, lo), min_value=lo, max_value=hi, key="cmp_a")
        b = st.date_input("Range B", value=(hi, hi), min_value=lo, max_value=hi, key="cmp_b")
        if all(isinstance(x, tuple) and len(x) == 2 for x in (a, b)):
            crops = st.session_state.get("flt_crops", [])
            st.caption(f"Range A: {a[0]} to {a[1]} · Range B: {b[0]} to {b[1]} · crops: {', '.join(crops)}")
            st.dataframe(du.compare_ranges(df[df["crop"].isin(crops)], a, b), width="stretch")


# ============================================================
# 8. TAB 3 - ASK AND REPORT
# ============================================================
def ask_tab(summary: dict) -> None:
    st.markdown("<p class='brand'>ASK YOUR RECORDS</p>", unsafe_allow_html=True)
    st.write("Ask a question. Answers use only the calculated summary of the filtered view shown on screen.")
    user_query = st.text_input("Enter your question:", key="question", max_chars=ai.MAX_QUESTION_CHARS,
                               placeholder="Which crop earned the most recorded revenue?")
    col1, col2 = st.columns([2, 1])
    run_search = col1.button("🚀 Ask the Assistant", width="stretch")
    clear_cache = col2.button("🗑️ Clear Cache", width="stretch")
    st.caption("Try an example:")
    for q in EXAMPLE_QUESTIONS:
        st.button(q, key=f"ex_{q[:20]}", on_click=pick_question, args=(q,))

    if st.session_state.pop("auto_run", False):
        run_search = True
    if clear_cache:
        st.session_state.answer_cache.clear()
        st.session_state.chat = []
        st.success("Answer cache and conversation cleared.")

    if run_search:
        question = user_query.strip()
        st.divider()
        st.markdown("### 🔎 Assistant Response")
        if not question:
            st.warning("Please enter a question first.")
        elif summary["records_in_view"] == 0:
            st.warning("No records match the current filters, so there is nothing to answer from.")
        else:
            cache_key = json.dumps(summary["filters"], sort_keys=True) + "||" + question.lower()
            cache = st.session_state.answer_cache
            answer = cache.get(cache_key)
            if answer:
                st.info("⚡ Retrieved from cache (no AI call made)")
                with st.container(border=True):
                    st.markdown(answer)
            else:
                placeholder, answer = st.empty(), ""
                try:
                    llm = get_llm()
                    with st.spinner("Assistant is reading your calculated summaries..."):
                        for piece in ai.stream_answer(llm, question, summary, st.session_state.chat):
                            answer += piece
                            placeholder.markdown(answer + " ▌")
                    placeholder.markdown(answer)
                    cache[cache_key] = answer
                except ai.AIError as exc:
                    placeholder.empty()
                    st.error(str(exc))
                    answer = ""
            if answer:
                odd = ai.unverified_figures(answer, summary)
                if odd:
                    st.caption("⚠️ These figures aren't in the calculated summary - rely on the on-screen numbers: "
                               + ", ".join(odd))
                chat = st.session_state.chat + [{"role": "user", "content": question},
                                                {"role": "assistant", "content": answer}]
                st.session_state.chat = chat[-MAX_CHAT_MESSAGES:]

    if st.session_state.chat:
        with st.expander(f"Conversation history ({len(st.session_state.chat) // 2} question(s))"):
            for msg in st.session_state.chat:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

    st.divider()
    st.markdown("<p class='brand'>DOWNLOADABLE REPORT</p>", unsafe_allow_html=True)
    sig = json.dumps(summary["filters"], sort_keys=True)
    stored = st.session_state.report_ai
    ai_text = stored["text"] if stored and stored["sig"] == sig else None
    if st.button("Add Gemini's possible explanations to the report"):
        if summary["records_in_view"] == 0:
            st.warning("No records match the current filters.")
        else:
            try:
                with st.spinner("Assistant is drafting possible explanations..."):
                    text = ai.explain_for_report(get_llm(), summary)
                st.session_state.report_ai = {"sig": sig, "text": text}
                st.rerun()
            except ai.AIError as exc:
                st.error(str(exc))
    st.caption("✅ AI explanations included in the report." if ai_text else
               "The report separates observed facts (calculated by Python) from possible explanations (unverified).")
    md = rp.build_report(summary, st.session_state.quality, st.session_state.source_name, ai_text)
    st.download_button("⬇ Download report (Markdown)", md, "farm_report.md", "text/markdown")
    with st.expander("Preview report"):
        st.markdown(md)


# ============================================================
# 9. MAIN
# ============================================================
def run_app() -> None:
    init_state()
    selection = sidebar()
    header()
    if st.session_state.load_error:
        st.error(st.session_state.load_error)
        policy_expander()
    elif st.session_state.quality is None:
        start_screen()
    elif st.session_state.clean_df is None:  # blocking validation error
        quality_tab()
    else:
        tab1, tab2, tab3 = st.tabs(["① Check records", "② Summary & charts", "③ Ask & report"])
        with tab1:
            quality_tab()
        if selection is None:
            with tab2:
                st.info("Complete the date range in the sidebar.")
        elif not selection[0]:
            with tab2:
                st.warning("Select at least one crop in the sidebar.")
        else:
            crops, start, end = selection
            view = du.filter_records(st.session_state.clean_df, crops, start, end)
            summary = du.summarize(view, crops, start, end)
            with tab2:
                if view.empty:
                    st.warning("No records match these filters.")
                else:
                    summary_tab(view, summary)
            with tab3:
                ask_tab(summary)

    st.divider()
    st.markdown("""<div class="custom-footer">Built by Yasir with ❤️ using Streamlit, LangChain and Google Gemini<br><br>
    <strong>Farm Records Assistant</strong> | AI-Powered Farm Records Platform</div>""", unsafe_allow_html=True)


run_app()
