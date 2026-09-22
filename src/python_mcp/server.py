"""MCP Server initialization, configuration, and CLI entry point."""

import argparse
import os
from pathlib import Path
import sys
from typing import Sequence

from mcp.server.mcpserver import MCPServer

from python_mcp.security import SecurityManager
from python_mcp.tools import register_tools
from python_mcp.prompts import register_prompts
from python_mcp.resources import register_resources


def create_server(
    allowed_directories: Sequence[str | Path] | None = None,
    base_dir: str | Path | None = None,
    server_name: str = "prompt-file-manager",
) -> MCPServer:
    """Create and configure the file manipulation MCP server.

    Args:
        allowed_directories: Permitted directory boundaries for operations.
            Defaults to current working directory if None. Use ["*"] for unrestricted.
        base_dir: Base directory for relative path resolution.
        server_name: MCP server identifier.

    Returns:
        Configured MCPServer instance.
    """
    security = SecurityManager(
        allowed_directories=allowed_directories,
        base_dir=base_dir,
    )

    server = MCPServer(
        name=server_name,
        version="0.1.0",
        instructions=(
            "This server provides tools, prompts, and resources to inspect, create, edit, "
            "search, and organize files and directories safely on the host system."
        ),
    )

    # Register capabilities
    register_tools(server, security)
    register_prompts(server, security)
    register_resources(server, security)

    return server


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Prompt-driven System File Manipulation MCP Server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--allowed-dirs",
        type=str,
        default=os.getenv("MCP_ALLOWED_DIRS", "."),
        help="Comma-separated list of allowed directories, or '*' for unrestricted access.",
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default=None,
        help="Base working directory to resolve relative paths against.",
    )
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="MCP transport mechanism to use.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind for SSE / HTTP transport.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind for SSE / HTTP transport.",
    )

    return parser.parse_args()


def main() -> None:
    """CLI entry point for running the server."""
    args = parse_args()

    # Parse allowed directories
    if args.allowed_dirs.strip() == "*":
        allowed_dirs = ["*"]
    else:
        allowed_dirs = [d.strip() for d in args.allowed_dirs.split(",") if d.strip()]

    server = create_server(
        allowed_directories=allowed_dirs,
        base_dir=args.base_dir,
    )

    if args.transport == "stdio":
        # Stdio transport: ensure stderr is used for logging so stdout remains clean JSON-RPC
        server.run(transport="stdio")
    elif args.transport == "sse":
        server.run(transport="sse", host=args.host, port=args.port)
    elif args.transport == "streamable-http":
        server.run(transport="streamable-http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
