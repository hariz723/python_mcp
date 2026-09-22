# Prompt-Driven System File Manipulation MCP Server

An MCP (Model Context Protocol) server implemented in Python that enables Large Language Models (Claude, Antigravity, Cursor, etc.) to inspect, manipulate, edit, search, and organize files and directories on your system driven by prompts and structured tools.

Built on the official `mcp` 2.x SDK with sandboxed path security and pre-configured prompt workflows.

---

## Architecture Overview

```
User Prompt (e.g. "Organize my downloads" or "Refactor auth in app.py")
                          │
                          ▼
              ┌───────────────────────┐
              │  LLM (Claude / AGY)   │
              └──────────┬────────────┘
                         │ JSON-RPC (stdio / SSE)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 prompt-file-manager Server                  │
│                                                             │
│  ┌─────────────────┐ ┌──────────────────┐ ┌──────────────┐  │
│  │   MCP Prompts   │ │    MCP Tools     │ │MCP Resources │  │
│  │organize_dir     │ │read_file         │ │file://{path} │  │
│  │refactor_file    │ │write_file        │ │dir://{path}  │  │
│  │find_and_replace │ │edit_file         │ │system://...  │  │
│  │scaffold_project │ │list_directory    │ └──────────────┘  │
│  │clean_directory  │ │search_files      │                   │
│  │batch_rename     │ │delete/move/copy  │                   │
│  └─────────────────┘ └─────────┬────────┘                   │
│                                │                            │
│                 ┌──────────────▼──────────────┐             │
│                 │   SecurityManager Sandbox   │             │
│                 └──────────────┬──────────────┘             │
└────────────────────────────────┼────────────────────────────┘
                                 ▼
                     Local File System
```

---

## Key Features

### 1. File Manipulation Tools (`@server.tool`)
- **`read_file`**: Read file content with optional line-level windowing (`offset_line`, `limit_lines`) for handling large files safely.
- **`read_multiple_files`**: Read multiple files in a single turn.
- **`write_file`**: Create a new file or overwrite an existing file (automatically creating parent directories).
- **`append_file`**: Append text to an existing file or create it if missing.
- **`edit_file`**: Surgical target-and-replace text editing (exact snippet replacement, preventing unintended changes).
- **`create_directory`**: Create directory hierarchies recursively.
- **`list_directory`**: List directory entries with file size, modified timestamps, and optional recursion depth.
- **`move_file`**: Move or rename files and directories.
- **`copy_file`**: Copy individual files or recursive directory trees.
- **`delete_file`**: Delete a file or directory (with recursive safety checks).
- **`get_file_info`**: Inspect file metadata, MIME type, size, line count, permissions, and timestamps.
- **`search_files`**: Fast glob searching for files and folders across directory trees.
- **`search_file_content`**: Grep-style text search inside files with line numbers and matched snippets.

### 2. Prompt Templates (`@server.prompt`)
These predefined interactive prompt templates steer the LLM through complex multi-step file manipulation workflows:
- **`organize_directory`**: Instructs the LLM to analyze files in a folder, create categories, and systematically move files into organized folders.
- **`refactor_file`**: Prompts the LLM to inspect code, plan edits, and use `edit_file` or `write_file` to execute refactorings cleanly.
- **`find_and_replace`**: Guides the LLM to search for occurrences across files, verify matches, and substitute text consistently.
- **`scaffold_project`**: Instructs the LLM to build directory structures and starter boilerplate files for a new project.
- **`clean_directory`**: Guides the LLM to scan for cache, log, and temporary files and safely delete them.
- **`batch_rename`**: Guides the LLM to scan matching files and rename them according to a desired naming convention.

### 3. Resources (`@server.resource`)
- `file://{path}`: Read raw file content directly as an MCP resource.
- `dir://{path}`: Read formatted directory hierarchy as a JSON resource.
- `system://file-server/status`: Read server configuration, working directory, and sandbox limits.

### 4. Sandboxing & Security
The server contains a `SecurityManager` that enforces directory boundaries:
- Specify one or more `--allowed-dirs` to confine operations to specific folders.
- Prevents path traversal vulnerabilities (`../../etc/passwd`).
- Can be set to `--allowed-dirs "*"` for full system access when desired.

---

## Quick Start

### Requirements
- Python 3.10+ (tested on Python 3.13)
- [`uv`](https://docs.astral.sh/uv/) (recommended) or standard `pip`

### 1. Installation

Clone and install dependencies with `uv`:
```bash
cd /home/hari/projects/python_mcp
uv sync
```

Or install using `pip`:
```bash
pip install -e .
```

### 2. Running Tests
Run the full test suite with `pytest`:
```bash
uv run pytest -v
```

### 3. Running the Server

#### Stdio Mode (Default for Claude Desktop & Antigravity)
Confine to current project directory:
```bash
uv run python main.py --allowed-dirs .
```

Confine to multiple specific directories:
```bash
uv run python main.py --allowed-dirs /home/hari/projects,/home/hari/Documents
```

Unrestricted system-wide access:
```bash
uv run python main.py --allowed-dirs "*"
```

#### SSE Mode (For network/remote connections)
```bash
uv run python main.py --transport sse --host 127.0.0.1 --port 8000
```

---

## Client Configurations

### 1. Claude Desktop (`claude_desktop_config.json`)
Add this entry to your `~/.config/Claude/claude_desktop_config.json` (Linux) or `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

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
        "--allowed-dirs",
        "/home/hari/projects"
      ]
    }
  }
}
```

### 2. Antigravity / Cursor Configuration
In your project or user settings (`.antigravity/mcp.json` or cursor settings):

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
        "--allowed-dirs",
        "."
      ]
    }
  }
}
```

### 3. Test Interactively with MCP Inspector
You can test all tools, prompts, and resources visually in your browser using the MCP Inspector:
```bash
uv run mcp dev main.py
```

---

## Example Prompts for the LLM

Once connected to your MCP client, you can use prompts like:

- **Organize a directory**:
  > *"Please use the `organize_directory` prompt on `~/Downloads` to organize files into Docs, Images, and Archives."*

- **Refactor code**:
  > *"Use the `refactor_file` prompt on `src/api.py` to add docstrings and type hints to all route handlers."*

- **Scaffold a new project**:
  > *"Use `scaffold_project` to create a new FastAPI service inside `~/projects/my_api` with routes, models, and tests."*

- **Find and Replace**:
  > *"Use `find_and_replace` in `src/` to rename `old_database_url` to `DATABASE_URL` across all Python files."*

---

## Project Structure

```
python_mcp/
├── main.py                  # Root entrypoint launcher
├── pyproject.toml           # Project packaging & dependencies (mcp 2.x, pytest)
├── README.md                # Documentation & configuration guide
├── src/
│   └── python_mcp/
│       ├── __init__.py      # Package export
│       ├── operations.py    # Native file system manipulation operations
│       ├── prompts.py       # MCP prompt templates
│       ├── resources.py     # MCP resource endpoints
│       ├── security.py      # Path resolution & boundary security
│       ├── server.py        # MCPServer factory & CLI argument parser
│       └── tools.py         # MCP tool definitions
└── tests/
    ├── test_operations.py   # Tests for core file operations
    ├── test_prompts.py      # Tests for MCP prompt templates
    ├── test_security.py     # Tests for sandboxing & path resolution
    └── test_server.py       # Integration tests for tools, prompts & resources
```
