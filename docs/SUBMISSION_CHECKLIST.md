# Checklist mapping

## Project checklist
| Item | Where |
|---|---|
| Required columns and date/numeric types validated | `data_utils.clean_records` |
| Missing values and duplicates flagged with a policy | Issue table in app; policy table in README |
| Negative/unsuitable values handled explicitly | Left blank, excluded from totals |
| Totals calculated in Python | `data_utils.summarize` |
| Filters update table, cards, chart consistently | `app.summary_tab`; test `test_filters_keep_...` |
| Answers use the on-screen filtered summary | `main.stream_answer(llm, question, summary, ...)` |
| Balance not labelled profit | Cards, report, system prompt |
| Report downloads; flawed file gives feedback | `report.py`; `sample_data/flawed_*.csv` |

## Shared Level 1 standards
| Standard | Where |
|---|---|
| Useful Streamlit experience | Start screen, sidebar, 3 tabs |
| Readable Python | `app.py`, `main.py`, `data_utils.py`, `report.py`; docstrings |
| Real AI integration, keys outside Git | LangChain + Gemini in `main.py`; `.env` in `.gitignore` |
| Graceful failures | `friendly_error`; upload errors; tests |
| Caching and explicit AI calls | `st.cache_data` samples, `st.cache_resource` model, session answer cache; buttons trigger calls |
| Memory and reset | Session state; trimmed history; Clear Cache and Reset buttons |
| Checked results | Python totals; `unverified_figures` |
| Reproducible repository | `pyproject.toml`, `uv.lock`, `requirements.txt`, `.gitignore`, samples, README |
| Visible Git workflow | `docs/GIT_WORKFLOW.md` (you make the commits) |
| Deployment and demonstration | README deployment steps; `docs/DEMO_SCRIPT.md` (you deploy and record) |

## Submission pack
- [ ] Deployed app link: ____
- [ ] GitHub repository link: ____
- [ ] Output examples: `docs/examples/` (+ paste live AI answers in file 06)
- [ ] Demo + normal / edge-case / API-failure results: `docs/TEST_RESULTS.md`
- [ ] Contributor names: README
