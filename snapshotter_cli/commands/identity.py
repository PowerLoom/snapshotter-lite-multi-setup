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
# TODO: locate env files in user's home directory instead of current directory. For eg: ~/.snapshotter-cli/envs/.env.devnet.uniswapv2.eth-mainnet
def list_env_files(cli_context: CLIContext) -> List[Path]:
    """Find all namespaced .env files in the current directory using known chains and markets."""
    env_files = []
    available_chains = [x.lower() for x in cli_context.available_environments]
    available_markets = [x.lower() for x in cli_context.available_markets]

    for file in glob(".env.*.*.*"):
        parts = file.strip().split('.')
        if len(parts) == 5:
            chain, market, source_chain = parts[2].lower(), parts[3].lower(), parts[4]
            if chain in available_chains and market in available_markets:
                env_files.append(Path(file))

    return sorted(env_files)

@identity_app.command("list")
def list_identities(ctx: typer.Context):
    """List all configured identities (namespaced .env files) with basic status."""
    cli_context: CLIContext = ctx.obj
    env_files = list_env_files(cli_context)
    
    if not env_files:
        console.print("No namespaced .env files found. Use 'snapshotter-cli configure' to create one.", style="yellow")
        return

    table = Table(title="Configured Identities", show_header=True, header_style="bold blue", title_style="bold cyan")
    table.add_column("Chain", style="magenta")
    table.add_column("Market", style="cyan")
    table.add_column("Source Chain", style="green")
    table.add_column("Status", style="yellow")

    for env_file in env_files:
        parts = env_file.name.split('.')
        chain = parts[2].upper()
        market = parts[3].upper()
        source_chain = parts[4].upper()
        
        env_vars = parse_env_file_vars(str(env_file))
        
        # Determine configuration status
        status_parts = []
        if not env_vars.get("WALLET_HOLDER_ADDRESS"):
            status_parts.append("❌ No Wallet")
        if not env_vars.get("SIGNER_ACCOUNT_ADDRESS"):
            status_parts.append("❌ No Signer")
        if not env_vars.get("SIGNER_ACCOUNT_PRIVATE_KEY"):
            status_parts.append("❌ No Key")
        if not env_vars.get("SOURCE_RPC_URL"):
            status_parts.append("❌ No RPC")
        if not env_vars.get("POWERLOOM_RPC_URL"):
            status_parts.append("❌ No Powerloom RPC")
        
        status = "✓ Ready" if not status_parts else " ".join(status_parts)
        
        table.add_row(
            chain,
            market,
            source_chain,
            status
        )

    console.print(table)
    console.print("\nℹ️ Use 'snapshotter-cli identity show --chain <CHAIN> --market <MARKET> --source-chain <SOURCE_CHAIN>' to view detailed configuration.", style="blue")
    console.print("ℹ️ Use 'snapshotter-cli configure' to create or update these configurations.", style="blue")

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


