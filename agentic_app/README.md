# SambaNova Agentic App

An agentic application powered by SambaNova LLM with tools, memory, and web interface.

## Features

- **SambaNova Integration** - Connects to SambaNova Cloud API
- **Tool Use** - Multiple built-in tools for file operations, web search, code execution, and more
- **Memory System** - In-memory and persistent storage for conversation history and long-term facts
- **Web Interface** - Streamlit-based UI for easy interaction

## Prerequisites

- Python 3.9+
- SambaNova API key

## Setup

### 1. Clone or Navigate to the Project

```bash
cd /Users/bowenl/work/test-codex/agentic_app
```

### 2. Create and Activate Conda Environment

```bash
# Create the environment from YAML
conda env create -f environment.yml

# Activate the environment
conda activate sambanova-agent
```

### 3. Set Your API Key

```bash
# Set the environment variable (replace with your actual key)
export OPENAI_API_KEY_CODEX="your-sambanova-api-key"

# Or add to your shell profile for persistence
echo 'export OPENAI_API_KEY_CODEX="your-key"' >> ~/.zshrc
source ~/.zshrc
```

### 4. Verify Installation

```bash
# Test CLI help
python -m src.agent --help

# List available tools
python -m src.agent --list-tools
```

## Usage

### CLI Mode

Run a task:
```bash
python -m src.agent "Write a hello world function in Python"
```

List available tools:
```bash
python -m src.agent --list-tools
```

List conversations:
```bash
python -m src.agent --list-conversations
```

Start new conversation:
```bash
python -m src.agent --new "My Conversation"
```

### Web Interface

Start the Streamlit app:
```bash
streamlit run streamlit/app.py
```

Then open http://localhost:8501 in your browser.

## Available Tools

| Tool | Description |
|------|-------------|
| read_file | Read the contents of a file |
| write_file | Write content to a file |
| list_directory | List files in a directory |
| execute_code | Execute Python code |
| run_command | Run a shell command |
| web_search | Search the web |
| get_weather | Get weather for a location |
| calculator | Perform math calculations |

## Memory System

The app supports:
- **In-memory storage** - Quick access to recent messages
- **Persistent storage** - JSON-based storage in ~/.codex/agent_memory/
- **Facts** - Long-term memory with key-value pairs
- **Multi-conversation** - Multiple conversation threads

## Configuration

The app uses your existing Codex configuration:
- API key from `OPENAI_API_KEY_CODEX` environment variable
- Default model: `MiniMax-M2.5`
- Base URL: `https://api.sambanova.ai/v1`

## Troubleshooting

### API Key Not Found

Make sure the environment variable is set:
```bash
echo $OPENAI_API_KEY_CODEX
```

### Module Not Found

Ensure you're in the correct directory and the environment is activated:
```bash
cd /Users/bowenl/work/test-codex/agentic_app
conda activate sambanova-agent
```

### Streamlit Port Already in Use

Specify a different port:
```bash
streamlit run streamlit/app.py --server.port 8502
```
