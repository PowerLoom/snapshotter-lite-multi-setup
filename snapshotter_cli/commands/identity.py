import os
from glob import glob
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from ..utils.deployment import (
    CONFIG_DIR,
    CONFIG_ENV_FILENAME_TEMPLATE,
    parse_env_file_vars,
)
from ..utils.models import CLIContext

console = Console()

identity_app = typer.Typer(
    name="identity",
    help="Manage chain and market-specific identity configurations via namespaced .env files.",
    no_args_is_help=True,
)


def list_env_files(cli_context: CLIContext) -> List[Path]:
    """Find all namespaced .env files in the user's home directory using known chains and markets."""
    env_files = []
    available_chains = [x.lower() for x in cli_context.available_environments]
    available_markets = [x.lower() for x in cli_context.available_markets]

    # Create config directory if it doesn't exist
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Search for env files in the config directory
    for file in CONFIG_DIR.glob(".env.*.*.*"):
        parts = file.name.strip().split(".")
        if len(parts) == 5:
            chain, market, source_chain = parts[2].lower(), parts[3].lower(), parts[4]
            if chain in available_chains and market in available_markets:
                env_files.append(file)

    # Also check current directory for backward compatibility
    for file in Path().glob(".env.*.*.*"):
        parts = file.name.strip().split(".")
        if len(parts) == 5:
            chain, market, source_chain = parts[2].lower(), parts[3].lower(), parts[4]
            if chain in available_chains and market in available_markets:
                # If file exists in both places, prefer the one in config directory
                if not any(ef.name == file.name for ef in env_files):
                    console.print(
                        f"⚠️ Found legacy env file in current directory: {file}. Consider moving it to {CONFIG_DIR}",
                        style="yellow",
                    )
                    env_files.append(file)

    return sorted(env_files)


@identity_app.command("list")
def list_identities(ctx: typer.Context):
    """List all configured identities (namespaced .env files) with basic status."""
    cli_context: CLIContext = ctx.obj
    env_files = list_env_files(cli_context)

    if not env_files:
        console.print(
            "No namespaced .env files found. Use 'powerloom-snapshotter-cli configure' to create one.",
            style="yellow",
        )
        return

    table = Table(
        title="Configured Identities",
        show_header=True,
        header_style="bold blue",
        title_style="bold cyan",
    )
    table.add_column("Chain", style="magenta")
    table.add_column("Market", style="cyan")
    table.add_column("Source Chain", style="green")
    table.add_column("Status", style="yellow")

    for env_file in env_files:
        parts = env_file.name.split(".")
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

        table.add_row(chain, market, source_chain, status)

    console.print(table)
    console.print(
        "\nℹ️ Use 'powerloom-snapshotter-cli identity show --chain <CHAIN> --market <MARKET> --source-chain <SOURCE_CHAIN>' to view detailed configuration.",
        style="blue",
    )
    console.print(
        "ℹ️ Use 'powerloom-snapshotter-cli configure' to create or update these configurations.",
        style="blue",
    )


