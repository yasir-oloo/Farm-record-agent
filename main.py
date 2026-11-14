"""LangChain + Google Gemini logic for the Farm Records Assistant.

Python (data_utils.py) calculates every figure. This module only sends the
calculated summary to Gemini through LangChain and streams back an explanation.
Every failure becomes a message that is safe to show: the API key and raw
provider errors are never displayed.

Quick check that your key and model work:   uv run python main.py
"""
from __future__ import annotations

import json
import logging
import os
import re
from collections.abc import Iterator

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

load_dotenv()  # reads GOOGLE_API_KEY and GEMINI_MODEL from your .env file

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-flash-lite-latest"
MAX_HISTORY_MESSAGES = 6     # only the most recent turns are re-sent
MAX_QUESTION_CHARS = 500

SYSTEM_INSTRUCTION = """You are the Farm Records Assistant. You explain a farmer's recorded data in plain, friendly language.

Rules you must always follow:
1. Use ONLY the calculated summary JSON provided in the latest message. All totals were calculated by Python. Never add up, average or compute new totals, percentages or differences yourself; quote figures exactly as given.
2. 'Recorded balance' is sales revenue minus recorded expenses. Never call it profit. The records may omit costs or other entries.
3. Do not infer sales quantities, prices per kg, yield per hectare, or the causes of any change. If asked 'why', say what the records show, then list what additional information would be needed (for example prices, quantities sold, weather, costs not recorded, or field notes). You may offer possible explanations only if you clearly label them as unverified possibilities.
4. If the summary cannot answer the question, say so plainly.
5. Currency is Ghana cedis (GHS); harvest is in kg. Keep answers short (under 180 words) and use simple words.
6. Give your recommendations in a numbered list, and your possible explanations in a bulleted list."""

PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_INSTRUCTION),
    MessagesPlaceholder("history"),
    ("human", "{task}"),
])


class AIError(Exception):
    """An error message that is safe to show in the interface."""


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
def get_setting(name: str, default: str | None = None) -> str | None:
    """Environment variables / .env first, then Streamlit secrets (for deployment)."""
    value = os.getenv(name)
    if value:
        return value
    try:
        import streamlit as st
        value = st.secrets.get(name)
    except Exception:  # no secrets file, or running outside Streamlit
        value = None
    return str(value) if value else default


def get_api_key() -> str | None:
    return get_setting("GOOGLE_API_KEY") or get_setting("GEMINI_API_KEY")


def is_configured() -> bool:
    return bool(get_api_key())


def model_name() -> str:
    return get_setting("GEMINI_MODEL", DEFAULT_MODEL) or DEFAULT_MODEL


def create_llm():
    """Create the LangChain Gemini chat model (same settings style as your research agent)."""
    key = get_api_key()
    if not key:
        raise AIError(
            "Gemini isn't configured. Add GOOGLE_API_KEY (and GEMINI_MODEL) to your .env file, then restart "
            "the app. Every other part of the app still works without it."
        )
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError as exc:
        raise AIError("LangChain's Gemini package is missing. Run: uv sync") from exc
    return ChatGoogleGenerativeAI(
        model=model_name(), temperature=0, google_api_key=key, max_retries=2, timeout=60)


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #
def friendly_error(exc: Exception) -> str:
    """Turn any provider/network exception into a safe, helpful message (raw text is never shown)."""
    text = f"{type(exc).__name__} {exc}".lower()
    if re.search(r"api key not valid|api_key_invalid|invalid api key|unauthenticated|\b401\b", text):
        return "Gemini rejected the API key. Check GOOGLE_API_KEY in your .env file and restart the app."
    if re.search(r"permission_denied|permission denied|\b403\b", text):
        return "Your key doesn't have access to this model. Try another GEMINI_MODEL or create a new key."
    if re.search(r"\b429\b|resource_exhausted|quota|rate limit", text):
        return "Gemini's rate or quota limit was reached. Wait a minute and try again."
    if re.search(r"\b404\b|not_found|not found|is not supported", text):
        return f"Gemini couldn't find the model '{model_name()}'. Check the GEMINI_MODEL setting."
    if re.search(r"timeout|timed out|deadline", text):
        return "Gemini took too long to answer. Please try again."
    if re.search(r"connect|network|dns|unreachable|name resolution", text):
        return "Couldn't reach Gemini. Check your internet connection and try again."
    if re.search(r"\b50\d\b|unavailable|internal|overloaded", text):
        return "Gemini is temporarily unavailable. Please try again shortly."
    if re.search(r"safety|blocked|prohibited", text):
        return "Gemini declined to answer that. Try rephrasing your question."
    return "Gemini couldn't complete the request. Please try again."


