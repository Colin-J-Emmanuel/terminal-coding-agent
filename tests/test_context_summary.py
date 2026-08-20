import os
import pytest
from unittest.mock import AsyncMock
from types import SimpleNamespace

os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-dummy")

from src.agent import CodingAgent
from src.config import Config


def make_agent(threshold=10, keep_recent=4):
    config = Config()
    config.config_data = {
        "llm": {"model": "test-model", "max_tokens": 100},
        "safety": {"max_iterations": 5},
        "context": {"summary_threshold": threshold, "keep_recent": keep_recent},
    }
    return CodingAgent(config, working_directory=".")


def summary_block(text):
    return SimpleNamespace(type="text", text=text)


@pytest.mark.asyncio
async def test_short_history_not_summarized():
    agent = make_agent(threshold=10)
    agent.llm.call = AsyncMock()
    history = [{"role": "user", "content": f"m{i}"} for i in range(6)]

    result = await agent._summarize_history(history)

    assert len(result) == 6
    assert agent.llm.call.called is False


@pytest.mark.asyncio
async def test_long_history_is_compressed():
    agent = make_agent(threshold=10, keep_recent=4)
    agent.llm.call = AsyncMock(return_value=([summary_block("a summary")], None))
    history = [{"role": "user", "content": f"m{i}"} for i in range(14)]

    result = await agent._summarize_history(history)

    assert len(result) < len(history)          # it actually got shorter
    assert "summary" in result[0]["content"]   # first message is the summary


@pytest.mark.asyncio
async def test_recent_turns_survive_verbatim():
    agent = make_agent(threshold=10, keep_recent=4)
    agent.llm.call = AsyncMock(return_value=([summary_block("a summary")], None))
    history = [{"role": "user", "content": f"m{i}"} for i in range(14)]

    result = await agent._summarize_history(history)

    assert len(result) == 5
    assert result[-1]["content"] == "m13"
    assert agent.llm.call.call_count == 1


@pytest.mark.asyncio
async def test_summary_failure_preserves_history():
    agent = make_agent(threshold=10, keep_recent=4)
    agent.llm.call = AsyncMock(return_value=(None, "api error"))
    history = [{"role": "user", "content": f"m{i}"} for i in range(14)]

    result = await agent._summarize_history(history)

    assert len(result) == 14