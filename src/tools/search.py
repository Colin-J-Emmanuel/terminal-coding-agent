"""
SearchTool: content search across the working directory (grep-style).

Walks the tree, skips noise dirs and unreadable/binary files, and returns
matching lines with file + line number so the agent can navigate a codebase.
"""

from pathlib import Path

from src.tools.base import BaseTool

IGNORE_DIRS = {".git", ".snapshots", "venv", "__pycache__", ".egg-info"}


def _iter_files(root):
    root = Path(root)
    for path in root.rglob("*"):
        if any(part in IGNORE_DIRS or part.endswith(".egg-info") for part in path.parts):
            continue
        if path.is_file():
            yield path


class SearchTool(BaseTool):
    name = "search_code"
    description = "Searches file contents in the working directory for a text query, grep-style"
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Text to search for in file contents"},
        },
        "required": ["query"],
    }

    def __init__(self, working_directory="."):
        self.working_directory = working_directory

    async def execute(self, query):
        matches = []
        for path in _iter_files(self.working_directory):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for lineno, line in enumerate(f, start=1):
                        if query in line:
                            matches.append({
                                "file": str(path),
                                "line": lineno,
                                "text": line.rstrip(),
                            })
            except (UnicodeDecodeError, OSError):
                continue
        return {"success": True, "result": matches, "count": len(matches)}


if __name__ == "__main__":
    import asyncio
    tool = SearchTool(working_directory="src")
    out = asyncio.run(tool.execute("def execute"))
    print(f"found {out['count']} matches for 'def execute':\n")
    for m in out["result"]:
        print(f"  {m['file']}:{m['line']}: {m['text']}")