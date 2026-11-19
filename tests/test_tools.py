import pytest
from src.tools.file_ops import WriteFileTool, ReadFileTool
from src.tools.base import ToolRegistry


@pytest.mark.asyncio
async def test_write_then_read_roundtrip(tmp_path):
    target = tmp_path / "note.txt"
    writer = WriteFileTool(working_directory=tmp_path)
    reader = ReadFileTool(working_directory=tmp_path)

    write_result = await writer.execute(path=str(target), content="hello tools")
    assert write_result["success"] is True

    read_result = await reader.execute(path=str(target))
    assert read_result["success"] is True
    assert read_result["result"] == "hello tools"


@pytest.mark.asyncio
async def test_read_missing_file_fails_softly(tmp_path):
    reader = ReadFileTool(working_directory=tmp_path)
    result = await reader.execute(path="definitely_does_not_exist_12345.txt")
    assert result["success"] is False
    assert "File not found" in result["error"]


@pytest.mark.asyncio
async def test_registry_runs_tool(tmp_path):
    reg = ToolRegistry(config=None, working_directory=str(tmp_path))
    reg.register(WriteFileTool(working_directory=tmp_path))
    result = await reg.execute("write_file", {"path": "a.txt", "content": "x"})
    assert result["success"]


@pytest.mark.asyncio
async def test_unknown_tool_handled():
    reg = ToolRegistry(config=None, working_directory=".")
    result = await reg.execute("no_such_tool", {})
    assert result["success"] is False
    assert "Unknown tool" in result["error"]

# --- Path traversal guard (file_ops._resolve_inside) ---

@pytest.mark.asyncio
async def test_relative_path_lands_in_working_directory(tmp_path):
    writer = WriteFileTool(working_directory=tmp_path)
    result = await writer.execute(path="sub_note.txt", content="hi")
    assert result["success"] is True
    assert (tmp_path / "sub_note.txt").read_text() == "hi"


@pytest.mark.asyncio
async def test_read_dotdot_traversal_denied(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (tmp_path / "secret.txt").write_text("top secret")
    reader = ReadFileTool(working_directory=root)
    result = await reader.execute(path="../secret.txt")
    assert result["success"] is False
    assert "Access denied" in result["error"]
    assert "top secret" not in str(result)


@pytest.mark.asyncio
async def test_write_dotdot_traversal_denied_and_no_file_created(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    writer = WriteFileTool(working_directory=root)
    result = await writer.execute(path="../escaped.txt", content="pwned")
    assert result["success"] is False
    assert "Access denied" in result["error"]
    assert not (tmp_path / "escaped.txt").exists()


@pytest.mark.asyncio
async def test_absolute_path_outside_denied(tmp_path):
    reader = ReadFileTool(working_directory=tmp_path)
    result = await reader.execute(path="/etc/passwd")
    assert result["success"] is False
    assert "Access denied" in result["error"]


@pytest.mark.asyncio
async def test_absolute_path_inside_allowed(tmp_path):
    (tmp_path / "ok.txt").write_text("fine")
    reader = ReadFileTool(working_directory=tmp_path)
    result = await reader.execute(path=str(tmp_path / "ok.txt"))
    assert result["success"] is True
    assert result["result"] == "fine"


@pytest.mark.asyncio
async def test_sibling_prefix_directory_denied(tmp_path):
    # "/tmp/x/project-evil" starts with the string "/tmp/x/project" --
    # a naive str.startswith() check would let this through.
    root = tmp_path / "project"
    root.mkdir()
    evil = tmp_path / "project-evil"
    evil.mkdir()
    (evil / "loot.txt").write_text("loot")
    reader = ReadFileTool(working_directory=root)
    result = await reader.execute(path="../project-evil/loot.txt")
    assert result["success"] is False
    assert "Access denied" in result["error"]


@pytest.mark.asyncio
async def test_symlink_escape_denied(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (tmp_path / "secret.txt").write_text("top secret")
    (root / "link.txt").symlink_to(tmp_path / "secret.txt")
    reader = ReadFileTool(working_directory=root)
    result = await reader.execute(path="link.txt")
    assert result["success"] is False
    assert "Access denied" in result["error"]