# --------------------------------------------------------------------------- #
# Calling Gemini through LangChain
# --------------------------------------------------------------------------- #
def _text_of(chunk) -> str:
    """Gemini chunks carry either a string or a list of content blocks."""
    content = getattr(chunk, "content", chunk)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "".join(parts)
    return ""


def _history_messages(history: list[dict]) -> list:
    recent = history[-MAX_HISTORY_MESSAGES:]
    while recent and recent[0]["role"] != "user":
        recent = recent[1:]
    return [HumanMessage(m["content"]) if m["role"] == "user" else AIMessage(m["content"]) for m in recent]


def _task(text: str, summary: dict) -> str:
    return ("CALCULATED SUMMARY OF THE CURRENT FILTERED VIEW (computed by Python):\n"
            + json.dumps(summary, indent=1) + "\n\n" + text)


def _stream(llm, task: str, history: list[dict]) -> Iterator[str]:
    produced = False
    try:
        for chunk in (PROMPT | llm).stream({"history": _history_messages(history), "task": task}):
            text = _text_of(chunk)
            if text:
                produced = True
                yield text
    except Exception as exc:
        logger.warning("Gemini call failed: %s", type(exc).__name__)  # type only - never the key or body
        raise AIError(friendly_error(exc)) from None
    if not produced:
        raise AIError("Gemini returned no answer. Try rephrasing your question.")


def stream_answer(llm, question: str, summary: dict, history: list[dict]) -> Iterator[str]:
    """Yield the answer piece by piece. `history` is trimmed; the summary is attached once."""
    question = question.strip()[:MAX_QUESTION_CHARS]
    yield from _stream(llm, _task("QUESTION:\n" + question, summary), history)


def explain_for_report(llm, summary: dict) -> str:
    """Possible explanations + things to check, for the 'unverified' section of the report."""
    task = ("Write the 'possible explanations' section of a farm report in Markdown. Give: "
            "(a) 'What to look at more closely' - 3 to 4 short bullets pointing at patterns visible in the summary "
            "(quote figures exactly, never compute new ones); "
            "(b) 'Possible explanations (unverified)' - 3 to 4 bullets, each phrased as a possibility using words like "
            "'may' or 'could', never as a fact; "
            "(c) 'Information that would be needed to confirm' - 3 to 4 bullets. Do not call the recorded balance profit.")
    return "".join(_stream(llm, _task(task, summary), [])).strip()


# --------------------------------------------------------------------------- #
# Checking AI output
# --------------------------------------------------------------------------- #
_NUMBER = re.compile(r"\d[\d,]*\.?\d*")


def _to_float(token: str) -> float | None:
    try:
        return float(token.replace(",", "").rstrip("."))
    except ValueError:
        return None


def unverified_figures(answer: str, summary: dict) -> list[str]:
    """Figures in the answer that don't appear in the calculated summary (within rounding)."""
    known = [v for v in map(_to_float, _NUMBER.findall(json.dumps(summary))) if v is not None]
    odd = []
    for token in _NUMBER.findall(answer):
        value = _to_float(token)
        if value is None or (value < 10 and value == int(value)):  # list numbers, "2 crops", etc.
            continue
        if not any(abs(value - k) <= 0.51 for k in known):
            odd.append(token.rstrip("."))
    return sorted(set(odd))


# --------------------------------------------------------------------------- #
# Command-line check:  uv run python main.py
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    from pathlib import Path

    import data_utils as du

    print(f"Model: {model_name()} | key found: {is_configured()}")
    csv = Path(__file__).parent / "sample_data" / "agriculture_sample_records.csv"
    df, _ = du.clean_records(du.read_csv_bytes(csv.read_bytes()))
    crops = sorted(df["crop"].unique())
    summary = du.summarize(df, crops, df["date"].min(), df["date"].max())
    try:
        print("\nAI Response:")
        for piece in stream_answer(create_llm(), "Which crop earned the most recorded revenue?", summary, []):
            print(piece, end="", flush=True)
        print("\n\nSuccess: your key and model work.")
    except AIError as err:
        print(f"\nAgent execution failed.\nError: {err}")
