"""
Command-line interface for the terminal coding agent.

Builds a CodingAgent and runs an interactive read -> process -> print loop,
plus a few slash-commands for history and snapshots.
"""

import asyncio
import sys

from dotenv import load_dotenv

from src.config import load_config
from src.agent import CodingAgent


HELP_TEXT = """\
Commands:
  /help              Show this help
  /snapshots         List available snapshots
  /rollback <id>     Restore a snapshot by id
  /clear             Clear conversation history
  /exit, /quit       Leave the agent
Anything else is sent to the agent as a request.
"""


async def handle_command(agent, line):
    """Handle a /slash command. Returns True if we should keep looping."""
    parts = line.split()
    cmd = parts[0]

    if cmd in ("/exit", "/quit"):
        print("Goodbye.")
        return False

    if cmd == "/help":
        print(HELP_TEXT)

    elif cmd == "/clear":
        agent.clear_history()
        print("History cleared.")

    elif cmd == "/snapshots":
        snapshots = agent.get_snapshots()
        if not snapshots:
            print("No snapshots yet.")
        else:
            for s in snapshots:
                print(" -", s["id"])

    elif cmd == "/rollback":
        if len(parts) < 2:
            print("Usage: /rollback <id>")
        else:
            result = await agent.rollback(parts[1])
            print(result)

    else:
        print(f"Unknown command: {cmd}. Type /help.")

    return True


async def main():
    load_dotenv()

    try:
        config = load_config()
    except Exception as e:
        print(f"Failed to load configuration: {e}")
        sys.exit(1)

    if not config.validate():
        # validate() already prints why (e.g. missing ANTHROPIC_API_KEY)
        sys.exit(1)

    agent = CodingAgent(config, working_directory=".")
    print("Terminal Coding Agent. Type /help for commands, /exit to quit.")

    while True:
        try:
            line = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not line:
            continue

        if line.startswith("/"):
            keep_going = await handle_command(agent, line)
            if not keep_going:
                break
            continue

        try:
            response = await agent.process_message(line)
            print(response)
        except Exception as e:
            print(f"Error: {e}")


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()