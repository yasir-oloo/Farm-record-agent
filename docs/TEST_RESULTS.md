# Test results

## Automated (`uv run pytest -q`: 23 passed, no real API calls)
| Type | Check | Result |
|---|---|---|
| Normal | Starter file gives 480 kg, GHS 3,820, GHS 1,280 (recorded balance GHS 2,540) | Pass |
| Normal | Maize filter: table total = card total = GHS 890; top crop correct | Pass |
| Normal | Two-date-range comparison covers all 12 records | Pass |
| Edge | Missing `expenses_ghs` column → error, no totals | Pass |
| Edge | Flawed file: blank crop, bad date, text, negative, blank, duplicate all flagged; totals 215 kg / GHS 2,090 / GHS 630 (bad entries excluded, not zero) | Pass |
| Edge | Column with only text → blocked with explanation | Pass |
| AI output | Figures not in the summary are flagged; matching figures are not | Pass |
| LangChain | Model built with `GOOGLE_API_KEY` + `gemini-flash-lite-latest`; default model is flash-lite | Pass |
| LangChain | Streaming works for string and Gemini content-block replies | Pass |
| LangChain | History trimmed to last 6 messages; summary attached once; rules in system prompt | Pass |
| API failure | Missing key → friendly message | Pass |
| API failure | Invalid key / no access / quota / model not found / timeout / network / server error / unknown → safe messages; key and raw text never shown (8 cases) | Pass |
| API failure | Empty reply → friendly message | Pass |

## Automated app run (Streamlit AppTest with a fake model)
Sample load → cards 480 kg / GHS 3,820 / GHS 1,280 · no key → configuration message · fake model → streamed answer shown · same question again → "Retrieved from cache", no second call · Maize filter → new summary (150 kg / GHS 890 / GHS 350) and a new call.

## Live checks with your own key (record before submitting)
Run `uv run python main.py` first.
| Check | Date | Result / notes |
|---|---|---|
| `uv run python main.py` streams an answer | | |
| Example question on the starter data | | |
| "Why did maize revenue change?" (states limits, no invented causes) | | |
| Report with AI explanations downloads and opens | | |
| Wrong key in `.env` → friendly message, app still usable | | |
