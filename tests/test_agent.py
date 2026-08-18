import os
import pytest
from unittest.mock import AsyncMock
from types import SimpleNamespace

# The agent builds a real ClaudeProvider in __init__, which requires an API key
# to even construct. We set a dummy key so construction succeeds; the real call
# is always replaced by a mock below, so this key is never actually used.
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-dummy")

from src.agent import CodingAgent
from src.config import Config


def make_agent():
    config = Config()
    config.config = {
        "llm": {"model": "test-model", "max_tokens": 100},
        "safety": {"max_iterations": 5},
    }
    return CodingAgent(config, working_directory=".")


def text_block(text):
    return SimpleNamespace(type="text", text=text)


def tool_block(tool_id, name, tool_input):
    return SimpleNamespace(type="tool_use", id=tool_id, name=name, input=tool_input)


@pytest.mark.asyncio
async def test_plain_text_response_ends_loop():
    agent = make_agent()
    agent.llm.call = AsyncMock(return_value=([text_block("All done!")], None))

    result = await agent.process_message("say hi")

    assert "All done!" in result
    assert agent.llm.call.call_count == 1
    assert agent.iteration_count == 1


@pytest.mark.asyncio
async def test_tool_call_then_finish():
    agent = make_agent()
    agent.llm.call = AsyncMock(side_effect=[
        ([tool_block("t1", "write_file", {"path": "x.txt", "content": "hi"})], None),
        ([text_block("File written.")], None),
    ])

    result = await agent.process_message("write x.txt")

    assert "File written." in result
    assert agent.llm.call.call_count == 2


@pytest.mark.asyncio
async def test_llm_error_is_surfaced():
    agent = make_agent()
    agent.llm.call = AsyncMock(return_value=(None, "rate limited"))

    result = await agent.process_message("anything")

    assert "rate limited" in result