# Prompt-Driven System File Manipulation (Ollama gpt-oss & MCP)

An autonomous system file manipulation application and MCP server in Python powered by local **Ollama (`gpt-oss:latest`)**.

It enables you to inspect, create, edit, search, organize, and delete files on your system simply by typing natural language prompts into your terminal, while also supporting standard Model Context Protocol (MCP) clients like Claude Desktop, Cursor, and Antigravity.

---

## Architecture Overview

```
User Prompt (e.g. "Organize my downloads" or "Create a FastAPI starter in ./api")
                                │
                                ▼
         ┌──────────────────────────────────────────────┐
         │     Ollama LLM Agent (gpt-oss:latest)        │
         │          (Local @ localhost:11434)           │
         └──────────────────────┬───────────────────────┘
                                │ Function / Tool Calling
                                ▼
         ┌──────────────────────────────────────────────┐
         │      System File Manipulation Engine         │
         │                                              │
         │  • read_file          • create_directory     │
         │  • write_file         • move_file            │
         │  • edit_file          • copy_file            │
         │  • append_file        • delete_file          │
         │  • list_directory     • search_files         │
         │  • get_file_info      • search_file_content  │
         └──────────────────────┬───────────────────────┘
                                │
                 ┌──────────────▼──────────────┐
                 │   SecurityManager Sandbox   │
                 └──────────────┬──────────────┘
                                ▼
                        Host File System
```

---

## Key Features

1. **Local Ollama Integration (`gpt-oss:latest`)**:
   - Zero external API costs, 100% private, runs entirely on your local machine.
   - Native multi-turn function/tool calling loop.
   - Visual feedback of tool execution using Rich terminal panels.

2. **Complete File Manipulation Capabilities**:
   - `read_file`: Line-windowed reading for safe inspection of large files.
   - `read_multiple_files`: Batch reading of multiple files in one turn.
   - `write_file`: Create or overwrite files (auto-creates parent directories).
   - `append_file`: Append text to existing or new files.
   - `edit_file`: Surgical target-and-replace text editing (exact matching).
   - `create_directory`: Recursive directory creation.
   - `list_directory`: Inspection with sizes, file types, and timestamps.
   - `move_file` / `copy_file`: Move, rename, or copy files and folder trees.
   - `delete_file`: Safe deletion of files and directory trees.
   - `get_file_info`: Metadata, MIME type, permissions, and line counts.
   - `search_files`: Glob searching across directory trees.
   - `search_file_content`: Grep-style text search inside files.

3. **Dual Execution Modes**:
   - **Ollama CLI & Interactive REPL**: Run prompts directly from your terminal.
   - **MCP Server Mode (`--serve-mcp`)**: Connect to Claude Desktop, Cursor, or Antigravity via stdio.

4. **Security & Sandboxing**:
   - Sandboxing to configurable directory boundaries (`--allowed-dirs`).
   - Traversal protection (`../../etc/passwd`).
   - Specify `--allowed-dirs "*"` for full system access.

---

## Quick Start

### Prerequisites
1. Ensure Ollama is running and `gpt-oss:latest` is pulled:
   ```bash
   ollama pull gpt-oss:latest
   ollama serve
   ```
2. Python 3.10+ (tested on Python 3.13) with `uv` or `pip`.

### 1. Installation
```bash
cd /home/hari/projects/python_mcp
uv sync
```

### 2. Run Single Prompts Directly
Execute file manipulation prompts directly from the CLI:

```bash
# Create a new project structure
uv run python main.py "Create a folder called 'my_service' with app.py and a README.md"

# Inspect and organize a folder
uv run python main.py "List the files in ./src and report their sizes"

# Find and replace text across files
uv run python main.py "Search for all occurrences of 'DEBUG = True' in . and replace with 'DEBUG = False'"
```

### 3. Interactive REPL Mode
Launch the interactive terminal shell:

```bash
uv run python main.py
```

Inside the interactive shell:
```
🚀 Ollama File Manipulation Agent
Model: gpt-oss:latest (Ollama @ http://localhost:11434)
Working Directory: /home/hari/projects/python_mcp
Allowed Directories: .

ollama-files> List all files in the current folder with their sizes
🔧 Tool Call: list_directory(include_hidden=False, max_depth=1, path='.', recursive=False)
   ✔ Completed
...

ollama-files> /help        # View help and example prompts
ollama-files> /tools       # View all 13 file manipulation tools
ollama-files> /status      # Check current model & sandbox config
ollama-files> /clear       # Reset conversation memory
ollama-files> /model <id>  # Switch Ollama model
ollama-files> /exit        # Exit
```

---

## Command-Line Options

| Option | Default | Description |
|---|---|---|
| `prompt` | `None` | Positional prompt. If omitted, starts interactive REPL. |
| `--model` | `gpt-oss:latest` | Ollama model name (or set `OLLAMA_MODEL` env var). |
| `--ollama-host` | `http://localhost:11434` | Ollama API endpoint (or set `OLLAMA_HOST` env var). |
| `--allowed-dirs` | `.` | Permitted directories (comma-separated, or `*` for unrestricted). |
| `--serve-mcp` | `False` | Run in standard MCP server mode (for Claude / Cursor / Antigravity). |
| `--transport` | `stdio` | MCP transport (`stdio`, `sse`, `streamable-http`). |

---

## MCP Server Integration (Claude Desktop / Antigravity)

To use this as an MCP server with external clients, pass `--serve-mcp`:

### Claude Desktop Configuration (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "file-manager": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/hari/projects/python_mcp",
        "run",
        "python",
        "main.py",
        "--serve-mcp",
        "--allowed-dirs",
        "."
      ]
    }
  }
}
```

---

## Running the Automated Test Suite

```bash
uv run pytest -v
```
*(All 15 tests for agent tool calling, file operations, security, and MCP protocol pass)*
