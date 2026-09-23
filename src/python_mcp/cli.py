"""Interactive CLI and prompt runner for Ollama system file manipulation."""

import argparse
import os
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from python_mcp import server as mcp_server_module
from python_mcp.ollama_agent import OllamaFileAgent
from python_mcp.security import SecurityManager

console = Console()


def print_welcome_banner(model: str, host: str, allowed_dirs: list[str]) -> None:
    """Display the application welcome banner."""
    dirs_str = "Unrestricted (*)" if allowed_dirs == ["*"] else ", ".join(allowed_dirs)
    body = (
        f"[bold]Model:[/bold] [cyan]{model}[/cyan] (Ollama @ {host})\n"
        f"[bold]Working Directory:[/bold] {Path.cwd()}\n"
        f"[bold]Allowed Directories:[/bold] [yellow]{dirs_str}[/yellow]\n\n"
        "Type your prompt in natural language to manipulate files (e.g. [italic]'create a python project'[/italic]).\n"
        "Type [bold cyan]/help[/bold cyan] for commands, [bold cyan]/tools[/bold cyan] to inspect capabilities, or [bold cyan]/exit[/bold cyan] to quit."
    )
    console.print(Panel(body, title="🚀 [bold green]Ollama File Manipulation Agent[/bold green]", border_style="green"))


def print_help() -> None:
    """Print command help and sample prompts."""
    table = Table(title="Interactive Commands", show_header=True, header_style="bold magenta")
    table.add_column("Command", style="cyan")
    table.add_column("Description")

    table.add_row("/help", "Show this help screen")
    table.add_row("/tools", "List all available file manipulation tools")
    table.add_row("/status", "Show current agent status, model, and allowed directories")
    table.add_row("/clear", "Reset conversation history and memory")
    table.add_row("/model <name>", "Switch active Ollama model (e.g. /model mistral:latest)")
    table.add_row("/exit, /quit", "Exit the application")

    console.print(table)

    sample_prompts = (
        "- [italic]\"List all files in the current folder with their sizes\"[/italic]\n"
        "- [italic]\"Create a new directory called 'demo' and write an app.py with a FastAPI starter\"[/italic]\n"
        "- [italic]\"Search for all files matching '*.py' and find any occurrences of 'import os'\"[/italic]\n"
        "- [italic]\"Replace 'old_string' with 'new_string' in demo/app.py\"[/italic]\n"
        "- [italic]\"Organize files in ./downloads by categorizing them into folders\"[/italic]"
    )
    console.print(Panel(sample_prompts, title="💡 [bold yellow]Example Prompts[/bold yellow]", border_style="yellow"))


def print_tools(agent: OllamaFileAgent) -> None:
    """Print table of available file manipulation tools."""
    table = Table(title="Available System File Tools", show_header=True, header_style="bold blue")
    table.add_column("Tool", style="green")
    table.add_column("Description")

    for name, fn in sorted(agent.tools_map.items()):
        doc = (fn.__doc__ or "").strip().split("\n")[0]
        table.add_row(name, doc)

    console.print(table)


def run_interactive_repl(agent: OllamaFileAgent, allowed_dirs: list[str]) -> None:
    """Run interactive Read-Eval-Print Loop."""
    print_welcome_banner(agent.model, agent.host, allowed_dirs)

    while True:
        try:
            user_input = console.input("\n[bold cyan]ollama-files>[/bold cyan] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Exiting...[/dim]")
            break

        if not user_input:
            continue

        cmd = user_input.lower()
        if cmd in ("/exit", "/quit", "exit", "quit"):
            console.print("[dim]Goodbye![/dim]")
            break
        elif cmd == "/help":
            print_help()
            continue
        elif cmd == "/tools":
            print_tools(agent)
            continue
        elif cmd == "/clear":
            agent.reset()
            console.print("[green]✔ Conversation memory cleared.[/green]")
            continue
        elif cmd == "/status":
            dirs_str = "Unrestricted (*)" if allowed_dirs == ["*"] else ", ".join(allowed_dirs)
            console.print(
                f"[bold]Model:[/bold] {agent.model}\n"
                f"[bold]Host:[/bold] {agent.host}\n"
                f"[bold]Allowed Dirs:[/bold] {dirs_str}\n"
                f"[bold]Messages in Memory:[/bold] {len(agent.messages)}"
            )
            continue
        elif cmd.startswith("/model "):
            new_model = user_input.split(" ", 1)[1].strip()
            agent.model = new_model
            console.print(f"[green]✔ Model switched to: {new_model}[/green]")
            continue

        # Execute prompt with Ollama
        with console.status("[bold green]Ollama is thinking and manipulating files...[/bold green]"):
            response_text = agent.chat(user_input)

        console.print()
        console.print(Panel(Markdown(response_text), title=f"🤖 [bold]{agent.model}[/bold]", border_style="cyan"))


def main() -> None:
    """Application CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Prompt-Driven System File Manipulation using local Ollama (gpt-oss:latest)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="Optional single-shot prompt to execute. If omitted, opens interactive mode.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.getenv("OLLAMA_MODEL", "gpt-oss:latest"),
        help="Ollama model to use for file manipulation.",
    )
    parser.add_argument(
        "--ollama-host",
        type=str,
        default=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        help="URL of the Ollama server.",
    )
    parser.add_argument(
        "--allowed-dirs",
        type=str,
        default=os.getenv("MCP_ALLOWED_DIRS", "."),
        help="Comma-separated list of allowed directories, or '*' for unrestricted access.",
    )
    parser.add_argument(
        "--serve-mcp",
        action="store_true",
        help="Run in standard MCP server mode (for Claude Desktop / Cursor / Antigravity).",
    )
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="MCP transport to use when --serve-mcp is specified.",
    )

    args = parser.parse_args()

    # If --serve-mcp is requested, run as MCP server
    if args.serve_mcp:
        if args.allowed_dirs.strip() == "*":
            allowed_dirs = ["*"]
        else:
            allowed_dirs = [d.strip() for d in args.allowed_dirs.split(",") if d.strip()]

        server = mcp_server_module.create_server(allowed_directories=allowed_dirs)
        server.run(transport=args.transport)
        return

    # Parse allowed directories
    if args.allowed_dirs.strip() == "*":
        allowed_dirs = ["*"]
    else:
        allowed_dirs = [d.strip() for d in args.allowed_dirs.split(",") if d.strip()]

    security = SecurityManager(allowed_directories=allowed_dirs)
    agent = OllamaFileAgent(
        model=args.model,
        host=args.ollama_host,
        security_manager=security,
        verbose=True,
    )

    if args.prompt:
        # Single-shot prompt execution
        with console.status(f"[bold green]Ollama ({args.model}) executing prompt...[/bold green]"):
            result = agent.chat(args.prompt)
        console.print(Panel(Markdown(result), title=f"🤖 [bold]{args.model}[/bold]", border_style="cyan"))
    else:
        # Interactive REPL
        run_interactive_repl(agent, allowed_dirs)


if __name__ == "__main__":
    main()
