import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from typing import List, Optional
import shlex
import sys
try:
    import readline
    HAS_READLINE = True
except ImportError:
    HAS_READLINE = False

console = Console()

def parse_command(command_line: str) -> tuple[str, List[str]]:
    """Parse a command line into command name and arguments."""
    try:
        parts = shlex.split(command_line)
        if not parts:
            return "", []
        return parts[0], parts[1:]
    except ValueError as e:
        console.print(f"[red]Error parsing command: {e}[/red]")
        return "", []

def run_shell(app: typer.Typer, parent_ctx: typer.Context):
    """Run an interactive shell for the CLI."""
    # Setup readline history if available
    if HAS_READLINE:
        import tempfile
        import os
        history_file = os.path.join(tempfile.gettempdir(), '.powerloom_shell_history')
        try:
            readline.read_history_file(history_file)
        except FileNotFoundError:
            pass  # History file doesn't exist yet
        readline.set_history_length(1000)
    
    console.print(Panel.fit(
        "[bold green]PowerLoom Snapshotter CLI - Interactive Mode[/bold green]\n"
        "Type 'help' for available commands, 'exit' or 'quit' to leave.\n"
        "Use Ctrl+C to cancel current command.",
        border_style="green"
    ))
    
    # Build command map from the app
    commands = {}
    
    # Get the Click command group from Typer app
    from typer.main import get_command
    click_group = get_command(app)
    
    # Iterate through registered commands
    if hasattr(click_group, 'commands'):
        for name in click_group.commands:
            if name != "shell":  # Don't include shell itself
                commands[name] = click_group.commands[name]
    
    # Add special commands
    special_commands = {
        "help": lambda: show_help(commands),
        "exit": lambda: sys.exit(0),
        "quit": lambda: sys.exit(0),
        "clear": lambda: console.clear(),
        "cls": lambda: console.clear(),
    }
    
    while True:
        try:
            # Get user input with readline support
            if HAS_READLINE:
                try:
                    command_line = input("\npowerloom-snapshotter> ").strip()
                except EOFError:
                    console.print("\n[yellow]Goodbye![/yellow]")
                    break
            else:
                command_line = Prompt.ask("\n[bold cyan]powerloom-snapshotter[/bold cyan]", default="").strip()
            
            if not command_line:
                continue
            
            # Parse command
            cmd_name, args = parse_command(command_line)
            
            # Handle special commands
            if cmd_name in special_commands:
                special_commands[cmd_name]()
                continue
            
            # Handle regular commands
            if cmd_name in commands:
                try:
                    # Get the Click command
                    click_cmd = commands[cmd_name]
                    
                    # Create a new context for this command
                    from typer.main import get_command
                    click_group = get_command(app)
                    
                    # Use Click's Context to invoke the command  
                    import click
                    # Create a fresh context that includes the parent's obj (CLIContext)
                    with click_group.make_context('powerloom-snapshotter', [cmd_name] + args) as cmd_ctx:
                        # Copy the parent context's obj if it exists
                        if hasattr(parent_ctx, 'obj') and parent_ctx.obj:
                            cmd_ctx.obj = parent_ctx.obj
                        click_group.invoke(cmd_ctx)
                        
                except click.exceptions.Exit:
                    # Normal exit from command
                    pass
                except typer.Exit:
                    # Commands might call typer.Exit, which we should catch
                    pass
                except click.exceptions.UsageError as e:
                    console.print(f"[red]Usage error: {e}[/red]")
                except Exception as e:
                    console.print(f"[red]Error executing command: {e}[/red]")
            else:
                console.print(f"[red]Unknown command: {cmd_name}[/red]")
                console.print("Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'exit' or 'quit' to leave the shell.[/yellow]")
        except EOFError:
            # Handle Ctrl+D
            console.print("\n[yellow]Goodbye![/yellow]")
            break
    
    # Save history on exit
    if HAS_READLINE:
        try:
            readline.write_history_file(history_file)
        except:
            pass  # Ignore errors saving history

def show_help(commands: dict):
    """Show available commands."""
    console.print("\n[bold]Available Commands:[/bold]")
    
    # Regular commands
    for name, command in sorted(commands.items()):
        # Get help text from Click command
        help_text = getattr(command, 'help', None) or getattr(command, 'short_help', None) or "No description available"
        # Get first line of help text
        help_line = str(help_text).split('\n')[0] if help_text else "No description available"
        console.print(f"  [cyan]{name:<15}[/cyan] {help_line}")
    
    # Special commands
    console.print("\n[bold]Special Commands:[/bold]")
    console.print("  [cyan]help[/cyan]           Show this help message")
    console.print("  [cyan]clear/cls[/cyan]      Clear the screen")
    console.print("  [cyan]exit/quit[/cyan]      Exit the shell")
    console.print("\n[dim]Tip: You can use shell syntax like quotes for arguments with spaces.[/dim]")

def shell_command(ctx: typer.Context):
    """Start an interactive shell session."""
    # Import here to avoid circular imports
    from snapshotter_cli.cli import app
    
    # Get the parent context which has the loaded config
    parent_ctx = ctx.parent if ctx.parent else ctx
    run_shell(app, parent_ctx)