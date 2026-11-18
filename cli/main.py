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
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt
from rich.theme import Theme

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

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
WORKSPACE_ROOT = os.path.abspath(os.getenv("WORKSPACE_ROOT", "./workspace"))
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")

# Simple tool definition for CLI agent
list_files_tool = {
    "type": "function",
    "function": {
        "name": "list_files",
        "description": "List files and subdirectories in the specified workspace directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Relative directory path inside the workspace to list. Defaults to '.'",
                }
            },
            "required": [],
        },
    },
}

read_file_tool = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read the contents of a text file located inside the workspace.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Workspace-relative file path to read.",
                }
            },
            "required": ["path"],
        },
    },
}

write_file_tool = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "Write or create a text file inside the workspace safely.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Workspace-relative file path to write to.",
                },
                "content": {
                    "type": "string",
                    "description": "The exact content to write into the file.",
                },
            },
            "required": ["path", "content"],
        },
    },
}

AVAILABLE_TOOLS = [list_files_tool, read_file_tool, write_file_tool]


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
    if not os.path.exists(WORKSPACE_ROOT):
        os.makedirs(WORKSPACE_ROOT, exist_ok=True)
    files = os.listdir(WORKSPACE_ROOT)
    table = Table(title=f"Workspace Contents ({WORKSPACE_ROOT})", border_style="cyan")
    table.add_column("File / Directory", style="bold green")
    table.add_column("Size", style="dim white")
    for f in sorted(files):
        p = os.path.join(WORKSPACE_ROOT, f)
        size = f"{os.path.getsize(p)} bytes" if os.path.isfile(p) else "DIR"
        table.add_row(f, size)
    console.print(table)


def execute_tool_safely(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute tools within strict workspace boundaries."""
    if name == "list_files":
        sub_dir = args.get("directory", ".")
        target = os.path.abspath(os.path.join(WORKSPACE_ROOT, sub_dir))
        if not target.startswith(WORKSPACE_ROOT):
            return {"ok": False, "error": "Access denied: Path escapes workspace root."}
        if not os.path.exists(target):
            return {"ok": False, "error": f"Directory not found: {sub_dir}"}
        return {"ok": True, "files": os.listdir(target)}

    elif name == "read_file":
        rel_path = args.get("path", "")
        target = os.path.abspath(os.path.join(WORKSPACE_ROOT, rel_path))
        if not target.startswith(WORKSPACE_ROOT):
            return {"ok": False, "error": "Access denied: Path escapes workspace root."}
        if not os.path.exists(target):
            return {"ok": False, "error": f"File not found: {rel_path}"}
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(50000)
        return {"ok": True, "content": content}

    elif name == "write_file":
        rel_path = args.get("path", "")
        content = args.get("content", "")
        target = os.path.abspath(os.path.join(WORKSPACE_ROOT, rel_path))
        if not target.startswith(WORKSPACE_ROOT):
            return {"ok": False, "error": "Access denied: Path escapes workspace root."}
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        return {"ok": True, "written_bytes": len(content)}

    return {"ok": False, "error": f"Unknown tool: {name}"}


def run_cli():
    current_model = DEFAULT_MODEL
    console.clear()
    print_banner(current_model)

    client = ollama.Client(host=OLLAMA_BASE_URL)

    # Verify Ollama connection
    try:
        models_resp = client.list()
        avail = [m.model for m in models_resp.models]
    except Exception as e:
        console.print(f"[danger]✘ Cannot connect to Ollama at {OLLAMA_BASE_URL}[/danger]")
        console.print(f"[dim]Make sure Ollama is running: brew services start ollama[/dim]\n")
        return

    # Canonical system instructions
    system_prompt = (
        "You are CodePilot, a software engineering assistant running locally. "
        "Inspect the workspace before proposing edits, and use tools to inspect or edit files. "
        "Always keep file edits inside the workspace."
    )
    prompt_file = os.path.join(os.getcwd(), "prompts", "SYSTEM_PROMPT.md")
    if os.path.exists(prompt_file):
        with open(prompt_file, "r") as f:
            system_prompt = f.read()

    conversation = [{"role": "system", "content": system_prompt}]
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

        # Agent Execution Loop
        conversation.append({"role": "user", "content": user_input})
        last_traces = []

        with console.status(f"[bold cyan]Planning with {current_model}...[/bold cyan]", spinner="dots"):
            try:
                response = client.chat(
                    model=current_model,
                    messages=conversation,
                    tools=AVAILABLE_TOOLS,
                )
            except Exception as e:
                console.print(f"[danger]Model generation error:[/danger] {e}")
                continue

        # Check for tool calls (Ollama native or parsed)
        from backend.app.smoke_test import extract_tool_calls
        tool_calls = extract_tool_calls(response.message)

        if tool_calls:
            for tc in tool_calls:
                fn_name = tc.get("name")
                fn_args = tc.get("arguments", {})

                # OpenCode tool call card
                call_text = Text()
                call_text.append(f"Tool: {fn_name}\n", style="bold magenta")
                call_text.append(f"Arguments: {json.dumps(fn_args, indent=2)}", style="dim cyan")
                console.print(Panel(call_text, title=f"🛠️  Tool Call: {fn_name}", border_style="magenta", padding=(0, 1)))

                # Execute
                start_time = time.time()
                tool_output = execute_tool_safely(fn_name, fn_args)
                latency = round((time.time() - start_time) * 1000, 1)

                status_style = "green" if tool_output.get("ok") else "red"
                status_icon = "✔" if tool_output.get("ok") else "✘"
                console.print(f"[{status_style}]{status_icon} Executed in {latency}ms[/{status_style}] -> {tool_output.get('summary', str(tool_output)[:100])}")

                last_traces.append({
                    "tool": fn_name,
                    "arguments": fn_args,
                    "result": tool_output,
                    "latency_ms": latency,
                })

                # Append to conversation
                if getattr(response.message, "tool_calls", None):
                    conversation.append(response.message)
                    conversation.append({
                        "role": "tool",
                        "content": json.dumps(tool_output),
                    })
                else:
                    conversation.append({"role": "assistant", "content": response.message.content or ""})
                    conversation.append({"role": "user", "content": f"Tool '{fn_name}' returned: {json.dumps(tool_output)}. Now provide your final answer."})

            # Final synthesis
            with console.status(f"[bold cyan]Synthesizing final response...[/bold cyan]", spinner="dots"):
                try:
                    final_res = client.chat(
                        model=current_model,
                        messages=conversation,
                    )
                    final_text = final_res.message.content or ""
                    conversation.append(final_res.message)
                except Exception as e:
                    console.print(f"[danger]Synthesis error:[/danger] {e}")
                    continue
        else:
            final_text = response.message.content or ""
            conversation.append(response.message)

        # Render final markdown response in terminal
        console.print()
        console.print(Markdown(final_text))


if __name__ == "__main__":
    run_cli()
