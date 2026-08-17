"""
Core Agent Orchestrator implementing the ReAct (Reason-Act-Observe) pattern.
"""

import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from src.llm_provider import ClaudeProvider
from src.tools.base import ToolRegistry
from src.utils.context import ContextManager
from src.utils.snapshots import SnapshotManager
from src.config import Config
from src.tools.file_ops import WriteFileTool, ReadFileTool
from src.tools.code_exec import CodeExecutionTool


class CodingAgent:
    """
    Main agent class that orchestrates the ReAct loop.
    
    Architecture:
    - Maintains conversation history
    - Coordinates between LLM and tools
    - Manages context and state
    - Implements safety checks
    """
    
    def __init__(
        self,
        config: Config,
        working_directory: str = ".",
    ):
        self.config = config
        self.working_directory = Path(working_directory).resolve()
        
        # Initialize components
        self.llm = ClaudeProvider(config)
        self.tools = ToolRegistry(config, self.working_directory)
        self._register_tools()
        self.context = ContextManager(config)
        self.snapshots = SnapshotManager(self.working_directory)
        
        # State
        self.conversation_history: List[Dict[str, Any]] = []
        self.iteration_count = 0
        
    def _register_tools(self):
        self.tools.register(WriteFileTool())
        self.tools.register(ReadFileTool())
        self.tools.register(CodeExecutionTool())

    async def process_message(self, user_input: str) -> str:
        """
        Main entry point for processing user messages.
        
        Args:
            user_input: Natural language command from user
            
        Returns:
            Final response from the agent
        """
        try:
            # Add user message to history
            self.add_message("user", user_input)
            
            # Run the ReAct loop
            response = await self.react_loop(user_input)
            
            # Add assistant response to history
            self.add_message("assistant", response)
            
            return response
            
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            self.add_message("assistant", error_msg)
            return error_msg
    
    async def react_loop(self, user_input: str) -> str:
        """
        Implements the ReAct (Reason-Act-Observe) pattern.
        
        Loop:
        1. REASON: LLM analyzes situation and decides actions
        2. ACT: Execute tools based on LLM's decisions
        3. OBSERVE: Incorporate tool results back to LLM
        4. Repeat until task complete or max iterations reached
        """
        
        # Build initial message list
        messages = self.build_messages_list(user_input=user_input)
        
        # Track last complete response
        last_response = None
        
        # Safety limit to prevent infinite loops
        max_iterations = self.config.get("safety.max_iterations", 20)
        self.iteration_count = 0
        
        while self.iteration_count < max_iterations:
            self.iteration_count += 1
            
            # === REASON: Get LLM's response ===
            content_blocks, error = await self.llm.call(
                messages, tools=self.tools.get_schemas()
                )
            
            if error:
                return f"Error: {error}"
            
            # Parse response into text and tool calls
            text_responses, tool_calls = self._parse_response(content_blocks)
            
            # Store last text response
            if text_responses:
                last_response = "\n".join(text_responses)
            
            # If no tools requested, task is complete
            if not tool_calls:
                break
            
            # === ACT: Execute the requested tools ===
            tool_results = await self._execute_tools(tool_calls)
            
            # === OBSERVE: Build next message with tool results ===
            messages = self.build_messages_list(
                assistant_content=content_blocks,
                tool_results=tool_results
            )
        
        # Prepare final response
        if not last_response:
            final_response = "I couldn't generate a response."
        elif self.iteration_count >= max_iterations:
            final_response = (
                f"{last_response}\n\n"
                "(Note: Reached processing limit. Consider breaking this into smaller steps.)"
            )
        else:
            final_response = last_response
        
        return final_response
    
    async def _execute_tools(self, tool_calls: List[Dict]) -> List[Dict]:
        """
        Execute tool calls and return results.
        
        Args:
            tool_calls: List of tool call requests from LLM
            
        Returns:
            List of tool results
        """
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            tool_input = tool_call.get("input", {})
            tool_id = tool_call.get("id")
            
            print(f"🔧 Executing: {tool_name}")
            
            try:
                # Check if tool requires confirmation
                if self._requires_confirmation(tool_name):
                    confirmed = await self._get_user_confirmation(tool_name, tool_input)
                    if not confirmed:
                        result = {
                            "success": False,
                            "error": "User declined operation"
                        }
                        results.append({
                            "tool_use_id": tool_id,
                            "content": json.dumps(result)
                        })
                        continue
                
                # Create snapshot before destructive operations
                if self._is_destructive(tool_name):
                    self.snapshots.create_snapshot(f"before_{tool_name}")
                
                # Execute the tool
                result = await self.tools.execute(tool_name, tool_input)
                
                print(f"✓ Tool executed successfully")
                
            except Exception as e:
                result = {"success": False, "error": str(e)}
                print(f"✗ Tool execution failed: {str(e)}")
            
            results.append({
                "tool_use_id": tool_id,
                "content": json.dumps(result)
            })
        
        return results
    
    def _parse_response(self, content_blocks: List) -> Tuple[List[str], List[Dict]]:
        """
        Parse LLM response into text and tool calls.
        
        Args:
            content_blocks: Raw content blocks from LLM
            
        Returns:
            Tuple of (text_responses, tool_calls)
        """
        text_responses = []
        tool_calls = []
        
        for block in content_blocks:
            if hasattr(block, 'type'):
                if block.type == "text":
                    text_responses.append(block.text)
                    print(f"💭 {block.text}")
                elif block.type == "tool_use":
                    tool_calls.append({
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })
                    print(f"🔧 Tool call: {block.name}")
        
        return text_responses, tool_calls
    
    def build_messages_list(
        self,
        user_input: Optional[str] = None,
        tool_results: Optional[List[Dict]] = None,
        assistant_content: Optional[Any] = None,
        max_history: int = 20
    ) -> List[Dict]:
        """
        Build messages list for LLM API call.
        
        Args:
            user_input: New user message
            tool_results: Results from tool execution
            assistant_content: Previous assistant response
            max_history: Maximum conversation history to include
            
        Returns:
            List of messages formatted for API
        """
        messages = []
        
        # Add recent conversation history (context window management)
        start_idx = max(0, len(self.conversation_history) - max_history)
        for msg in self.conversation_history[start_idx:]:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Add new user input
        if user_input:
            messages.append({
                "role": "user",
                "content": user_input
            })
        
        # Add assistant content (for tool use continuation)
        if assistant_content:
            messages.append({
                "role": "assistant",
                "content": assistant_content
            })
        
        # Add tool results as user message
        if tool_results:
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tr["tool_use_id"],
                        "content": tr["content"]
                    }
                    for tr in tool_results
                ]
            })
        
        return messages
    
    def add_message(self, role: str, content: str):
        """Add message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
        self.context.save_history(self.conversation_history)
    
    def _requires_confirmation(self, tool_name: str) -> bool:
        """Check if tool requires user confirmation."""
        confirmation_tools = self.config.get(
            "cli.require_confirmation_for",
            ["write_file", "execute_code", "rollback"]
        )
        return tool_name in confirmation_tools
    
    def _is_destructive(self, tool_name: str) -> bool:
        """Check if tool is destructive (modifies files)."""
        destructive_tools = ["write_file", "execute_code"]
        return tool_name in destructive_tools
    
    async def _get_user_confirmation(self, tool_name: str, tool_input: Dict) -> bool:
        """
        Get user confirmation for destructive operations.
        
        TODO: This will be implemented by the CLI layer
        For now, return True to allow operations
        """
        return True
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        self.context.clear_history()
    
    def get_snapshots(self) -> List[Dict]:
        """Get list of available snapshots."""
        return self.snapshots.list_snapshots()
    
    async def rollback(self, snapshot_id: str) -> bool:
        """Rollback to a previous snapshot."""
        return self.snapshots.restore_snapshot(snapshot_id)