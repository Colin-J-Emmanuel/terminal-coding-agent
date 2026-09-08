# Terminal-Based Coding Agent

[![CI](https://github.com/Colin-J-Emmanuel/terminal-coding-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Colin-J-Emmanuel/terminal-coding-agent/actions/workflows/ci.yml)

A terminal coding agent that takes natural-language instructions, reasons about
them, and acts on your filesystem through a set of tools — writing and reading
files, searching a codebase, and running code inside a sandbox. It's built
around the ReAct (Reason–Act–Observe) loop and talks to Anthropic's Claude API.

> **About this project.** This is a personal learning project. I built the
> load-bearing pieces by hand — the tool system, the code validator, the
> execution sandbox, and the agent loop — to understand how coding agents work
> end to end, and used AI assistance only for boilerplate and test scaffolding.
> The goal was depth of understanding, not shipping a product, so the
> **Known Limitations** section below is deliberately candid about where the
> boundaries are.

## What it does

- **Natural-language interface** — issue requests in plain English at a terminal prompt.
- **ReAct loop** — the agent reasons, calls a tool, observes the result, and repeats until the task is done.
- **File tools** — create/overwrite files (`write_file`) and read them back (`read_file`).
- **Code search** — grep-style content search across the working directory (`search_code`).
- **Git tools** — read repo status and diffs, and stage-and-commit with a message (`git_status`, `git_diff`, `git_commit`); commits require confirmation.
- **Context management** — when history grows past a threshold, older turns are summarized by the LLM while recent turns are kept verbatim, keeping the conversation within budget.
- **Multi-file refactoring** — the agent composes search + read + write to rename a symbol across files, preserving syntax; verified on small multi-file cases (see limitations for scale caveats).
- **Sandboxed code execution** — runs Python in an isolated subprocess with a timeout and, where the OS allows, CPU/memory caps (`execute_code`), gated by a static validator that runs first.
- **Snapshots** — file snapshots are taken before destructive operations, with rollback via a CLI command.

## Architecture

The agent follows the ReAct (Reason–Act–Observe) pattern:

```
User input → Reason (LLM) → Act (tool) → Observe (result) → … → Response
```

The loop maintains a single, growing message list: each turn the assistant's
tool call and the tool's result are appended to the same conversation, so the
model always sees its own prior actions.

### Components

| Component | File | Responsibility |
|---|---|---|
| Agent orchestrator | `src/agent.py` | Runs the ReAct loop; parses responses; dispatches tools |
| LLM provider | `src/llm_provider.py` | Claude API wrapper |
| Tool base + registry | `src/tools/base.py` | `BaseTool` contract and name→tool dispatch |
| File tools | `src/tools/file_ops.py` | `write_file`, `read_file` |
| Code search | `src/tools/search.py` | `search_code` |
| Code execution tool | `src/tools/code_exec.py` | Validate-then-execute gate |
| Validator | `src/execution/validator.py` | AST-based static check (blocks dangerous imports) |
| Executor | `src/execution/executor.py` | Sandboxed subprocess with timeout + resource caps |
| Docker executor | `src/execution/docker_executor.py` | Container-isolated execution (preferred when Docker is available) |
| Context | `src/utils/context.py` | Conversation-history persistence |
| Snapshots | `src/utils/snapshots.py` | File snapshot + rollback |
| CLI | `src/cli.py` | Interactive prompt and slash-commands |
| Config | `src/config.py` | YAML + env config loader |

## Installation

### Prerequisites

- Python 3.10+
- An Anthropic API key
- Docker (optional) — for container-isolated code execution; without it, the agent falls back to a subprocess sandbox.

### Setup

```bash
git clone https://github.com/Colin-J-Emmanuel/terminal-coding-agent.git
cd terminal-coding-agent

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
pip install -e .

cp .env.example .env              # then edit .env and add your ANTHROPIC_API_KEY
```

## Usage

Start the agent:

```bash
python -m src.cli
```

Then talk to it:

```
> create a file called hello.py that prints hello world
> read the file hello.py
> run this python code: print(sum(range(101)))
> search the code for ToolRegistry
```

### CLI commands

- `/help` — show available commands
- `/snapshots` — list available snapshots
- `/rollback <id>` — restore a snapshot by id
- `/clear` — clear conversation history
- `/exit`, `/quit` — leave the agent

## Configuration

`config.yaml` controls the model string, token limit, safety iteration cap, and
the code-execution timeout / CPU / memory settings. The API key is read from
`.env` (never commit it). See `.env.example` for the expected variables.

## Safety model

Code execution is guarded in two stages — a cheap static filter, then real
containment:

1. **Static validation** (`validator.py`) — parses the code into an AST and
   blocks dangerous imports (`os`, `subprocess`, `socket`, `sys`, `shutil`),
   handling both `import x` and `from x import y`. Unparseable code is rejected
   (fail-closed).
2. **Sandboxed execution** (`executor.py`) — code that passes runs in a separate
   subprocess with:
   - a **wall-clock timeout** (kills infinite loops),
   - a **CPU-time cap** (`RLIMIT_CPU`),
   - a **memory cap** (`RLIMIT_AS`) where the OS supports it.

The validator is a first filter, not a security boundary — it's a blocklist, and
blocklists are inherently incomplete. The real containment is the executor.

When Docker is available, code runs inside a container (`--network none`, a hard
memory cap, and an isolated filesystem), which provides genuine isolation. When
Docker is not present, the tool falls back to the subprocess sandbox
(timeout + resource limits) so it still works everywhere. The design favors
*bounding what code can do* over trying to enumerate everything dangerous it
might try.

## Known limitations

This is a learning project, and these boundaries are intentional and documented
rather than hidden:

- **Refactoring is verified only at small scale.** Multi-file rename works by
  rewriting whole files from the model's output, verified on a 3-file case with
  syntax checks. This has not been tested on large files or many files, where
  full-file regeneration gets riskier and more token-expensive; a line-level
  edit tool would be the next step for scale.
- **Isolation depends on Docker being present.** With Docker, code runs in a
  container with no network and an enforced memory cap — genuine isolation. The
  AST validator alone can be evaded (`__import__`, `eval`, `importlib`), so on
  machines *without* Docker the fallback subprocess sandbox is defense-in-depth,
  not a hard boundary. Container hardening (seccomp, read-only rootfs, dropped
  capabilities) would be the next step.
- **Subprocess memory capping is platform-dependent.** In the *subprocess*
  fallback, `RLIMIT_AS` works on Linux but is refused by macOS, so the memory cap
  is skipped there (timeout and CPU cap still apply). The Docker path does not
  have this problem — its `--memory` cap is enforced on all platforms. Found by
  testing per-platform, not assumed.
- **No path sandboxing.** Tools operate within the working directory by
  convention but do not hard-enforce a filesystem boundary.
- **Eager provider construction.** The agent builds its LLM provider in
  `__init__`, which couples construction to a live API key; tests work around
  this with a dummy key. Dependency injection would be the cleaner design.

## Development

### Project structure

```
terminal-coding-agent/
├── src/
│   ├── agent.py            # ReAct orchestrator
│   ├── cli.py              # terminal interface
│   ├── llm_provider.py     # Claude API wrapper
│   ├── config.py           # config loader
│   ├── tools/              # base, file_ops, search, code_exec
│   ├── execution/          # validator, executor
│   └── utils/              # context, snapshots
├── tests/                  # pytest suite
├── config.yaml
├── requirements.txt
└── setup.py
```

### Running tests

```bash
pytest tests/
```

The suite (15 tests) covers the executor (success, crash, timeout, stream
separation), the tools (read/write round-trip, missing-file handling, unknown-tool
handling), and the agent loop itself — the LLM is **mocked**, so tests run offline
with no API key or network and assert real behavior (loop termination, tool
dispatch, error surfacing) rather than just that code ran.

### Continuous integration

A GitHub Actions pipeline runs on every push and pull request to `main`. Each run
installs the package, executes a flake8 lint pass, and runs the full pytest suite
across a build matrix of Python 3.10, 3.11, and 3.12. The build fails on any
failing test, syntax error, or undefined name, so the **CI badge** at the top of
this README always reflects the current state of `main`. The workflow is defined
in [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

### Adding a tool

1. Create a class in `src/tools/` that subclasses `BaseTool`.
2. Define `name`, `description`, `input_schema`, and an async `execute()`.
3. Register an instance in `CodingAgent._register_tools()` in `src/agent.py`.

## Roadmap

All phases are complete. Listed in the order they were built in this project:

- [x] **Phase 1 — ReAct loop & tool system:** the Reason–Act–Observe loop plus the `BaseTool` / `ToolRegistry` contract and name→tool dispatch
- [x] **Phase 2 — File operations:** read and write files (`read_file`, `write_file`)
- [x] **Phase 3 — Snapshots & rollback:** file snapshots taken before destructive operations, with restore by id
- [x] **Phase 4 — Sandboxed code execution:** AST-based static validation plus a subprocess sandbox with a timeout and per-platform resource limits
- [x] **Phase 5 — Code search:** grep-style content search across the working directory
- [x] **Phase 6 — Test suite:** pytest coverage for the executor, tools, and the agent loop, with the LLM mocked so tests run offline
- [x] **Phase 7 — Confirmation gate:** default-deny confirmation prompts for destructive operations
- [x] **Phase 8 — Git integration:** status / diff / commit as separate, single-purpose agent tools
- [x] **Phase 9 — Context management:** LLM summarization of older turns past a length threshold, keeping recent turns verbatim
- [x] **Phase 10 — Multi-file refactoring:** composing search + read + write to rename a symbol everywhere it's used
- [x] **Phase 11 — Container isolation:** Docker-based code execution (no network, enforced memory cap) with graceful fallback to the subprocess sandbox

Possible future directions are noted in **Known Limitations**.

## Notable engineering problems solved

A few of the more interesting things this project surfaced:

- **ReAct loop state bug.** The agent initially re-executed tools multiple times
  for a single request. Tracing the actual per-turn message list showed the loop
  was *rebuilding* the conversation each iteration instead of *accumulating* it,
  so the model couldn't see its own prior tool calls. Fixed by maintaining one
  growing message list.
- **Cross-platform resource limits.** Discovered by testing (not docs) that
  `RLIMIT_AS` is honored on Linux but rejected on macOS, and that the CPU cap
  fires with different kill signals per platform (`SIGKILL` vs `SIGXCPU`). Limits
  the OS rejects are now skipped defensively instead of crashing execution.

## Acknowledgments

- Inspired by Claude Code, OpenAI Codex CLI, and similar coding agents.
- Built on Anthropic's Claude API.