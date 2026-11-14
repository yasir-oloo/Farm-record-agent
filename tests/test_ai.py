"""LangChain/Gemini checks that need no real API key (the model is replaced by a fake)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from langchain_core.runnables import RunnableLambda

import data_utils as du
import main as ai

DATA = Path(__file__).resolve().parents[1] / "sample_data"


def summary():
    df, _ = du.clean_records(du.read_csv_bytes((DATA / "agriculture_sample_records.csv").read_bytes()))
    return du.summarize(df, sorted(df["crop"].unique()), df["date"].min(), df["date"].max())


def fake_llm(text="Maize earned GHS 890.", captured=None):
    def run(prompt_value):
        if captured is not None:
            captured["messages"] = prompt_value.to_messages()
        from langchain_core.messages import AIMessage
        return AIMessage(content=text)
    return RunnableLambda(run)


def failing_llm(message):
    def run(_):
        raise RuntimeError(message)
    return RunnableLambda(run)


def test_missing_key_gives_friendly_error(monkeypatch):
    monkeypatch.setattr(ai, "get_setting", lambda name, default=None: default)
    with pytest.raises(ai.AIError) as exc:
        ai.create_llm()
    assert "GOOGLE_API_KEY" in str(exc.value)


def test_default_model_is_flash_lite(monkeypatch):
    monkeypatch.setattr(ai, "get_setting", lambda name, default=None: default)
    assert ai.model_name() == "gemini-flash-lite-latest"


def test_llm_is_built_with_key_and_model(monkeypatch):
    values = {"GOOGLE_API_KEY": "fake-key", "GEMINI_MODEL": "gemini-flash-lite-latest"}
    monkeypatch.setattr(ai, "get_setting", lambda name, default=None: values.get(name, default))
    llm = ai.create_llm()
    assert type(llm).__name__ == "ChatGoogleGenerativeAI"
    assert "flash-lite" in llm.model


def test_streaming_answer_text():
    assert "".join(ai.stream_answer(fake_llm(), "Which crop?", summary(), [])) == "Maize earned GHS 890."


def test_gemini_content_blocks_are_handled():
    blocks = [{"type": "text", "text": "Hello "}, {"type": "thinking", "thinking": "x"}, {"type": "text", "text": "farm"}]
    from langchain_core.messages import AIMessage
    llm = RunnableLambda(lambda _: AIMessage(content=blocks))
    assert "".join(ai.stream_answer(llm, "q", summary(), [])) == "Hello farm"


def test_history_trimmed_and_summary_attached_once():
    seen = {}
    history = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"m{i}"} for i in range(20)]
    "".join(ai.stream_answer(fake_llm(captured=seen), "Why did maize revenue change?", summary(), history))
    msgs = seen["messages"]
    assert msgs[0].type == "system" and "never" in msgs[0].content.lower()
    assert len(msgs) <= ai.MAX_HISTORY_MESSAGES + 2          # system + history + latest question
    assert msgs[1].type == "human"
    assert sum("CALCULATED SUMMARY" in str(m.content) for m in msgs) == 1


@pytest.mark.parametrize("raw, expected", [
    ("400 API key not valid. Please pass a valid API key. sk-SECRET", "rejected the API key"),
    ("403 PERMISSION_DENIED", "access to this model"),
    ("429 RESOURCE_EXHAUSTED quota exceeded", "quota"),
    ("404 models/foo is not found", "couldn't find the model"),
    ("Read timed out", "too long"),
    ("Failed to connect: name resolution", "internet connection"),
    ("503 UNAVAILABLE overloaded", "temporarily unavailable"),
    ("something odd", "couldn't complete"),
])
def test_api_failures_become_safe_messages(raw, expected):
    with pytest.raises(ai.AIError) as exc:
        "".join(ai.stream_answer(failing_llm(raw), "q", summary(), []))
    assert expected in str(exc.value)
    assert "SECRET" not in str(exc.value) and raw not in str(exc.value)


def test_empty_answer_is_reported():
    with pytest.raises(ai.AIError):
        "".join(ai.stream_answer(fake_llm(text=""), "q", summary(), []))


def test_report_explanations_use_summary():
    seen = {}
    text = ai.explain_for_report(fake_llm("- Look at Tomato.", seen), summary())
    assert text == "- Look at Tomato."
    assert "possible explanations" in str(seen["messages"][-1].content).lower()
