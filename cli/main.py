"""CodePilot Interactive CLI — OpenCode Style.

Provides a terminal interface styled after OpenCode / modern coding agents:
- Rich formatted panels, banners, and status spinners
- Live tool execution traces
- Slash commands (/help, /model, /workspace, /trace, /clear, /exit)
- Markdown and syntax-highlighted code rendering
- Direct local integration with Ollama and strict workspace sandboxing
"""

import os
import re
import sys
import argparse
from pathlib import Path

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
from backend.app.agent.skills import discover_skills

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
    """Render the CodePilot header banner."""
    workspace = str(settings.resolved_workspace_root)
    header_text = Text()
    header_text.append("⚡ ", style="bold yellow")
    header_text.append("CodePilot ", style="bold #d97757")
    header_text.append("\n")
    header_text.append("Local Coding Assistant • Ollama\n", style="dim white")
    header_text.append(f"Model: {model_name}  •  Workspace: {workspace}  •  Type ", style="cyan")
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
    table.add_row("/workspace", "Show and list the active workspace")
    table.add_row("/workspace default", "Return to the configured default workspace")
    table.add_row("/trace", "Show the detailed tool execution trace of the last turn")
    table.add_row("/skills", "List available agent skills")
    table.add_row("/allow-edits", "Toggle file creation and replacement for coding tasks")
    table.add_row("/allow-tests", "Toggle the pytest runner for coding tasks")
    table.add_row("/clear", "Clear the terminal screen")
    table.add_row("/exit, /quit", "Exit the CodePilot CLI")

    console.print(table)


def list_workspace_files(workspace_root: Path | None = None):
    """List workspace files cleanly."""
    ws_root = workspace_root or settings.resolved_workspace_root
    files = os.listdir(ws_root)
    table = Table(title=f"Workspace Contents ({ws_root})", border_style="cyan")
    table.add_column("File / Directory", style="bold green")
    table.add_column("Size", style="dim white")
    for f in sorted(files):
        p = os.path.join(ws_root, f)
        size = f"{os.path.getsize(p)} bytes" if os.path.isfile(p) else "DIR"
        table.add_row(f, size)
    console.print(table)


def workspace_requested_by_prompt(
    prompt: str,
    home_directory: Path | None = None,
) -> Path | None:
    """Resolve an explicitly named home-directory workspace or save destination."""
    home = (home_directory or Path.home()).resolve()
    direct_path = prompt.strip().strip("'\"")
    if direct_path.startswith(("~", "/")) and not any(char.isspace() for char in direct_path):
        requested_path = Path(direct_path).expanduser().resolve()
        try:
            requested_path.relative_to(home)
        except ValueError:
            return None
        if requested_path.is_dir():
            return requested_path

    selects_workspace = re.search(
        r"\b(?:use|set|switch|change|select|open)\b.{0,200}\bworkspace\b"
        r"|\bworkspace\b.{0,200}\b(?:use|set|switch|change|select|open)\b",
        prompt,
        re.IGNORECASE,
    )
    saves_to_path = re.search(r"\b(?:save|write|store|put|create)\b", prompt, re.IGNORECASE)
    if not (selects_workspace or saves_to_path):
        return None

    path_match = re.search(r"(?P<path>~(?=/)[^\s,;]+|/[^\s,;]+)", prompt)
    if path_match:
        requested_path = Path(path_match.group("path").rstrip(".,:!?)]}'\"")).expanduser().resolve()
        try:
            requested_path.relative_to(home)
        except ValueError:
            return None
        if selects_workspace:
            return requested_path if requested_path.is_dir() else None
        candidate = requested_path if requested_path.is_dir() else requested_path.parent
        while candidate != home and not candidate.is_dir():
            candidate = candidate.parent
        if candidate.is_dir():
            return candidate

    if re.search(r"\b(?:in|to|on|under|inside)\s+(?:my\s+)?desktop\b", prompt, re.IGNORECASE):
        desktop = (home / "Desktop").resolve()
        try:
            desktop.relative_to(home)
        except ValueError:
            return None
        if desktop.is_dir():
            return desktop

    return None


