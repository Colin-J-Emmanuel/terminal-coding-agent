"""
Git tools: one tool per operation, each restricted to a single git command.

Safety by construction — there is no tool that runs arbitrary git, so the agent
cannot reach destructive commands (push --force, reset --hard, clean) because
none of these tools can express them.
"""

import subprocess

from src.tools.base import BaseTool


def _run_git(args, cwd):
    """Run one git command, return a standard result dict."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=15,
        )
        if result.returncode == 0:
            return {"success": True, "result": result.stdout.strip() or "(no output)"}
        return {"success": False, "error": result.stderr.strip() or "git command failed"}
    except FileNotFoundError:
        return {"success": False, "error": "git is not installed or not on PATH"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "git command timed out"}


class GitStatusTool(BaseTool):
    name = "git_status"
    description = "Shows the working-tree status (modified, staged, and untracked files)"
    input_schema = {"type": "object", "properties": {}}

    def __init__(self, working_directory="."):
        self.working_directory = working_directory

    async def execute(self):
        return _run_git(["status"], self.working_directory)

class GitDiffTool(BaseTool):
    name = "git_diff"
    description = "Showing unstaged changes"
    input_schema = {"type": "object", "properties": {}}

    def __init__(self, working_directory="."):
        self.working_directory = working_directory

    async def execute(self):
        return _run_git(["diff"], self.working_directory)
    
class GitCommitTool(BaseTool):
    name = "git_commit"
    description = "showing committed files and a commit message"
    input_schema = {
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "The commit message"},
        },
        "required": ["message"],
    }

    def __init__(self, working_directory="."):
        self.working_directory = working_directory

    async def execute(self, message):
        # Step 1: stage everything.
        add_result = _run_git(["add", "-A"], self.working_directory)
        # If staging failed, don't try to commit - return the error.
        if not add_result["success"]:
            return add_result
        # Step 2: commit with the message.
        return _run_git(["commit", "-m", message], self.working_directory)
    
if __name__ == "__main__":
    import asyncio
    print("status:", asyncio.run(GitStatusTool(".").execute()))
    print("diff:", asyncio.run(GitDiffTool(".").execute()))