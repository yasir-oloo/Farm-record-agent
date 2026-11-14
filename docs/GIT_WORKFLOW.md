# Suggested Git workflow
```bash
git init -b main
git add .gitignore .python-version pyproject.toml uv.lock requirements.txt .env.example README.md
git commit -m "chore: uv project scaffold, lockfile and README"
git checkout -b feature/data-validation
git add data_utils.py sample_data tests/test_core.py && git commit -m "feat: CSV validation, cleaning and summaries with tests"
git checkout -b feature/gemini-langchain main
git add main.py report.py tests/test_ai.py && git commit -m "feat: LangChain Gemini assistant, safe errors and report"
git add app.py .streamlit/config.toml .streamlit/secrets.toml.example docs scripts && git commit -m "feat: dark Streamlit interface, docs and examples"
```
Push each branch and open a pull request into `main` (team: a teammate reviews; solo: review your own diff and note what you checked). Before every push run `git status` and confirm `.env` is **not** listed. If a key is ever committed, delete it at aistudio.google.com/apikey and create a new one.
