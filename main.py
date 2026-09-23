"""Convenience launcher for the Ollama-powered system file manipulation application."""

import sys
from pathlib import Path

# Ensure src/ is in sys.path when run directly
sys.path.insert(0, str(Path(__file__).parent / "src"))

from python_mcp.cli import main

if __name__ == "__main__":
    main()
