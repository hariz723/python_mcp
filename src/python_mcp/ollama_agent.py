"""Ollama-powered agent for manipulating system files via natural language prompts."""

import json
import logging
from collections.abc import Callable
from typing import Any

import ollama
from rich.console import Console

from python_mcp import operations
from python_mcp.security import SecurityManager

logger = logging.getLogger(__name__)
console = Console()

SYSTEM_PROMPT = """You are an autonomous AI system file manipulation assistant powered by local Ollama (`gpt-oss:latest`).
You have direct access to system tools to inspect, create, edit, search, organize, and delete files on the host system.

Core Guidelines:
1. Always use the available tools to inspect and execute real file system operations. Do not merely describe what you would do—call the tools to perform the actions.
2. Inspect before editing: Call `read_file` or `list_directory` before attempting modifications.
3. Be surgical with edits: When modifying existing files, prefer `edit_file` with exact text snippets to minimize unintended changes.
4. Verify your work: After writing, moving, or editing files, confirm the changes took effect.
5. Provide a clear, concise summary of the actions you performed when you are done.
"""


class OllamaFileAgent:
    """Agent that orchestrates system file manipulation using Ollama and local tools."""

    def __init__(
        self,
        model: str = "gpt-oss:latest",
        host: str = "http://localhost:11434",
        security_manager: SecurityManager | None = None,
        verbose: bool = True,
    ):
        """Initialize the Ollama file manipulation agent.

        Args:
            model: Ollama model identifier (default: 'gpt-oss:latest').
            host: Ollama server URL.
            security_manager: Path security manager for sandboxing.
            verbose: If True, prints tool execution progress to console.
        """
        self.model = model
        self.host = host
        self.security = security_manager or SecurityManager(allowed_directories=["*"])
        self.verbose = verbose
        self.client = ollama.Client(host=host)

        # Internal conversation memory
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        # Register tools
        self._init_tools()

    def _init_tools(self) -> None:
        """Create tool functions bound to this agent and security manager."""
        sec = self.security

        def read_file(path: str, offset_line: int = 1, limit_lines: int | None = None) -> str:
            """Read content of a text file with optional line-level slicing.

            Args:
                path: Path to the target file.
                offset_line: Starting 1-indexed line number.
                limit_lines: Maximum number of lines to read.
            """
            try:
                resolved = sec.validate_path(path, must_exist=True, must_be_file=True)
                res = operations.read_file(resolved, offset_line=offset_line, limit_lines=limit_lines)
                return json.dumps({"success": True, **res})
            except Exception as e:
                return json.dumps({"success": False, "path": path, "error": str(e)})

        def read_multiple_files(paths: list[str]) -> str:
            """Read the contents of multiple files in a single turn.

            Args:
                paths: List of file paths to read.
            """
            results = []
            for p in paths:
                try:
                    resolved = sec.validate_path(p, must_exist=True, must_be_file=True)
                    results.append(operations.read_file(resolved))
                except Exception as e:
                    results.append({"path": p, "error": str(e)})
            return json.dumps({"success": True, "files": results})

        def write_file(path: str, content: str, overwrite: bool = True) -> str:
            """Create a new file or overwrite an existing file. Automatically creates parent directories.

            Args:
                path: Target file path.
                content: Text content to write into the file.
                overwrite: If True, overwrites existing file.
            """
            try:
                resolved = sec.resolve_path(path)
                res = operations.write_file(resolved, content, overwrite=overwrite, make_parents=True)
                return json.dumps({"success": True, **res})
            except Exception as e:
                return json.dumps({"success": False, "path": path, "error": str(e)})

        def append_file(path: str, content: str) -> str:
            """Append text to an existing file, creating it if it does not exist.

            Args:
                path: Target file path.
                content: Text content to append.
            """
            try:
                resolved = sec.resolve_path(path)
                res = operations.append_file(resolved, content)
                return json.dumps({"success": True, **res})
            except Exception as e:
                return json.dumps({"success": False, "path": path, "error": str(e)})

        def edit_file(
            path: str,
            target_snippet: str,
            replacement_snippet: str,
            allow_multiple: bool = False,
        ) -> str:
            """Perform exact targeted text replacement in an existing file.

            Args:
                path: Path to the file to edit.
                target_snippet: The exact string to find and replace (including whitespace).
                replacement_snippet: The replacement text.
                allow_multiple: If True, replaces all occurrences.
            """
            try:
                resolved = sec.validate_path(path, must_exist=True, must_be_file=True)
                res = operations.edit_file(
                    resolved,
                    target_snippet=target_snippet,
                    replacement_snippet=replacement_snippet,
                    allow_multiple=allow_multiple,
                )
                return json.dumps({"success": True, **res})
            except Exception as e:
                return json.dumps({"success": False, "path": path, "error": str(e)})

        def create_directory(path: str) -> str:
            """Create a directory and any missing parent directories.

            Args:
                path: Directory path to create.
            """
            try:
                resolved = sec.resolve_path(path)
                res = operations.create_directory(resolved)
                return json.dumps({"success": True, **res})
            except Exception as e:
                return json.dumps({"success": False, "path": path, "error": str(e)})

        def list_directory(
            path: str = ".",
            recursive: bool = False,
            max_depth: int = 2,
            include_hidden: bool = False,
        ) -> str:
            """List files and folders in a given directory with sizes and modified dates.

            Args:
                path: Directory path to list.
                recursive: If True, recursively list subdirectories up to max_depth.
                max_depth: Maximum recursion depth (1 = top level only).
                include_hidden: Whether to include dotfiles.
            """
            try:
                resolved = sec.validate_path(path, must_exist=True, must_be_dir=True)
                res = operations.list_directory(
                    resolved,
                    recursive=recursive,
                    max_depth=max_depth,
                    include_hidden=include_hidden,
                )
                return json.dumps({"success": True, **res})
            except Exception as e:
                return json.dumps({"success": False, "path": path, "error": str(e)})

        def move_file(source: str, destination: str, overwrite: bool = False) -> str:
            """Move or rename a file or directory.

            Args:
                source: Path of the source file or directory.
                destination: Path of the target destination.
                overwrite: If True, replaces existing destination.
            """
            try:
                src_path = sec.validate_path(source, must_exist=True)
                dst_path = sec.resolve_path(destination)
                res = operations.move_path(src_path, dst_path, overwrite=overwrite)
                return json.dumps({"success": True, **res})
            except Exception as e:
                return json.dumps({"success": False, "source": source, "destination": destination, "error": str(e)})

        def copy_file(source: str, destination: str, overwrite: bool = False) -> str:
            """Copy a file or directory tree.

            Args:
                source: Source file or directory.
                destination: Destination path.
                overwrite: If True, overwrite target.
            """
            try:
                src_path = sec.validate_path(source, must_exist=True)
                dst_path = sec.resolve_path(destination)
                res = operations.copy_path(src_path, dst_path, overwrite=overwrite)
                return json.dumps({"success": True, **res})
            except Exception as e:
                return json.dumps({"success": False, "source": source, "destination": destination, "error": str(e)})

        def delete_file(path: str, recursive: bool = False) -> str:
            """Delete a file or directory. For non-empty directories, set recursive=True.

            Args:
                path: Target path to delete.
                recursive: Set to True to delete non-empty directory trees.
            """
            try:
                resolved = sec.validate_path(path, must_exist=True)
                res = operations.delete_path(resolved, recursive=recursive)
                return json.dumps({"success": True, **res})
            except Exception as e:
                return json.dumps({"success": False, "path": path, "error": str(e)})

        def get_file_info(path: str) -> str:
            """Get detailed file metadata, size, line count, permissions, and timestamps.

            Args:
                path: Path of the file or directory.
            """
            try:
                resolved = sec.validate_path(path, must_exist=True)
                res = operations.get_metadata(resolved)
                return json.dumps({"success": True, **res})
            except Exception as e:
                return json.dumps({"success": False, "path": path, "error": str(e)})

        def search_files(
            directory: str = ".",
            pattern: str = "*",
            recursive: bool = True,
            include_hidden: bool = False,
        ) -> str:
            """Search for files and directories matching a glob pattern.

            Args:
                directory: Directory to search inside.
                pattern: Glob pattern (e.g. '*.py', '**/*.json', 'test_*').
                recursive: If True, searches recursively.
                include_hidden: Whether to include hidden files.
            """
            try:
                resolved = sec.validate_path(directory, must_exist=True, must_be_dir=True)
                res = operations.search_files(
                    resolved,
                    pattern=pattern,
                    recursive=recursive,
                    include_hidden=include_hidden,
                )
                return json.dumps({"success": True, "count": len(res), "matches": res})
            except Exception as e:
                return json.dumps({"success": False, "directory": directory, "error": str(e)})

        def search_file_content(
            directory: str = ".",
            query: str = "",
            case_sensitive: bool = False,
            file_pattern: str = "*",
            max_results: int = 50,
        ) -> str:
            """Search for text within files across a directory (grep-style).

            Args:
                directory: Directory to search within.
                query: String to search for.
                case_sensitive: Whether match should be case sensitive.
                file_pattern: File name glob pattern to filter.
                max_results: Maximum number of match lines to return.
            """
            try:
                resolved = sec.validate_path(directory, must_exist=True, must_be_dir=True)
                res = operations.search_file_content(
                    resolved,
                    query=query,
                    case_sensitive=case_sensitive,
                    file_pattern=file_pattern,
                    max_results=max_results,
                )
                return json.dumps({"success": True, "count": len(res), "matches": res})
            except Exception as e:
                return json.dumps({"success": False, "directory": directory, "error": str(e)})

        self.tools_map: dict[str, Callable[..., str]] = {
            "read_file": read_file,
            "read_multiple_files": read_multiple_files,
            "write_file": write_file,
            "append_file": append_file,
            "edit_file": edit_file,
            "create_directory": create_directory,
            "list_directory": list_directory,
            "move_file": move_file,
            "copy_file": copy_file,
            "delete_file": delete_file,
            "get_file_info": get_file_info,
            "search_files": search_files,
            "search_file_content": search_file_content,
        }

        self.tools_list = list(self.tools_map.values())

    def reset(self) -> None:
        """Clear conversation memory, resetting back to initial system prompt."""
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def chat(self, user_prompt: str, max_turns: int = 15) -> str:
        """Process a user prompt, executing any requested tool calls until complete.

        Args:
            user_prompt: Natural language instruction (e.g. 'Organize downloads folder').
            max_turns: Maximum tool-execution iterations to prevent infinite loops.

        Returns:
            Final string answer from the model.
        """
        self.messages.append({"role": "user", "content": user_prompt})

        turn = 0
        while turn < max_turns:
            turn += 1

            try:
                response = self.client.chat(
                    model=self.model,
                    messages=self.messages,
                    tools=self.tools_list,
                )
            except Exception as e:
                err_msg = f"Error communicating with Ollama ({self.host}): {e}"
                if self.verbose:
                    console.print(f"[bold red]{err_msg}[/bold red]")
                return err_msg

            msg = response.message
            tool_calls = getattr(msg, "tool_calls", None) or []

            # Add assistant message to history
            self.messages.append(msg)

            # If no tool calls, model provided final answer
            if not tool_calls:
                final_content = msg.content or ""
                return final_content

            # Execute tool calls
            for tc in tool_calls:
                fn_name = tc.function.name
                fn_args = tc.function.arguments or {}

                if self.verbose:
                    args_repr = ", ".join(f"{k}={v!r}" for k, v in fn_args.items())
                    console.print(f"[bold cyan]🔧 Tool Call:[/bold cyan] [green]{fn_name}[/green]({args_repr})")

                tool_fn = self.tools_map.get(fn_name)
                if tool_fn is not None:
                    try:
                        result_str = tool_fn(**fn_args)
                    except Exception as e:
                        result_str = json.dumps({"success": False, "error": str(e)})
                else:
                    result_str = json.dumps({"success": False, "error": f"Tool '{fn_name}' not found"})

                if self.verbose:
                    try:
                        parsed = json.loads(result_str)
                        if parsed.get("success"):
                            console.print("   [dim green]✔ Completed[/dim green]")
                        else:
                            console.print(f"   [dim red]✘ Failed: {parsed.get('error')}[/dim red]")
                    except Exception:
                        console.print("   [dim green]✔ Done[/dim green]")

                # Feed tool result back to the conversation
                self.messages.append({
                    "role": "tool",
                    "content": result_str,
                })

        return "Reached maximum turn limit without final response."
