import typer
from rich.console import Console
import json
from pathlib import Path
from typing import Optional, List, cast
import os

from ..utils.models import UserSettings, ChainSpecificIdentity, CLIContext # Updated imports

console = Console()

APP_NAME = "snapshotter-cli"
CONFIG_FILE_NAME = "settings.json"

# --- Configuration file helpers ---
def get_config_file_path() -> Path:
    app_dir = Path(typer.get_app_dir(APP_NAME, force_posix=True))
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir / CONFIG_FILE_NAME

def load_settings() -> UserSettings:
    config_file = get_config_file_path()
    if config_file.exists():
        try:
            settings_data = json.loads(config_file.read_text())
            # Handle potential old format if necessary during migration, or just load new
            return UserSettings(**settings_data)
        except json.JSONDecodeError:
            console.print(f"[yellow]Warning: Config file {config_file} is corrupted. Using defaults.[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load config from {config_file}: {e}. Using defaults.[/yellow]")
    return UserSettings()

def save_settings(settings: UserSettings):
    config_file = get_config_file_path()
    try:
        config_file.write_text(settings.model_dump_json(indent=4))
        os.chmod(config_file, 0o600)
        console.print(f"💾 Settings saved to {config_file} (permissions restricted)", style="green")
    except Exception as e:
        console.print(f"[bold red]Error saving settings to {config_file}: {e}[/bold red]")

# --- Typer Application for Identity Management ---
identity_app = typer.Typer(
    name="identity",
    help="Manage chain-specific user identities and source RPC configurations.",
    no_args_is_help=True
)

# --- Helper for chain validation ---
def get_valid_chain_names(ctx: typer.Context) -> List[str]:
    # Ascend to the main app context to get available_environments
    main_app_ctx = ctx
    while main_app_ctx.parent is not None:
        main_app_ctx = main_app_ctx.parent
    
    cli_context = cast(CLIContext, main_app_ctx.obj)
    if not cli_context or not cli_context.available_environments:
        # This might happen if called in a weird context or before full app load.
        # For `identity set` with prompt, this is less ideal.
        # Consider alternative ways to get this if it becomes an issue (e.g. re-fetch sources.json limitedly)
        console.print("[yellow]Warning: Could not determine available Powerloom chains. Validation might be skipped.[/yellow]")
        return [] # Or raise an error, or fetch if absolutely necessary
    return sorted(list(cli_context.available_environments))

# --- Identity Commands ---
@identity_app.command("set")
def set_identity(
    ctx: typer.Context,
    chain_name_input: str = typer.Option(
        ..., 
        "--chain", "-c", 
        help="The Powerloom chain name (e.g., DEVNET, MAINNET) for which to set the identity.",
        prompt="Enter the Powerloom chain name (e.g., DEVNET, MAINNET)"
    ),
    wallet_address: Optional[str] = typer.Option(None, prompt="Wallet Holder Address (0x...) [leave blank to keep current/unset]", help="Wallet that owns the slots.", show_default=False),
    signer_address: Optional[str] = typer.Option(None, prompt="Signer Account Address (0x...) [leave blank to keep current/unset]", help="Address that signs transactions.", show_default=False),
    signer_private_key: Optional[str] = typer.Option(None, prompt="Signer Private Key (0x...) [leave blank to keep current/unset]", help="Private key for signer. WILL BE STORED LOCALLY.", hide_input=True, show_default=False),
):
    """
    Set/update wallet and signer details for a specific Powerloom chain.
    Stores information in the CLI's configuration file.
    """
    settings = load_settings()
    chain_name = chain_name_input.upper()
    
    valid_chains = get_valid_chain_names(ctx)
    if valid_chains and chain_name not in valid_chains:
        console.print(f"[bold red]Error: Invalid chain name '{chain_name}'. Valid chains are: {', '.join(valid_chains)}[/bold red]")
        raise typer.Exit(1)

    if chain_name not in settings.chain_identities:
        settings.chain_identities[chain_name] = ChainSpecificIdentity()
    
    chain_identity = settings.chain_identities[chain_name]
    updated_fields = []

    if wallet_address and wallet_address.strip():
        if not wallet_address.startswith("0x") or len(wallet_address) != 42:
            console.print("[red]Invalid Wallet Holder address format.[/red]"); raise typer.Exit(1)
        chain_identity.wallet_address = wallet_address
        updated_fields.append("Wallet Holder Address")
    elif wallet_address == "": # Explicitly clearing
        chain_identity.wallet_address = None
        updated_fields.append("Wallet Holder Address (cleared)")

    if signer_address and signer_address.strip():
        if not signer_address.startswith("0x") or len(signer_address) != 42:
            console.print("[red]Invalid Signer Address format.[/red]"); raise typer.Exit(1)
        chain_identity.signer_account_address = signer_address
        updated_fields.append("Signer Address")
    elif signer_address == "":
        chain_identity.signer_account_address = None
        updated_fields.append("Signer Address (cleared)")

    if signer_private_key and signer_private_key.strip():
        pk_to_validate = signer_private_key[2:] if signer_private_key.startswith("0x") else signer_private_key
        if not all(c in "0123456789abcdefABCDEF" for c in pk_to_validate) or len(pk_to_validate) != 64:
            console.print("[red]Invalid Signer Private Key format.[/red]"); raise typer.Exit(1)
        chain_identity.signer_account_private_key = signer_private_key
        updated_fields.append("Signer Private Key")
        console.print(f"[yellow]⚠️ Signer Private Key for {chain_name} will be stored in plain text in {get_config_file_path()}[/yellow]")
    elif signer_private_key == "":
        chain_identity.signer_account_private_key = None
        updated_fields.append("Signer Private Key (cleared)")

    if not updated_fields:
        console.print(f"No changes made to identity for chain '{chain_name}'.")
        return

    save_settings(settings)
    console.print(f"✅ Identity for chain [bold magenta]{chain_name}[/bold magenta] updated fields: {', '.join(updated_fields)}", style="green")

