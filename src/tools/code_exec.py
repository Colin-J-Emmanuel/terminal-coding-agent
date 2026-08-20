"""
CodeExecutionTool: validate-then-execute gate.

Runs code through the AST validator first; only code that passes reaches the
sandboxed executor. Blocked code never runs.
"""

from src.tools.base import BaseTool
from src.execution.validator import CodeValidator
from src.execution.executor import CodeExecutor
from src.execution.docker_executor import DockerExecutor


class CodeExecutionTool(BaseTool):
    name = "execute_code"
    description = "Executes Python code in a sandboxed subprocess and returns its output"
    input_schema = {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Python code to execute"},
        },
        "required": ["code"],
    }

    def __init__(self, timeout=5, cpu_seconds=2, memory_mb=100):
        self.validator = CodeValidator()
        # Prefer Docker isolation; fall back to the subprocess sandbox if Docker
        # isn't available so the tool still works on machines without it.
        if DockerExecutor.is_available():
            self.executor = DockerExecutor(timeout=timeout + 5, memory_mb=memory_mb)
            self.engine = "docker"
        else:
            self.executor = CodeExecutor(timeout=timeout, cpu_seconds=cpu_seconds, memory_mb=memory_mb)
            self.engine = "subprocess"

    async def execute(self, code):
        # Gate 1: validate. Blocked code never reaches the executor.
        check = self.validator.validate(code)
        if not check["safe"]:
            return {
                "success": False,
                "blocked": True,
                "error": "Code blocked by validator",
                "violations": check["violations"],
            }

        # Gate 2: run in the sandbox.
        result = self.executor.execute(code)
        return {
            "success": result["success"],
            "blocked": False,
            "result": result["output"],
            "error": result["error"],
        }


if __name__ == "__main__":
    import asyncio
    tool = CodeExecutionTool()

    print("=== safe code that runs ===")
    print(asyncio.run(tool.execute("print(2 + 2)")))

    print("\n=== dangerous code (blocked, never runs) ===")
    print(asyncio.run(tool.execute("import os\nos.system('echo pwned')")))

    print("\n=== safe code that runs but crashes ===")
    print(asyncio.run(tool.execute("print(1/0)")))