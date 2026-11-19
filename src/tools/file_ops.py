from pathlib import Path
from src.tools.base import BaseTool
import asyncio


def _resolve_inside(root, path):
    """
    Resolve `path` against `root` and confirm the result stays inside `root`.

    Why resolve first: the danger isn't the string the LLM sends, it's where
    that string actually lands on disk. "../../etc/passwd", "/etc/passwd", and a
    symlink inside the project that points outside it all look different as
    strings but end up outside the sandbox. Path.resolve() collapses "..",
    makes the path absolute, and follows symlinks, so we check the real
    destination instead of trying to blacklist bad-looking strings.

    Returns the resolved Path, or None if it escapes the root.
    """
    root = Path(root).resolve()
    # Relative paths are anchored to the agent's working directory, not to
    # whatever directory the process happened to be launched from.
    # (If `path` is absolute, `root / path` just returns `path`.)
    target = (root / path).resolve()
    if target == root or target.is_relative_to(root):
        return target
    return None


def _outside_error(path, root):
    return {
        "success": False,
        "error": f"Access denied: '{path}' is outside the working directory ({Path(root).resolve()})",
    }


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Writes text content to a file at the given path (must be inside the working directory)"
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path to write to, relative to the working directory"},
            "content": {"type": "string", "description": "Text content to write"},
        },
        "required": ["path", "content"],
    }

    def __init__(self, working_directory="."):
        self.working_directory = working_directory

    async def execute(self, path, content):
        target = _resolve_inside(self.working_directory, path)
        if target is None:
            return _outside_error(path, self.working_directory)
        with open(target, "w") as f:
            f.write(content)
        return {"success": True, "result": f"Wrote {len(content)} chars to {path}"}


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Reads text content from a file at the given path (must be inside the working directory)"
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path to read from, relative to the working directory"},
        },
        "required": ["path"]
    }

    def __init__(self, working_directory="."):
        self.working_directory = working_directory

    async def execute(self, path):
        target = _resolve_inside(self.working_directory, path)
        if target is None:
            return _outside_error(path, self.working_directory)
        try:
            with open(target, "r") as f:
                content = f.read()
            return {"success": True, "result": content}
        except FileNotFoundError:
            return {"success": False, "error": f"File not found: {path}"}


if __name__ == "__main__":
    t = WriteFileTool()
    v = ReadFileTool()
    print(asyncio.run(t.execute(path="test_output.txt", content="hello from file_ops")))
    print(asyncio.run(v.execute(path="test_output.txt")))
    print(asyncio.run(v.execute(path="nope.txt")))
    print(asyncio.run(v.execute(path="../../etc/passwd")))   # should be denied
    print(asyncio.run(v.execute(path="/etc/passwd")))        # should be denied
