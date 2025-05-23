import typer
from rich.console import Console
import json
from pathlib import Path
from typing import Optional
import os # Import os to access environment variables

from ..utils.models import UserSettings # Will be created in models.py

console = Console()

APP_NAME = "snapshotter-cli"
CONFIG_FILE_NAME = "settings.json"

def get_config_file_path() -> Path:
    app_dir = Path(typer.get_app_dir(APP_NAME, force_posix=True)) # force_posix for consistency in tests/dev if needed
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir / CONFIG_FILE_NAME

def load_settings() -> UserSettings:
    config_file = get_config_file_path()
    if config_file.exists():
        try:
            settings_data = json.loads(config_file.read_text())
            return UserSettings(**settings_data)
        except json.JSONDecodeError:
            console.print(f"[yellow]Warning: Configuration file at {config_file} is corrupted. Using defaults.[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load configuration from {config_file}: {e}. Using defaults.[/yellow]")
    return UserSettings()

def save_settings(settings: UserSettings):
    config_file = get_config_file_path()
    try:
        config_file.write_text(settings.model_dump_json(indent=4))
        # Ensure the config file has restricted permissions if it contains sensitive data
        os.chmod(config_file, 0o600) # Read/Write for owner only
        console.print(f"💾 Settings saved to {config_file} (permissions restricted)", style="green")
    except Exception as e:
        console.print(f"[bold red]Error saving settings to {config_file}: {e}[/bold red]")

identity_app = typer.Typer(
    name="identity",
    help="Manage Snapshotter CLI user identity (e.g., wallet, signer keys).",
    no_args_is_help=True
)

@identity_app.command("set")
def set_identity(
    wallet_address: Optional[str] = typer.Option(
        None, # Default to None, prompt if not provided
        prompt="Please enter your EVM wallet address (0x...) that owns the slots (leave blank to keep current)",
        help="The EVM wallet address (0x...) that owns the snapshotter slots.",
        show_default=False # Don't show default in help if it's None and we prompt
    ),
    signer_address: Optional[str] = typer.Option(
        None, 
        prompt="Please enter your Signer Account address (0x...) (leave blank to keep current)",
        help="The Signer Account address used to sign transactions for the snapshotter.",
        show_default=False
    ),
    signer_private_key: Optional[str] = typer.Option(
        None, 
        prompt="Please enter your Signer Account private key (0x...) (leave blank to keep current)",
        help="The private key for the Signer Account. WILL BE STORED LOCALLY.",
        hide_input=True, # Hide input for private key
        show_default=False
    )
):
    """
    Set and save your primary EVM wallet address, signer address, and signer private key.
    Values are stored in a local configuration file.
    """
    settings = load_settings()
    changed_fields = []

    if wallet_address:
        if not wallet_address.startswith("0x") or len(wallet_address) != 42:
            console.print("[bold red]Invalid wallet address format. It should start with '0x' and be 42 characters long.[/bold red]")
            raise typer.Exit(code=1)
        settings.wallet_address = wallet_address
        changed_fields.append("Wallet Holder Address")

    if signer_address:
        if not signer_address.startswith("0x") or len(signer_address) != 42:
            console.print("[bold red]Invalid signer address format. It should start with '0x' and be 42 characters long.[/bold red]")
            raise typer.Exit(code=1)
        settings.signer_account_address = signer_address
        changed_fields.append("Signer Account Address")

    if signer_private_key:
        # Basic validation for private key (hex, 64 chars, optionally 0x prefixed)
        pk_to_validate = signer_private_key[2:] if signer_private_key.startswith("0x") else signer_private_key
        if not all(c in "0123456789abcdefABCDEF" for c in pk_to_validate) or len(pk_to_validate) != 64:
            console.print("[bold red]Invalid signer private key format. It should be a 64-character hex string (optionally 0x-prefixed).[/bold red]")
            raise typer.Exit(code=1)
        settings.signer_account_private_key = signer_private_key
        changed_fields.append("Signer Account Private Key")
        console.print("[yellow]⚠️  Signer private key will be stored in plain text in the local configuration file.[/yellow]")
        console.print(f"   Ensure the file ({get_config_file_path()}) is adequately protected.")

    if not changed_fields:
        console.print("No changes were made to the identity settings.")
        return

    save_settings(settings)
    console.print(f"✅ Following identity fields updated: {', '.join(changed_fields)}", style="bold green")

@identity_app.command("show")
def show_identity():
    """
    Display the configured identity and relevant environment variables.
    """
    settings = load_settings()
    env_wallet_address = os.getenv("WALLET_HOLDER_ADDRESS")
    env_signer_address = os.getenv("SIGNER_ACCOUNT_ADDRESS")
    # We don't show env_signer_private_key for security

    console.print("--- Identity Configuration ---", style="bold underline")

    # Configured Wallet Holder
    if settings.wallet_address:
        console.print(f"👤 Wallet Holder (settings.json): [bold cyan]{settings.wallet_address}[/bold cyan]")
    else:
        console.print(" Wallet Holder (settings.json): [yellow]Not set.[/yellow]")

    # Configured Signer Address
    if settings.signer_account_address:
        console.print(f"✍️  Signer Address (settings.json): [bold cyan]{settings.signer_account_address}[/bold cyan]")
    else:
        console.print(" Signer Address (settings.json): [yellow]Not set.[/yellow]")
    
    # Note about Signer Private Key (not displayed)
    if settings.signer_account_private_key:
        console.print("🔑 Signer Private Key (settings.json): [green]Set (not displayed for security)[/green]")
    else:
        console.print(" Signer Private Key (settings.json): [yellow]Not set.[/yellow]")

    console.print("\n--- Environment Variables ---")
    # Env Wallet Holder
    if env_wallet_address:
        console.print(f"🌍 WALLET_HOLDER_ADDRESS: [bold blue]{env_wallet_address}[/bold blue]")
    else:
        console.print(" WALLET_HOLDER_ADDRESS: [yellow]Not set.[/yellow]")
    
    # Env Signer Address
    if env_signer_address:
        console.print(f"🌍 SIGNER_ACCOUNT_ADDRESS: [bold blue]{env_signer_address}[/bold blue]")
    else:
        console.print(" SIGNER_ACCOUNT_ADDRESS: [yellow]Not set.[/yellow]")
    console.print("   (SIGNER_ACCOUNT_PRIVATE_KEY env var is checked by commands but not displayed here for security)")
    
    console.print("\n--- Resolution Priority for Commands (e.g., deploy) ---")
    console.print("1. Command-line options (e.g., --wallet, --signer-address, --signer-key)")
    console.print("2. Environment variables (e.g., WALLET_HOLDER_ADDRESS, SIGNER_ACCOUNT_ADDRESS, SIGNER_ACCOUNT_PRIVATE_KEY)")
    console.print("3. Configured Identity (from settings.json via 'identity set')")

    if not settings.wallet_address and not env_wallet_address:
        console.print("\n[yellow]Hint: Wallet Holder Address is not configured. Use 'identity set' or set WALLET_HOLDER_ADDRESS.[/yellow]")
    if not settings.signer_account_address and not env_signer_address:
        console.print("[yellow]Hint: Signer Account Address is not configured. Use 'identity set' or set SIGNER_ACCOUNT_ADDRESS.[/yellow]")

if __name__ == "__main__":
    # Example for direct testing
    # typer.run(set_identity) # Test set
    # typer.run(show_identity) # Test show
    console.print("Run this module via the main CLI: snapshotter-cli identity ...") 