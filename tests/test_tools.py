import pytest
from src.tools.file_ops import WriteFileTool, ReadFileTool
from src.tools.base import ToolRegistry


@pytest.mark.asyncio
async def test_write_then_read_roundtrip(tmp_path):
    target = tmp_path / "note.txt"
    writer = WriteFileTool()
    reader = ReadFileTool()

    write_result = await writer.execute(path=str(target), content="hello tools")
    assert write_result["success"] is True

    read_result = await reader.execute(path=str(target))
    assert read_result["success"] is True
    assert read_result["result"] == "hello tools"


@pytest.mark.asyncio
async def test_read_missing_file_fails_softly():
    reader = ReadFileTool()
    result = await reader.execute(path="definitely_does_not_exist_12345.txt")
    assert result["success"] is False
    assert "File not found" in result["error"]


@pytest.mark.asyncio
async def test_registry_runs_tool(tmp_path):
    reg = ToolRegistry(config=None, working_directory=str(tmp_path))
    reg.register(WriteFileTool())
    result = await reg.execute("write_file", {"path": str(tmp_path / "a.txt"), "content": "x"})
    assert result["success"]


@pytest.mark.asyncio
async def test_unknown_tool_handled():
    reg = ToolRegistry(config=None, working_directory=".")
    result = await reg.execute("no_such_tool", {})
    assert result["success"] is False
    assert "Unknown tool" in result["error"]