@identity_app.command("show")
def show_identity(
    ctx: typer.Context, # Added context to potentially get valid chains
    chain_name_input: Optional[str] = typer.Option(None, "--chain", "-c", help="Show identity for a specific Powerloom chain name.")
):
    """
    Display configured identities and source RPCs, optionally for a specific chain.
    Also shows relevant environment variables.
    """
    settings = load_settings()
    target_chain_name = chain_name_input.upper() if chain_name_input else None

    console.print("--- Configured Identities (settings.json) ---", style="bold underline")
    if not settings.chain_identities and not target_chain_name:
        console.print(" No Powerloom chain identities configured. Use 'identity set --chain <chain_name>'.")
    
    displayed_specific_chain_identity = False
    if settings.chain_identities:
        for chain_name_key, identity in sorted(settings.chain_identities.items()):
            if target_chain_name and chain_name_key != target_chain_name:
                continue
            displayed_specific_chain_identity = True
            console.print(f"\n📜 Powerloom Chain: [bold magenta]{chain_name_key}[/bold magenta]")
            console.print(f"  👤 Wallet Holder: [cyan]{identity.wallet_address or '[Not Set]'}[/cyan]")
            console.print(f"  ✍️  Signer Address: [cyan]{identity.signer_account_address or '[Not Set]'}[/cyan]")
            console.print(f"  🔑 Signer Private Key: [green]{'Set (not displayed)' if identity.signer_account_private_key else '[Not Set]'}[/green]")
    
    if target_chain_name and not displayed_specific_chain_identity:
        console.print(f" No identity configured for Powerloom chain '{target_chain_name}'. Use 'identity set --chain {target_chain_name}'.")

    console.print("\n--- Configured Source Chain RPCs (settings.json) ---", style="bold underline")
    if not settings.source_chain_rpcs:
        console.print(" No source chain RPCs configured. Use 'identity set-source-rpc'.")
    else:
        for src_chain, rpc_url in sorted(settings.source_chain_rpcs.items()):
            console.print(f"  🔗 Source Chain [bold yellow]{src_chain}[/bold yellow]: [blue]{rpc_url}[/blue]")

    # Environment Variables Section (General - not chain specific display for now)
    console.print("\n--- Environment Variables (Global & Chain-Specific Fallbacks) ---", style="bold underline")
    # General guidance, specific checks are done by get_credential in cli.py
    console.print(" Check for variables like:")
    console.print("   POWERLOOM_<CHAIN>_WALLET_HOLDER_ADDRESS, POWERLOOM_WALLET_HOLDER_ADDRESS")
    console.print("   POWERLOOM_<CHAIN>_SIGNER_ACCOUNT_ADDRESS, POWERLOOM_SIGNER_ACCOUNT_ADDRESS")
    console.print("   POWERLOOM_<CHAIN>_SIGNER_ACCOUNT_PRIVATE_KEY, POWERLOOM_SIGNER_ACCOUNT_PRIVATE_KEY")
    console.print("   POWERLOOM_SOURCE_RPC_<SOURCE_CHAIN_NAME> (e.g., POWERLOOM_SOURCE_RPC_ETH_MAINNET)")

    console.print("\n--- Resolution Priority for Credentials (e.g., in 'deploy') ---")
    console.print("1. Command-line options (e.g., --wallet, --signer-address)")
    console.print("2. Chain-specific Environment Variables (e.g., POWERLOOM_DEVNET_WALLET_HOLDER_ADDRESS)")
    console.print("3. Global Environment Variables (e.g., POWERLOOM_WALLET_HOLDER_ADDRESS)")
    console.print("4. Configured Identity for the specific chain (from settings.json via 'identity set')")
    console.print("   (For Source RPCs: Env Var POWERLOOM_SOURCE_RPC_<SOURCE_CHAIN> > settings.json)")

