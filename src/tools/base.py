"""
Base classes for the tool system: BaseTool (abstract) and ToolRegistry.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any


class BaseTool(ABC):
    """
    Abstract base class for all tools.

    Every concrete tool must define name / description / input_schema
    and implement the async execute() method.
    """
    name: str = ""
    description: str = ""
    input_schema: Dict[str, Any] = {}

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Run the tool. Must return {"success": bool, ...}."""
        ...


class ToolRegistry:
    """Holds tools and runs them by name on behalf of the agent."""

    def __init__(self, config, working_directory):
        self.config = config
        self.working_directory = working_directory
        self.tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        self.tools[tool.name] = tool

    async def execute(self, name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        if name not in self.tools:
            return {"success": False, "error": f"Unknown tool: {name}"}
        tool = self.tools[name]
        return await tool.execute(**tool_input)

    def get_schemas(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in self.tools.values()
        ]


if __name__ == "__main__":
    import asyncio

    class WriteFileTool(BaseTool):
        name = "write_file"
        description = "Writes text to a file"
        input_schema = {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        }

        async def execute(self, path, content):
            with open(path, "w") as f:
                f.write(content)
            return {"success": True, "result": f"Wrote {len(content)} chars to {path}"}

    registry = ToolRegistry(config=None, working_directory=".")
    registry.register(WriteFileTool())

    print(asyncio.run(registry.execute("write_file", {"path": "hello3.txt", "content": "from base.py"})))
    print(asyncio.run(registry.execute("delete_everything", {})))
    print(registry.get_schemas())