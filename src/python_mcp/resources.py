"""MCP resource definitions for reading files and directory status."""

import json
import os
import platform
from mcp.server.mcpserver import MCPServer

from python_mcp.security import SecurityManager
from python_mcp import operations


def register_resources(server: MCPServer, security: SecurityManager) -> None:
    """Register MCP resources on the server.

    Args:
        server: Target MCPServer instance.
        security: SecurityManager instance.
    """

    @server.resource("file://{path}", description="Read content of a file as an MCP resource.")
    def file_resource(path: str) -> str:
        """Read text file content."""
        resolved = security.validate_path(path, must_exist=True, must_be_file=True)
        res = operations.read_file(resolved)
        return str(res.get("content", ""))

    @server.resource("dir://{path}", description="Read directory entries and structure.")
    def dir_resource(path: str) -> str:
        """Read directory listing as JSON."""
        resolved = security.validate_path(path, must_exist=True, must_be_dir=True)
        res = operations.list_directory(resolved, recursive=True, max_depth=2)
        return json.dumps(res, indent=2)

    @server.resource("system://file-server/status", description="Server configuration and status.")
    def status_resource() -> str:
        """Get server status and configuration."""
        info = {
            "server_name": server.name,
            "version": server.version or "0.1.0",
            "working_directory": str(security.base_dir),
            "allow_all": security.allow_all,
            "allowed_directories": [str(d) for d in security.allowed_directories],
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "python_version": platform.python_version(),
            },
            "pid": os.getpid(),
        }
        return json.dumps(info, indent=2)
