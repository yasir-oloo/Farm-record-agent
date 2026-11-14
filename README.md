# 🌾 Farm Records Assistant

**Get Skills Network · Python with AI · Level 1 · Agriculture**
Stack: Python · Streamlit · pandas · Altair · **LangChain + Google Gemini** (`gemini-flash-lite-latest`) · managed with **uv**

## Problem and user
A farmer records harvests, sales and expenses but can't easily see what happened across crops and dates. This app turns a simple farm CSV into **checked summaries, matching charts and plain-language answers**, and exports a report that separates observed facts from possible explanations.

**Core journey:** Upload farm records → Check the numbers → Explore the story

## Features
1. **Check records** – validates required columns and types; flags missing values, text/negative numbers, bad dates and duplicates; explains how each is handled.
2. **Reliable summaries** – total harvest (kg), recorded sales revenue and recorded expenses, filterable by crop and date. All maths is done in Python (pandas).
3. **Visible patterns** – revenue vs expenses by crop, harvest by crop, revenue over time, built from the same filtered data as the table and cards, with an on-screen consistency check.
4. **Explain without guessing** – a LangChain prompt sends Gemini only the calculated summary; the answer streams back and is scanned for figures that aren't in the summary. The downloadable Markdown report separates **observed facts** from **possible explanations (unverified)**.
5. **Optional extension** – compare two date ranges side by side.

> *Recorded balance* = revenue − recorded expenses. It is **not** verified profit; the file may omit costs or other entries. The app never infers sales quantities, yield per hectare or causes.

## Setup with uv
```bash
# 1. Install uv once (https://docs.astral.sh/uv/)
#    macOS/Linux:  curl -LsSf https://astral.sh/uv/install.sh | sh
#    Windows:      powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
#    or:           pip install uv

git clone https://github.com/<your-username>/farm-records-agent.git
cd farm-records-agent
uv sync                      # creates .venv and installs exactly what uv.lock pins
```
Create your `.env` (git-ignored):
```bash
cp .env.example .env         # Windows: copy .env.example .env
```
```dotenv
GOOGLE_API_KEY=your-key-from-https://aistudio.google.com/apikey
GEMINI_MODEL=gemini-flash-lite-latest
```

## Run
```bash
uv run python main.py          # 1) checks that your key + model work (prints a streamed answer)
uv run streamlit run app.py    # 2) launches the app
uv run pytest -q               # 3) runs the tests (no API key needed)
```
Click **Load the sample farm data**, or upload `sample_data/agriculture_sample_records.csv`. The sidebar shows **Gemini Ready** with the model name when the key is found.

## How the LangChain part works (`main.py`)
- `create_llm()` builds `ChatGoogleGenerativeAI(model, temperature=0, google_api_key, max_retries=2, timeout=60)`.
- A `ChatPromptTemplate` holds the rules (no maths, no profit, no invented causes), the last 6 messages of history, and the latest question with the Python-calculated summary attached once.
- `stream_answer()` runs `PROMPT | llm` with `.stream()`; the app shows the text as it arrives.
- `friendly_error()` turns any provider error (bad key, quota, wrong model, timeout, network, blocked…) into a safe message. The key and raw errors are never shown.
- A direct chain is used instead of a tool-calling agent because there is no web to search: all facts come from the user's own records, so one grounded call is faster, cheaper and easier to check.

## Data-handling policy
| Situation | Handling |
|---|---|
| Missing required column, or a column with no valid numbers | Stop and explain – no misleading totals |
| Blank crop / unreadable date | Row removed |
| Text, blank or negative number | Entry left blank and excluded from that total (never counted as zero); row kept |
| Exact duplicate row | First kept, extras removed |
| Same crop twice on one date | Kept, flagged for review |

## Demo checks
| Check | How | Expected |
|---|---|---|
| Normal journey | Load sample data | 480 kg, GHS 3,820, GHS 1,280 |
| Data quality | Upload `sample_data/flawed_records.csv` | Issue table; bad entries excluded, not zero |
| Missing column | Upload `sample_data/flawed_missing_column.csv` | Clear error, no totals |
| Evidence boundary | Ask "Why did maize revenue change?" | States what records show + what extra information is needed |
| API failure | Put a wrong key in `.env`, restart, ask | Friendly message; rest of app still works |

Five extra test files are in `sample_data/test_datasets/` (guide: `TEST_DATASETS.md`). Results and examples: [`docs/TEST_RESULTS.md`](docs/TEST_RESULTS.md), [`docs/examples/`](docs/examples/). Demo script: [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md). Standards mapping: [`docs/SUBMISSION_CHECKLIST.md`](docs/SUBMISSION_CHECKLIST.md). Git workflow: [`docs/GIT_WORKFLOW.md`](docs/GIT_WORKFLOW.md).

## Project structure
```
app.py            Streamlit interface (dark theme), session state, reset
main.py           LangChain + Gemini: model, prompt, streaming, safe errors, output check
data_utils.py     Validation, cleaning, filtering, summaries (all calculations)
report.py         Markdown report (facts vs possible explanations)
sample_data/      Starter CSV, flawed CSVs, test_datasets/
tests/            pytest checks (no real API calls)
pyproject.toml    uv project + dependencies        uv.lock   exact versions
requirements.txt  exported from uv for platforms that need it
```

## Design notes
- **Caching:** only static sample files use `st.cache_data`; the LangChain model object uses `st.cache_resource` (it holds no farm data). Uploaded data, chat and answers stay in `st.session_state`. Repeating the same question on the same filters is answered from the session cache without an API call.
- **AI calls are explicit:** only *Ask the Assistant* and *Add Gemini's possible explanations* call Gemini; changing a filter does not.
- **Limited memory:** only the last 6 messages are re-sent. *Clear Cache* and *Reset everything* are provided.

## Deployment (Streamlit Community Cloud)
Push to GitHub → <https://share.streamlit.io> → pick the repo and `app.py` → **Advanced settings → Secrets**:
```toml
GOOGLE_API_KEY = "your-key"
GEMINI_MODEL = "gemini-flash-lite-latest"
```
If you change dependencies: `uv add <package>` then `uv export --no-dev --no-hashes --no-emit-project -o requirements.txt`.

## Known limitations
- Daily aggregates per crop only; no sales quantities, prices per kg or hectares.
- Dates are best as `YYYY-MM-DD`; ambiguous formats may be misread.
- Money columns assume GHS; text like "GHS 80" is treated as invalid.
- Outliers (e.g. a GHS 9,999,999 day) are valid numbers, so they are included and not flagged.
- AI wording can vary; figures are checked against the summary but wording is not verified.
- The free Gemini tier has rate limits.

## Contributors
| Name | Contribution |
|---|---|
| <Your name> | All development, testing and documentation |

*Submit through the channel and by the deadline your facilitator provides.*