@identity_app.command("set-source-rpc")
def set_source_rpc(
    source_chain_name: str = typer.Option(..., "--source-chain", "-s", help="Name of the source chain (e.g., ETH-MAINNET, POLYGON-MAINNET). Case-insensitive.", prompt=True),
    rpc_url: str = typer.Option(..., "--rpc-url", "-u", help="The RPC URL for this source chain.", prompt=True)
):
    """
    Set and save the RPC URL for a specific source chain.
    This is used by the deploy command to connect to chains like Ethereum Mainnet.
    """
    settings = load_settings()
    # Normalize source_chain_name, e.g., to uppercase or a specific casing if needed by other parts of the system
    norm_source_chain_name = source_chain_name.strip().upper() # Example: ETH-MAINNET
    if not norm_source_chain_name or not rpc_url.strip().startswith("http"):
        console.print("[red]Error: Source chain name must be non-empty and RPC URL must start with http(s).[/red]")
        raise typer.Exit(1)

    settings.source_chain_rpcs[norm_source_chain_name] = rpc_url.strip()
    save_settings(settings)
    console.print(f"✅ RPC URL for source chain [bold yellow]{norm_source_chain_name}[/bold yellow] set to: [blue]{rpc_url.strip()}[/blue]", style="green")

@identity_app.command("set-default-chain")
def set_default_chain_for_identity(
    ctx: typer.Context,
    chain_name_input: str = typer.Option(
        ..., 
        "--chain", "-c", 
        help="The Powerloom chain name to set as default for identity lookups.",
        prompt="Enter the Powerloom chain name to set as default (e.g., DEVNET, MAINNET)"
    )
):
    """
    Set a default Powerloom chain for identity lookups when a specific chain isn't targeted.
    """
    settings = load_settings()
    chain_name = chain_name_input.upper()

    valid_chains = get_valid_chain_names(ctx)
    if not valid_chains: # Should ideally not happen if main app callback ran
        console.print("[red]Error: Could not determine available chains. Cannot set default.[/red]")
        raise typer.Exit(1)
        
    if chain_name not in valid_chains:
        console.print(f"[bold red]Error: Invalid chain name '{chain_name}'. Valid chains are: {', '.join(valid_chains)}[/bold red]")
        raise typer.Exit(1)
    
    if chain_name not in settings.chain_identities or not settings.chain_identities[chain_name].wallet_address:
        console.print(f"[yellow]Warning: No complete identity (at least wallet address) is set for chain '{chain_name}'.[/yellow]")
        console.print(f"  You can still set it as default, but it might not be usable until configured via 'identity set --chain {chain_name}'.")

    settings.default_chain_for_identity = chain_name
    save_settings(settings)
    console.print(f"✅ Default chain for identity lookups set to: [bold magenta]{chain_name}[/bold magenta]", style="green")


@identity_app.command("show-default-chain")
def show_default_chain_for_identity():
    """
    Display the currently configured default Powerloom chain for identity lookups.
    """
    settings = load_settings()
    if settings.default_chain_for_identity:
        console.print(f"🏷️ Default chain for identity: [bold magenta]{settings.default_chain_for_identity}[/bold magenta]")
    else:
        console.print(" No default chain for identity is set. Use 'snapshotter-cli identity set-default-chain'.")


if __name__ == "__main__":
    console.print("Run this module via the main CLI: snapshotter-cli identity ...") 