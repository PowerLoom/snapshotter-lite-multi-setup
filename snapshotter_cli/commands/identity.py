import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path
from typing import Optional, List
import os
from glob import glob

from ..utils.models import CLIContext
from ..utils.deployment import CONFIG_ENV_FILENAME_TEMPLATE, parse_env_file_vars

console = Console()

identity_app = typer.Typer(
    name="identity",
    help="Manage chain and market-specific identity configurations via namespaced .env files.",
    no_args_is_help=True
)

def list_env_files() -> List[Path]:
    """Find all namespaced .env files in the current directory."""
    env_files = []
    for file in glob(".env.*.*.*"):
        if file.count('.') == 3:  # Should match .env.chain.market.source_chain pattern
            env_files.append(Path(file))
    return sorted(env_files)

@identity_app.command("list")
def list_identities(ctx: typer.Context):
    """List all configured identities (namespaced .env files) and their contents."""
    env_files = list_env_files()
    
    if not env_files:
        console.print("No namespaced .env files found. Use 'snapshotter-cli configure' to create one.", style="yellow")
        return

    table = Table(title="Configured Identities", show_header=True, header_style="bold blue")
    table.add_column("Chain", style="magenta")
    table.add_column("Market", style="cyan")
    table.add_column("Source Chain", style="green")
    table.add_column("Wallet Address", style="dim")
    table.add_column("Signer Address", style="dim")
    table.add_column("Has Private Key", style="dim")
    table.add_column("Source RPC", style="dim")

    for env_file in env_files:
        # Parse filename parts (.env.chain.market.source_chain)
        parts = env_file.name.split('.')
        if len(parts) != 4:
            continue
        
        chain = parts[1].upper()
        market = parts[2].upper()
        source_chain = parts[3].upper()
        
        env_vars = parse_env_file_vars(str(env_file))
        
        table.add_row(
            chain,
            market,
            source_chain,
            env_vars.get("WALLET_HOLDER_ADDRESS", "[Not Set]"),
            env_vars.get("SIGNER_ACCOUNT_ADDRESS", "[Not Set]"),
            "✓" if env_vars.get("SIGNER_ACCOUNT_PRIVATE_KEY") else "✗",
            "✓" if env_vars.get("SOURCE_RPC_URL") else "✗"
        )

    console.print(table)
    console.print("\nℹ️ Use 'snapshotter-cli configure' to create or update these configurations.", style="blue")

@identity_app.command("show")
def show_identity(
    ctx: typer.Context,
    chain: str = typer.Option(..., "--chain", "-c", help="Powerloom chain name (e.g., DEVNET, MAINNET)"),
    market: str = typer.Option(..., "--market", "-m", help="Data market name (e.g., UNISWAPV2)"),
    source_chain: str = typer.Option(..., "--source-chain", "-s", help="Source chain name (e.g., ETH-MAINNET)")
):
    """Show the contents of a specific namespaced .env file."""
    # Normalize inputs for filename
    norm_chain = chain.lower()
    norm_market = market.lower()
    norm_source = source_chain.lower().replace('-', '_')
    
    env_filename = CONFIG_ENV_FILENAME_TEMPLATE.format(norm_chain, norm_market, norm_source)
    env_path = Path(os.getcwd()) / env_filename
    
    if not env_path.exists():
        console.print(f"No configuration found for {chain}/{market}/{source_chain}.", style="yellow")
        console.print(f"Use 'snapshotter-cli configure' to create one.", style="blue")
        return

    env_vars = parse_env_file_vars(str(env_path))
    
    console.print(f"\n[bold]Configuration for {chain}/{market}/{source_chain}[/bold]")
    console.print(f"File: {env_filename}\n")
    
    # Display in sections
    console.print("[bold]Identity[/bold]")
    console.print(f"  Wallet Address: {env_vars.get('WALLET_HOLDER_ADDRESS', '[Not Set]')}")
    console.print(f"  Signer Address: {env_vars.get('SIGNER_ACCOUNT_ADDRESS', '[Not Set]')}")
    console.print(f"  Signer Private Key: {'[Set]' if env_vars.get('SIGNER_ACCOUNT_PRIVATE_KEY') else '[Not Set]'}")
    
    console.print("\n[bold]RPC Configuration[/bold]")
    console.print(f"  Source RPC URL: {env_vars.get('SOURCE_RPC_URL', '[Not Set]')}")
    console.print(f"  Powerloom RPC URL: {env_vars.get('POWERLOOM_RPC_URL', '[Not Set]')}")
    
    # Show other relevant configuration if present
    if "TELEGRAM_CHAT_ID" in env_vars or "TELEGRAM_REPORTING_URL" in env_vars:
        console.print("\n[bold]Notifications[/bold]")
        if "TELEGRAM_CHAT_ID" in env_vars:
            console.print(f"  Telegram Chat ID: {env_vars['TELEGRAM_CHAT_ID']}")
        if "TELEGRAM_REPORTING_URL" in env_vars:
            console.print(f"  Telegram Reporting URL: {env_vars['TELEGRAM_REPORTING_URL']}")

@identity_app.command("delete")
def delete_identity(
    ctx: typer.Context,
    chain: str = typer.Option(..., "--chain", "-c", help="Powerloom chain name (e.g., DEVNET, MAINNET)"),
    market: str = typer.Option(..., "--market", "-m", help="Data market name (e.g., UNISWAPV2)"),
    source_chain: str = typer.Option(..., "--source-chain", "-s", help="Source chain name (e.g., ETH-MAINNET)")
):
    """Delete a specific namespaced .env file."""
    # Normalize inputs for filename
    norm_chain = chain.lower()
    norm_market = market.lower()
    norm_source = source_chain.lower().replace('-', '_')
    
    env_filename = CONFIG_ENV_FILENAME_TEMPLATE.format(norm_chain, norm_market, norm_source)
    env_path = Path(os.getcwd()) / env_filename
    
    if not env_path.exists():
        console.print(f"No configuration found for {chain}/{market}/{source_chain}.", style="yellow")
        return

    if typer.confirm(f"Are you sure you want to delete the configuration for {chain}/{market}/{source_chain}?"):
        try:
            env_path.unlink()
            console.print(f"✅ Deleted configuration: {env_filename}", style="green")
        except OSError as e:
            console.print(f"Error deleting configuration: {e}", style="bold red")
            raise typer.Exit(1)


