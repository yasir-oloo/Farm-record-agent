# Short demo script (about 4 minutes)
1. **Start screen (20 s):** hero, three steps, required columns, example question.
2. **Normal journey (60 s):** *Load the sample farm data* → 480 kg, GHS 3,820, GHS 1,280. Filter to Maize → cards, charts and table change together (150 kg / GHS 890 / GHS 350). Point at the "chart adds up" check and the "not verified profit" note.
3. **Edge case (45 s):** upload `flawed_records.csv` → issue table and policy. Then `flawed_missing_column.csv` → clear error, no totals.
4. **Ask (45 s):** ask "Why did maize revenue change?" → streamed answer states what is recorded and what is missing. Ask it again → "Retrieved from cache".
5. **API failure (30 s):** put a wrong key in `.env`, restart, ask → friendly message; rest of app works. Restore the key.
6. **Report (20 s):** download it; show *Observed facts* vs *Possible explanations (unverified)*.

## Facilitator prompts
- **Explain a function:** `clean_records` in `data_utils.py` (columns → crop → date → numbers → duplicates), or `stream_answer` in `main.py` (`PROMPT | llm` streaming, errors mapped by `friendly_error`).
- **Handle a failure:** wrong key or unplugged internet; show the safe message.
- **Small change ideas:** change `MAX_HISTORY_MESSAGES`; flag outliers (see `04_hostile_edge_cases.csv`); add a "future dates" check.
- **Limitation:** recorded balance is not profit; no sold quantities, prices or yields.