def prompt_requests_file_edits(prompt: str) -> bool:
    """Grant per-turn editing only when the user asks for an implementation change."""
    if re.search(r"\bhow\s+(?:(?:do|would|can|should)\s+i|to)\b", prompt, re.IGNORECASE):
        return False
    action = re.search(
        r"\b(?:create|write|save|edit|update|modify|fix|refactor|implement|add|remove|delete|rename)\b",
        prompt,
        re.IGNORECASE,
    )
    target = re.search(
        r"\b(?:file|folder|directory|module|class|function|script|code|bug|feature|test|calculator)\b",
        prompt,
        re.IGNORECASE,
    )
    return bool(action and target)


def run_cli():
    current_model = DEFAULT_MODEL
    allow_edits = False
    allow_test_execution = False
    current_workspace = settings.resolved_workspace_root
    current_workspace_is_external = False
    conversation_history: list[dict[str, str]] = []
    console.clear()
    print_banner(current_model)

    client = ollama.Client(
        host=settings.ollama_base_url,
        timeout=settings.ollama_request_timeout_seconds,
    )

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
            console.print(f"[info]Active workspace:[/info] {current_workspace}")
            list_workspace_files(current_workspace)
            continue
        elif user_input == "/workspace default":
            current_workspace = settings.resolved_workspace_root
            current_workspace_is_external = False
            console.print(f"[info]Returned to default workspace:[/info] {current_workspace}")
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
        elif user_input == "/skills":
            skills = discover_skills()
            if not skills:
                console.print("[dim]No bundled skills are available.[/dim]")
            else:
                table = Table(title="Available Agent Skills", border_style="cyan")
                table.add_column("Skill", style="bold yellow")
                table.add_column("When to use it", style="white")
                for skill in skills:
                    table.add_row(skill.name, skill.description)
                console.print(table)
            continue
        elif user_input == "/allow-edits":
            allow_edits = not allow_edits
            state = "enabled" if allow_edits else "disabled"
            console.print(f"[warning]File edits {state} for subsequent tasks.[/warning]")
            continue
        elif user_input == "/allow-tests":
            allow_test_execution = not allow_test_execution
            state = "enabled" if allow_test_execution else "disabled"
            console.print(f"[warning]Pytest execution {state} for subsequent tasks.[/warning]")
            continue

        # Execute agent turn with rich status
        requested_workspace = workspace_requested_by_prompt(user_input)
        if requested_workspace:
            current_workspace = requested_workspace
            current_workspace_is_external = True
        if requested_workspace:
            console.print(f"[info]Using the directory named in your prompt for this task:[/info] {requested_workspace}")
        edits_for_request = allow_edits or prompt_requests_file_edits(user_input)
        if edits_for_request and not allow_edits:
            console.print("[info]This prompt requests a file change; allowing edits for this task only.[/info]")

        try:
            with console.status(f"[bold cyan]Planning & running tools with {current_model}...[/bold cyan]", spinner="dots"):
                response_text, steps, _ = run_agent_turn(
                    user_prompt=user_input,
                    model_name=current_model,
                    history=conversation_history,
                    workspace=str(current_workspace),
                    allow_edits=edits_for_request,
                    allow_test_execution=allow_test_execution,
                    allow_external_workspace=current_workspace_is_external,
                )
        except KeyboardInterrupt:
            console.print("\n[warning]Turn interrupted. No response was received.[/warning]")
            continue
        except Exception as exc:
            console.print(
                f"\n[danger]Agent turn failed ({type(exc).__name__}): {exc}[/danger]"
            )
            console.print_exception(show_locals=False)
            continue

        last_traces = steps
        conversation_history.extend([
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": response_text},
        ])
        del conversation_history[:-12]

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
                    border_style="magenta" if s.get("status") == "completed" else "red",
                    padding=(0, 1),
                ))
                latency = s.get("latency_ms", 0)
                if s.get("status") == "completed":
                    console.print(f"[success]✔ Completed in {latency}ms[/success]\n")
                else:
                    console.print(f"[danger]✘ Failed in {latency}ms[/danger]\n")

        # Render final markdown response in terminal
        console.print(Markdown(response_text))


if __name__ == "__main__":
    argparse.ArgumentParser(description="Run CodePilot; name the save location in your task prompt.").parse_args()
    run_cli()
