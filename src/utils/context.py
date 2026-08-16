"""
ContextManager: persists conversation history to disk so a session
can be saved, reloaded, and cleared.
"""

import json
from pathlib import Path
from typing import List, Dict, Any


class ContextManager:
    """
    Manages persistence of the agent's conversation history.

    agent.py calls:
      - save_history(history)   after every message
      - clear_history()         on /clear
    load_history() is provided for restoring a session on startup.
    """

    def __init__(self, config):
        self.config = config
        history_file = ".agent_history.json"
        if config is not None:
            history_file = config.get("context.history_file", history_file)
        self.history_file = Path(history_file)

    def save_history(self, history: List[Dict[str, Any]]) -> None:
        """Write the full conversation history to disk as JSON."""
        try:
            with open(self.history_file, "w") as f:
                json.dump(history, f, indent=2)
        except OSError as e:
            print(f"Warning: could not save history: {e}")

    def load_history(self) -> List[Dict[str, Any]]:
        """Load conversation history from disk, or [] if none exists."""
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, "r") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"Warning: could not load history: {e}")
            return []

    def clear_history(self) -> None:
        """Delete the stored history file."""
        try:
            if self.history_file.exists():
                self.history_file.unlink()
        except OSError as e:
            print(f"Warning: could not clear history: {e}")


if __name__ == "__main__":
    cm = ContextManager(config=None)
    sample = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi there"},
    ]
    cm.save_history(sample)
    print("saved:", sample)
    print("loaded:", cm.load_history())
    cm.clear_history()
    print("after clear:", cm.load_history())