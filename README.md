# Terminal-Based Coding Agent

A sophisticated terminal-based coding agent that accepts natural language instructions, interprets them into structured code generation or execution commands, and manages an interactive development workflow.

## Features

- **Natural Language Interface**: Communicate with the agent using plain English
- **Multi-Turn Conversations**: Agent remembers context and previous actions
- **Safe Code Execution**: Sandboxed environment with AST validation and resource limits
- **File Management**: Create, edit, and version code files with rollback capability
- **Interactive Workflow**: Review changes before they're applied
- **Real-Time Feedback**: See the agent's reasoning and execution steps

## Architecture

The agent follows the ReAct (Reason-Act-Observe) pattern:

```
User Input → Agent Reasoning → Tool Execution → Observation → Response
```

### Core Components

1. **CLI Interface**: Rich terminal UI for user interaction
2. **Agent Orchestrator**: Central coordination hub implementing the ReAct loop
3. **LLM Provider**: Claude API integration for natural language understanding
4. **Tool Registry**: Extensible system for file operations, code execution, and search
5. **Execution Environment**: Sandboxed code execution with security layers
6. **File System Management**: Version control with snapshots and rollback

## Installation

### Prerequisites

- Python 3.10 or higher
- Anthropic API key
- (Optional) E2B API key for cloud sandboxing

### Setup

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/terminal-coding-agent.git
cd terminal-coding-agent
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

5. Install the package in development mode:
```bash
pip install -e .
```

## Usage

### Start the Agent

```bash
python -m src.cli
```

### Example Commands

```
You: Create a Python function for quicksort in sorts.py

You: Open utils.py and add logging to all functions

You: Modify the last function to handle empty lists

You: Run the tests in test_main.py

You: Show me what files have been changed

You: Rollback to the previous version
```

### CLI Commands

- `/help` - Show available commands
- `/history` - View conversation history
- `/rollback` - Revert to a previous snapshot
- `/clear` - Clear conversation history
- `/exit` or `/quit` - Exit the agent

## Configuration

Edit `config.yaml` to customize:

- Model selection
- Token limits
- Sandbox settings
- Tool availability
- Safety settings

## Development

### Project Structure

```
coding-agent/
├── src/
│   ├── agent.py              # Core agent orchestrator
│   ├── cli.py                # Terminal interface
│   ├── llm_provider.py       # Claude API wrapper
│   ├── config.py             # Configuration loader
│   ├── tools/                # Tool implementations
│   ├── execution/            # Sandboxed execution
│   └── utils/                # Utilities
├── tests/                    # Unit tests
├── config.yaml              # Configuration
└── requirements.txt         # Dependencies
```

### Running Tests

```bash
pytest tests/
```

### Adding New Tools

1. Create a new tool in `src/tools/`
2. Inherit from `BaseTool`
3. Implement `execute()` method
4. Register in `src/tools/__init__.py`

## Safety & Security

### Code Validation

- AST parsing to detect dangerous patterns
- Blocks dangerous imports (os, subprocess, socket)
- Prevents file system access outside working directory

### Execution Limits

- CPU time: 5 seconds max
- Memory: 100MB limit
- Single process only
- No network access

### Version Control

- Automatic snapshots before destructive operations
- Easy rollback to previous states
- Full audit trail of changes

## Roadmap

- [ ] Phase 1: Basic file operations and ReAct loop
- [ ] Phase 2: Safe code execution with sandboxing
- [ ] Phase 3: Advanced context management for large codebases
- [ ] Phase 4: Git integration
- [ ] Phase 5: Multi-file refactoring
- [ ] Phase 6: Test generation and execution

## Demo Video

[Link to YouTube demo with captions enabled]

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.
## License

MIT License - see LICENSE file for details

## Acknowledgments

- Inspired by Claude Code, OpenAI Codex CLI, and other coding agents
- Built with Anthropic's Claude API
- Thanks to the E2B team for sandboxing infrastructure

## Contact

Colin J. Emmanuel - c.j.emmanuel@columbia.edu

Project Link: https://github.com/Colin-J-Emmanuel/terminal-coding-agent