@identity_app.command("show")
def show_identity(
    ctx: typer.Context,
    chain: str = typer.Option(
        ..., "--chain", "-c", help="Powerloom chain name (e.g., DEVNET, MAINNET)"
    ),
    market: str = typer.Option(
        ..., "--market", "-m", help="Data market name (e.g., UNISWAPV2)"
    ),
    source_chain: str = typer.Option(
        ..., "--source-chain", "-s", help="Source chain name (e.g., ETH-MAINNET)"
    ),
):
    """Show the contents of a specific namespaced .env file."""
    # Normalize inputs for filename
    norm_chain = chain.lower()
    norm_market = market.lower()
    norm_source = source_chain.lower().replace("-", "_")

    env_filename = CONFIG_ENV_FILENAME_TEMPLATE.format(
        norm_chain, norm_market, norm_source
    )

    # First check in config directory
    env_path = CONFIG_DIR / env_filename

    # If not found in config directory, check current directory for backward compatibility
    if not env_path.exists():
        cwd_env_path = Path(os.getcwd()) / env_filename
        if cwd_env_path.exists():
            console.print(
                f"⚠️ Found legacy env file in current directory. Consider moving it to {CONFIG_DIR}",
                style="yellow",
            )
            env_path = cwd_env_path

    if not env_path.exists():
        console.print(
            f"No configuration found for {chain}/{market}/{source_chain}.",
            style="yellow",
        )
        console.print(
            f"Use 'powerloom-snapshotter-cli configure' to create one.", style="blue"
        )
        return

    env_vars = parse_env_file_vars(str(env_path))

    console.print(f"\n[bold]Configuration for {chain}/{market}/{source_chain}[/bold]")
    console.print(f"File: {env_path}\n")

    # Display in sections
    console.print("[bold]Identity[/bold]")
    console.print(
        f"  Wallet Address: {env_vars.get('WALLET_HOLDER_ADDRESS', '[Not Set]')}"
    )
    console.print(
        f"  Signer Address: {env_vars.get('SIGNER_ACCOUNT_ADDRESS', '[Not Set]')}"
    )
    console.print(
        f"  Signer Private Key: {'[Set]' if env_vars.get('SIGNER_ACCOUNT_PRIVATE_KEY') else '[Not Set]'}"
    )

    console.print("\n[bold]RPC Configuration[/bold]")
    console.print(f"  Source RPC URL: {env_vars.get('SOURCE_RPC_URL', '[Not Set]')}")
    console.print(
        f"  Powerloom RPC URL: {env_vars.get('POWERLOOM_RPC_URL', '[Not Set]')}"
    )

    # Show other relevant configuration if present
    if "TELEGRAM_CHAT_ID" in env_vars or "TELEGRAM_REPORTING_URL" in env_vars:
        console.print("\n[bold]Notifications[/bold]")
        if "TELEGRAM_CHAT_ID" in env_vars:
            console.print(f"  Telegram Chat ID: {env_vars['TELEGRAM_CHAT_ID']}")
        if "TELEGRAM_REPORTING_URL" in env_vars:
            console.print(
                f"  Telegram Reporting URL: {env_vars['TELEGRAM_REPORTING_URL']}"
            )


@identity_app.command("delete")
def delete_identity(
    ctx: typer.Context,
    chain: str = typer.Option(
        ..., "--chain", "-c", help="Powerloom chain name (e.g., DEVNET, MAINNET)"
    ),
    market: str = typer.Option(
        ..., "--market", "-m", help="Data market name (e.g., UNISWAPV2)"
    ),
    source_chain: str = typer.Option(
        ..., "--source-chain", "-s", help="Source chain name (e.g., ETH-MAINNET)"
    ),
):
    """Delete a specific namespaced .env file."""
    # Normalize inputs for filename
    norm_chain = chain.lower()
    norm_market = market.lower()
    norm_source = source_chain.lower().replace("-", "_")

    env_filename = CONFIG_ENV_FILENAME_TEMPLATE.format(
        norm_chain, norm_market, norm_source
    )

    # First check in config directory
    env_path = CONFIG_DIR / env_filename

    # If not found in config directory, check current directory for backward compatibility
    if not env_path.exists():
        cwd_env_path = Path(os.getcwd()) / env_filename
        if cwd_env_path.exists():
            console.print(
                f"⚠️ Found legacy env file in current directory. Consider moving it to {CONFIG_DIR}",
                style="yellow",
            )
            env_path = cwd_env_path

    if not env_path.exists():
        console.print(
            f"No configuration found for {chain}/{market}/{source_chain}.",
            style="yellow",
        )
        return

    if typer.confirm(
        f"Are you sure you want to delete the configuration for {chain}/{market}/{source_chain}?"
    ):
        try:
            env_path.unlink()
            console.print(f"✅ Deleted configuration: {env_path}", style="green")
        except OSError as e:
            console.print(f"Error deleting configuration: {e}", style="bold red")
            raise typer.Exit(1)
