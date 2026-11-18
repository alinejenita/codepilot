"""CodePilot Interactive CLI — OpenCode Style.

Provides a terminal interface styled after OpenCode / modern coding agents:
- Rich formatted panels, banners, and status spinners
- Live tool execution traces
- Slash commands (/help, /model, /workspace, /trace, /clear, /exit)
- Markdown and syntax-highlighted code rendering
- Direct local integration with Ollama and strict workspace sandboxing
"""

import os
import sys

# Ensure repository root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment
load_dotenv()

import ollama
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from backend.app.config import settings
from backend.app.agent.loop import run_agent_turn

# Custom OpenCode theme
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "danger": "bold red",
    "success": "bold green",
    "accent": "bold #d97757",
    "tool": "bold magenta",
    "code": "bright_cyan",
})

console = Console(theme=custom_theme)

DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")


def print_banner(model_name: str):
    """Render the OpenCode signature header banner."""
    header_text = Text()
    header_text.append("⚡ ", style="bold yellow")
    header_text.append("CodePilot ", style="bold #d97757")
    header_text.append("(OpenCode Terminal)\n", style="bold white")
    header_text.append("Local Autonomous Coding Assistant • Apple Silicon M4 Metal\n", style="dim white")
    header_text.append(f"Model: {model_name}  •  Workspace: ./workspace (Sandboxed)  •  Type ", style="cyan")
    header_text.append("/help", style="bold yellow")
    header_text.append(" for commands", style="cyan")

    panel = Panel(
        header_text,
        border_style="#d97757",
        padding=(0, 2),
    )
    console.print(panel)


def print_help():
    """Display slash commands in a clean table."""
    table = Table(title="Available Slash Commands", border_style="dim", title_style="bold cyan")
    table.add_column("Command", style="bold yellow", width=16)
    table.add_column("Description", style="white")

    table.add_row("/help", "Show this help screen")
    table.add_row("/model <name>", "Switch model (e.g. /model qwen2.5-coder:7b or qwen3.5:4b)")
    table.add_row("/workspace", "List all files currently inside ./workspace")
    table.add_row("/trace", "Show the detailed tool execution trace of the last turn")
    table.add_row("/clear", "Clear the terminal screen")
    table.add_row("/exit, /quit", "Exit the CodePilot CLI")

    console.print(table)


def list_workspace_files():
    """List workspace files cleanly."""
    ws_root = settings.resolved_workspace_root
    if not os.path.exists(ws_root):
        os.makedirs(ws_root, exist_ok=True)
    files = os.listdir(ws_root)
    table = Table(title=f"Workspace Contents ({ws_root})", border_style="cyan")
    table.add_column("File / Directory", style="bold green")
    table.add_column("Size", style="dim white")
    for f in sorted(files):
        p = os.path.join(ws_root, f)
        size = f"{os.path.getsize(p)} bytes" if os.path.isfile(p) else "DIR"
        table.add_row(f, size)
    console.print(table)


def run_cli():
    current_model = DEFAULT_MODEL
    console.clear()
    print_banner(current_model)

    client = ollama.Client(host=settings.ollama_base_url)

    # Verify Ollama connection
    try:
        models_resp = client.list()
    except Exception as e:
        console.print(f"[danger]✘ Cannot connect to Ollama at {settings.ollama_base_url}[/danger]")
        console.print(f"[dim]Make sure Ollama is running: brew services start ollama[/dim]\n")
        return

    last_traces: List[Dict[str, Any]] = []

    while True:
        try:
            user_input = console.input(f"\n[bold #d97757]CodePilot[/bold #d97757] [bold green]❯[/bold green] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Exiting CodePilot. Goodbye![/dim]")
            break

        if not user_input:
            continue

        # Handle Slash Commands
        if user_input in ("/exit", "/quit"):
            console.print("[dim]Exiting CodePilot. Goodbye![/dim]")
            break
        elif user_input == "/help":
            print_help()
            continue
        elif user_input == "/clear":
            console.clear()
            print_banner(current_model)
            continue
        elif user_input == "/workspace":
            list_workspace_files()
            continue
        elif user_input.startswith("/model"):
            parts = user_input.split()
            if len(parts) > 1:
                current_model = parts[1]
                console.print(f"[success]✔ Switched active model to:[/success] [bold cyan]{current_model}[/bold cyan]")
            else:
                console.print(f"[info]Current model:[/info] {current_model}")
            continue
        elif user_input == "/trace":
            if not last_traces:
                console.print("[dim]No tool execution traces recorded for the last turn.[/dim]")
            else:
                console.print(Panel(
                    json.dumps(last_traces, indent=2),
                    title="Last Turn Execution Traces",
                    border_style="magenta",
                ))
            continue

        # Execute agent turn with rich status
        with console.status(f"[bold cyan]Planning & running tools with {current_model}...[/bold cyan]", spinner="dots"):
            response_text, steps = run_agent_turn(
                user_prompt=user_input,
                model_name=current_model,
            )

        last_traces = steps

        # Render each executed tool step in OpenCode style
        if steps:
            for s in steps:
                call_text = Text()
                call_text.append(f"Tool: {s['tool']}\n", style="bold magenta")
                call_text.append(f"Arguments: {json.dumps(s.get('args', {}), indent=2)}\n", style="dim cyan")
                call_text.append(f"Summary: {s.get('summary', '')}", style="white")

                console.print(Panel(
                    call_text,
                    title=f"🛠️  Tool Execution: {s['tool']}",
                    border_style="magenta",
                    padding=(0, 1),
                ))
                latency = s.get("latency_ms", 0)
                status_style = "green" if s.get("status") == "completed" else "red"
                console.print(f"[{status_style}]✔ Completed in {latency}ms[/{status_style}]\n")

        # Render final markdown response in terminal
        console.print(Markdown(response_text))


if __name__ == "__main__":
    run_cli()
