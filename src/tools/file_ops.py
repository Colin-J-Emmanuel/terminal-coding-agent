from src.tools.base import BaseTool
import asyncio

class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Writes text content to a file at the given path"
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path to write to"},
            "content": {"type": "string", "description": "Text content to write"},
        },
        "required": ["path", "content"],
    }

    async def execute(self, path, content):
        with open(path, "w") as f:
            f.write(content)
        return {"success": True, "result": f"Wrote {len(content)} chars to {path}"}
    

class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Reads text content from a file at the given path"
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path to read from"},
        },
        "required": ["path"]
    }

    async def execute(self, path,):
        try:
            with open(path, "r") as f:
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