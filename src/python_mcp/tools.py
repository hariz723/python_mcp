"""MCP tool definitions for system file manipulation."""

import logging
from typing import Any

from mcp.server.mcpserver import MCPServer

from python_mcp import operations
from python_mcp.security import SecurityError, SecurityManager

logger = logging.getLogger(__name__)


def register_tools(server: MCPServer, security: SecurityManager) -> None:
    """Register all file manipulation tools on the MCPServer instance.

    Args:
        server: Target MCPServer instance.
        security: SecurityManager instance for path validation.
    """

    @server.tool(
        name="read_file",
        description=(
            "Read the contents of a text file. Supports line windowing with offset_line "
            "and limit_lines for viewing specific portions of large files."
        ),
    )
    def read_file_tool(
        path: str,
        offset_line: int = 1,
        limit_lines: int | None = None,
    ) -> dict[str, Any]:
        """Read text file content with line windowing."""
        try:
            resolved = security.validate_path(path, must_exist=True, must_be_file=True)
            logger.debug(f"Reading file: {resolved}")
            res = operations.read_file(resolved, offset_line=offset_line, limit_lines=limit_lines)
            return {"success": True, **res}
        except (SecurityError, FileNotFoundError, IsADirectoryError, Exception) as e:
            return {"success": False, "path": path, "error": str(e)}

    @server.tool(
        name="read_multiple_files",
        description="Read the contents of multiple files in a single operation.",
    )
    def read_multiple_files_tool(
        paths: list[str],
    ) -> dict[str, Any]:
        """Read multiple files at once."""
        results: list[dict[str, Any]] = []
        for p_str in paths:
            try:
                resolved = security.validate_path(p_str, must_exist=True, must_be_file=True)
                results.append(operations.read_file(resolved))
            except Exception as e:
                results.append({"path": p_str, "error": str(e)})

        return {"success": True, "files": results}

    @server.tool(
        name="write_file",
        description=(
            "Create a new file or overwrite an existing file with the provided content. "
            "Automatically creates parent directories if needed."
        ),
    )
    def write_file_tool(
        path: str,
        content: str,
        overwrite: bool = True,
    ) -> dict[str, Any]:
        """Write content to a file."""
        try:
            resolved = security.resolve_path(path)
            logger.debug(f"Writing file: {resolved}")
            res = operations.write_file(resolved, content, overwrite=overwrite, make_parents=True)
            return {"success": True, **res}
        except (SecurityError, FileExistsError, Exception) as e:
            return {"success": False, "path": path, "error": str(e)}

    @server.tool(
        name="append_file",
        description="Append text content to the end of a file. Creates file if missing.",
    )
    def append_file_tool(
        path: str,
        content: str,
    ) -> dict[str, Any]:
        """Append text content to a file."""
        try:
            resolved = security.resolve_path(path)
            logger.debug(f"Appending to file: {resolved}")
            res = operations.append_file(resolved, content)
            return {"success": True, **res}
        except (SecurityError, Exception) as e:
            return {"success": False, "path": path, "error": str(e)}

    @server.tool(
        name="edit_file",
        description=(
            "Targeted text replacement in an existing file. Replaces target_snippet with "
            "replacement_snippet. Requires exact match including whitespace."
        ),
    )
    def edit_file_tool(
        path: str,
        target_snippet: str,
        replacement_snippet: str,
        allow_multiple: bool = False,
    ) -> dict[str, Any]:
        """Perform exact text replacement in a file."""
        try:
            resolved = security.validate_path(path, must_exist=True, must_be_file=True)
            logger.debug(f"Editing file: {resolved}")
            res = operations.edit_file(
                resolved,
                target_snippet=target_snippet,
                replacement_snippet=replacement_snippet,
                allow_multiple=allow_multiple,
            )
            return {"success": True, **res}
        except (SecurityError, FileNotFoundError, ValueError, Exception) as e:
            return {"success": False, "path": path, "error": str(e)}

    @server.tool(
        name="create_directory",
        description="Create a directory and any missing parent directories.",
    )
    def create_directory_tool(
        path: str,
    ) -> dict[str, Any]:
        """Create directory recursively."""
        try:
            resolved = security.resolve_path(path)
            logger.debug(f"Creating directory: {resolved}")
            res = operations.create_directory(resolved)
            return {"success": True, **res}
        except (SecurityError, Exception) as e:
            return {"success": False, "path": path, "error": str(e)}

    @server.tool(
        name="list_directory",
        description=(
            "List files and directories in a given path. Supports recursive listing "
            "up to a specified depth."
        ),
    )
    def list_directory_tool(
        path: str = ".",
        recursive: bool = False,
        max_depth: int = 2,
        include_hidden: bool = False,
    ) -> dict[str, Any]:
        """List contents of a directory."""
        try:
            resolved = security.validate_path(path, must_exist=True, must_be_dir=True)
            logger.debug(f"Listing directory: {resolved}")
            res = operations.list_directory(
                resolved,
                recursive=recursive,
                max_depth=max_depth,
                include_hidden=include_hidden,
            )
            return {"success": True, **res}
        except (SecurityError, FileNotFoundError, NotADirectoryError, Exception) as e:
            return {"success": False, "path": path, "error": str(e)}

    @server.tool(
        name="move_file",
        description="Move or rename a file or directory to a new destination.",
    )
    def move_file_tool(
        source: str,
        destination: str,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Move or rename file/folder."""
        try:
            src_path = security.validate_path(source, must_exist=True)
            dst_path = security.resolve_path(destination)
            logger.debug(f"Moving {src_path} -> {dst_path}")
            res = operations.move_path(src_path, dst_path, overwrite=overwrite)
            return {"success": True, **res}
        except (SecurityError, FileNotFoundError, FileExistsError, Exception) as e:
            return {"success": False, "source": source, "destination": destination, "error": str(e)}

    @server.tool(
        name="copy_file",
        description="Copy a file or directory tree to a target destination.",
    )
    def copy_file_tool(
        source: str,
        destination: str,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Copy file or directory."""
        try:
            src_path = security.validate_path(source, must_exist=True)
            dst_path = security.resolve_path(destination)
            logger.debug(f"Copying {src_path} -> {dst_path}")
            res = operations.copy_path(src_path, dst_path, overwrite=overwrite)
            return {"success": True, **res}
        except (SecurityError, FileNotFoundError, FileExistsError, Exception) as e:
            return {"success": False, "source": source, "destination": destination, "error": str(e)}

    @server.tool(
        name="delete_file",
        description=(
            "Delete a file or directory. To delete a non-empty directory, "
            "set recursive=True."
        ),
    )
    def delete_file_tool(
        path: str,
        recursive: bool = False,
    ) -> dict[str, Any]:
        """Delete file or directory."""
        try:
            resolved = security.validate_path(path, must_exist=True)
            logger.debug(f"Deleting path: {resolved}")
            res = operations.delete_path(resolved, recursive=recursive)
            return {"success": True, **res}
        except (SecurityError, FileNotFoundError, ValueError, Exception) as e:
            return {"success": False, "path": path, "error": str(e)}

    @server.tool(
        name="get_file_info",
        description="Get detailed metadata, size, line count, permissions, and timestamps.",
    )
    def get_file_info_tool(
        path: str,
    ) -> dict[str, Any]:
        """Retrieve file metadata and statistics."""
        try:
            resolved = security.validate_path(path, must_exist=True)
            res = operations.get_metadata(resolved)
            return {"success": True, **res}
        except (SecurityError, FileNotFoundError, Exception) as e:
            return {"success": False, "path": path, "error": str(e)}

    @server.tool(
        name="search_files",
        description="Search for files and directories matching a glob pattern.",
    )
    def search_files_tool(
        directory: str = ".",
        pattern: str = "*",
        recursive: bool = True,
        include_hidden: bool = False,
    ) -> dict[str, Any]:
        """Search filenames by glob pattern."""
        try:
            resolved = security.validate_path(directory, must_exist=True, must_be_dir=True)
            logger.debug(f"Searching {resolved} for pattern '{pattern}'")
            results = operations.search_files(
                resolved, pattern=pattern, recursive=recursive, include_hidden=include_hidden
            )
            return {"success": True, "count": len(results), "matches": results}
        except (SecurityError, FileNotFoundError, NotADirectoryError, Exception) as e:
            return {"success": False, "directory": directory, "error": str(e)}

    @server.tool(
        name="search_file_content",
        description="Search for text or regex pattern inside files across a directory (grep-like).",
    )
    def search_file_content_tool(
        directory: str = ".",
        query: str = "",
        case_sensitive: bool = False,
        file_pattern: str = "*",
        max_results: int = 100,
    ) -> dict[str, Any]:
        """Search file contents for text."""
        try:
            resolved = security.validate_path(directory, must_exist=True, must_be_dir=True)
            logger.debug(f"Searching content in {resolved} for '{query}'")
            results = operations.search_file_content(
                resolved,
                query=query,
                case_sensitive=case_sensitive,
                file_pattern=file_pattern,
                max_results=max_results,
            )
            return {"success": True, "count": len(results), "matches": results}
        except (SecurityError, FileNotFoundError, NotADirectoryError, Exception) as e:
            return {"success": False, "directory": directory, "error": str(e)}
