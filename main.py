"""Convenience launcher for the file manipulation MCP server."""

import sys
from pathlib import Path

# Ensure src/ is in sys.path when run directly
sys.path.insert(0, str(Path(__file__).parent / "src"))

from python_mcp.server import main

if __name__ == "__main__":
    main()
