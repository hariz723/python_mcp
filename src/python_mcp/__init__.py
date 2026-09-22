"""Prompt-driven System File Manipulation MCP Server."""

from python_mcp.server import create_server, main
from python_mcp.security import SecurityManager, SecurityError

__version__ = "0.1.0"
__all__ = ["create_server", "main", "SecurityManager", "SecurityError"]
