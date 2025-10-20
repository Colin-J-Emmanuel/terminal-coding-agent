"""
LLM Provider wrapper for Claude API.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
import anthropic

from src.config import Config


class ClaudeProvider:
    """
    Wrapper for Anthropic's Claude API.
    
    Handles:
    - API authentication
    - Message formatting
    - Tool schema management
    - Error handling
    """
    
    def __init__(self, config: Config):
        self.config = config
        
        # Initialize Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment variables. "
                "Please set it in your .env file."
            )
        
        self.client = anthropic.Anthropic(api_key=api_key)
        
        # Get model configuration
        self.model = config.get("llm.model", "claude-sonnet-4-20250514")
        self.max_tokens = config.get("llm.max_tokens", 4000)
        self.temperature = config.get("llm.temperature", 0.7)
        self.timeout = config.get("llm.timeout", 60)
        
        # System prompt
        self.system_prompt = config.get("system_prompt", self._default_system_prompt())
    
    async def call(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None
    ) -> Tuple[Any, Optional[str]]:
        """
        Call Claude API with messages and optional tools.
        
        Args:
            messages: List of conversation messages
            tools: Optional list of tool definitions
            
        Returns:
            Tuple of (response_content, error_message)
        """
        try:
            # Prepare tool schemas if provided
            tool_params = []
            if tools:
                for tool in tools:
                    tool_params.append(anthropic.ToolParam(
                        name=tool["name"],
                        description=tool["description"],
                        input_schema=tool["input_schema"]
                    ))
            
            # Make API call
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=self.system_prompt,
                messages=messages,
                tools=tool_params if tool_params else anthropic.NOT_GIVEN,
                timeout=self.timeout
            )
            
            return response.content, None
            
        except anthropic.APIError as e:
            return None, f"API Error: {str(e)}"
        except anthropic.APIConnectionError as e:
            return None, f"Connection Error: {str(e)}"
        except anthropic.RateLimitError as e:
            return None, f"Rate Limit Error: {str(e)}"
        except anthropic.APITimeoutError as e:
            return None, f"Timeout Error: {str(e)}"
        except Exception as e:
            return None, f"Unexpected error: {str(e)}"
    
    def _default_system_prompt(self) -> str:
        """
        Default system prompt if not provided in config.
        """
        return """You are a helpful coding agent that assists with programming tasks and file operations.

When responding to requests:
1. Analyze what the user needs
2. Break down complex tasks into steps
3. Use the minimum number of tools necessary to accomplish the task
4. After using tools, provide a concise summary of what was done
5. Request confirmation before destructive operations

IMPORTANT: Once you've completed the requested task, STOP and provide your final response. 
Do not continue creating additional files or performing extra actions unless specifically asked.

Examples of good behavior:
- User: "Create a file that adds numbers" → Create ONE file, then summarize
- User: "Create files for add and subtract" → Create ONLY those two files, then summarize
- User: "Create math operation files" → Ask for clarification on which operations, or create a reasonable set and stop

After receiving tool results:
- If the task is complete, provide a final summary
- Only continue with more tools if the original request is not yet fulfilled
- Do not interpret successful tool execution as a request to do more

Be concise and efficient. Complete the requested task and stop."""
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Note: This is an approximation. For exact counts, use
        the Anthropic token counting API.
        """
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4
    
    def format_tool_error(self, error: str) -> str:
        """
        Format error message for tool execution failures.
        """
        return f"Tool execution failed: {error}"