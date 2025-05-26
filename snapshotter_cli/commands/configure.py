import os
import typer
from rich.console import Console
from rich.panel import Panel
from typing import Dict, List, Optional
from glob import glob
from pathlib import Path
from snapshotter_cli.utils.models import CLIContext, MarketConfig, PowerloomChainConfig, UserSettings, ChainSpecificIdentity
from snapshotter_cli.utils.config_helpers import get_credential, get_source_chain_rpc_url

console = Console()

ENV_FILENAME_TEMPLATE = ".env.{}.{}.{}" # e.g. .env.devnet.uniswapv2.eth-mainnet

def parse_env_file_vars(file_path: str) -> Dict[str, str]:
    """Parses a .env file and returns a dictionary of key-value pairs."""
    env_vars = {}
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars

def get_default_env_vars() -> Dict[str, str]:
    """Loads default .env variables from env.example in the project root."""
    # Assuming env.example is in the parent directory of snapshotter_cli
    project_root = Path(__file__).resolve().parent.parent.parent 
    env_example_path = project_root / "env.example"
    return parse_env_file_vars(str(env_example_path))


def configure_command(ctx: typer.Context):
    """Configure a namespaced .env file for a specific chain and data market."""
    cli_context: CLIContext = ctx.obj
    user_settings: UserSettings = cli_context.user_settings
    
    all_powerloom_chains = cli_context.markets_config
    
    if not all_powerloom_chains:
        console.print("❌ No Powerloom chains found in the configuration. Cannot proceed.", style="bold red")
        raise typer.Exit(1)

    chain_list_display = "\n".join(
        f"[bold green]{i+1}.[/] [cyan]{chain.powerloomChain.name}[/]" 
        for i, chain in enumerate(all_powerloom_chains)
    )
    panel = Panel(
        chain_list_display,
        title="[bold blue]Available Powerloom Chains[/]",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(panel)
    
    selected_chain_name_input = typer.prompt("👉🏼 Select a Powerloom chain (enter number or name)", type=str)
    
    selected_powerloom_chain_config: Optional[PowerloomChainConfig] = None
    if selected_chain_name_input.isdigit():
        index = int(selected_chain_name_input) - 1
        if 0 <= index < len(all_powerloom_chains):
            selected_powerloom_chain_config = all_powerloom_chains[index]
        else:
            console.print("❌ Invalid selection number for Powerloom chain.", style="bold red")
            raise typer.Exit(1)
    else:
        selected_powerloom_chain_config = next((chain for chain in all_powerloom_chains 
                                             if chain.powerloomChain.name.upper() == selected_chain_name_input.upper()), None)

    if not selected_powerloom_chain_config:
        console.print(f"❌ Powerloom chain '{selected_chain_name_input}' not found.", style="bold red")
        raise typer.Exit(1)

    chain_name_upper = selected_powerloom_chain_config.powerloomChain.name.upper()
    console.print(f"✅ Selected Powerloom Chain: [bold cyan]{selected_powerloom_chain_config.powerloomChain.name}[/bold cyan]")

    # --- Prompt for Data Market ---
    available_markets_for_chain = selected_powerloom_chain_config.dataMarkets
    if not available_markets_for_chain:
        console.print(f"🤷 No data markets found for chain {selected_powerloom_chain_config.powerloomChain.name}.", style="yellow")
        raise typer.Exit(0)

    market_list_display = "\n".join(
        f"[bold green]{i+1}.[/] [cyan]{market.name}[/] ([dim]Source: {market.sourceChain}[/])"
        for i, market in enumerate(available_markets_for_chain)
    )
    market_panel = Panel(
        market_list_display,
        title=f"[bold blue]Available Data Markets on {selected_powerloom_chain_config.powerloomChain.name}[/]",
        border_style="blue",
        padding=(1,2)
    )
    console.print(market_panel)

    selected_market_name_input = typer.prompt("👉🏼 Select a Data Market (enter number or name)", type=str)
    selected_market_config: Optional[MarketConfig] = None

    if selected_market_name_input.isdigit():
        market_idx = int(selected_market_name_input) - 1
        if 0 <= market_idx < len(available_markets_for_chain):
            selected_market_config = available_markets_for_chain[market_idx]
        else:
            console.print("❌ Invalid selection number for Data Market.", style="bold red")
            raise typer.Exit(1)
    else:
        selected_market_config = next((market for market in available_markets_for_chain
                                       if market.name.upper() == selected_market_name_input.upper()), None)
    
    if not selected_market_config:
        console.print(f"❌ Data Market '{selected_market_name_input}' not found on {selected_powerloom_chain_config.powerloomChain.name}.", style="bold red")
        raise typer.Exit(1)

    console.print(f"✅ Selected Data Market: [bold cyan]{selected_market_config.name}[/bold cyan] (Source: {selected_market_config.sourceChain})")

    # --- Determine Filename and Path ---
    # Normalize names for filename (e.g. lower, replace spaces/special chars if any, though names are usually clean)
    norm_chain_name = selected_powerloom_chain_config.powerloomChain.name.lower()
    norm_market_name = selected_market_config.name.lower()
    norm_source_chain_name = selected_market_config.sourceChain.lower().replace('-', '_') # e.g. eth_mainnet
    
    env_filename = ENV_FILENAME_TEMPLATE.format(norm_chain_name, norm_market_name, norm_source_chain_name)
    # Assume project root is where the snapshotter-cli is run from, or where settings.json would be.
    # For simplicity, let's assume the current working directory.
    env_file_path = Path(os.getcwd()) / env_filename
    
    console.print(f"ℹ️  The configuration will be saved to: [bold yellow]{env_file_path}[/bold yellow]")

    # --- Load base template and existing specific config (if any) ---
    default_env_vars = get_default_env_vars()
    if not default_env_vars:
        console.print("⚠️ Could not load 'env.example'. Using an empty template.", style="yellow")
    
    existing_specific_env_vars = parse_env_file_vars(str(env_file_path))
    
    if existing_specific_env_vars:
        console.print(f"🔍 Found existing configuration at [bold yellow]{env_file_path}[/bold yellow].")
        overwrite = typer.confirm("Do you want to overwrite/update it?", default=True)
        if not overwrite:
            console.print("Skipping configuration update.", style="dim")
            raise typer.Exit(0)
    
    output_env_vars: Dict[str, str] = {}
    configured_chain_identity = user_settings.chain_identities.get(chain_name_upper)

    # --- Interactive Prompting ---
    console.print(f"⚙️ Please provide values for the {env_filename} configuration. Press Enter to keep default/current.", style="bold blue")

    # Key order from env.example is preferred, but it's a dict, so we iterate over a fixed list
    # or keys from default_env_vars (which should maintain order if Python >= 3.7)
    keys_to_configure = list(default_env_vars.keys()) 
    # Add any keys from an existing specific file that might not be in env.example (legacy or custom)
    for k in existing_specific_env_vars.keys():
        if k not in keys_to_configure:
            keys_to_configure.append(k)
    if not keys_to_configure and not default_env_vars: # if env.example was empty and no existing file
         console.print("🤷 No keys to configure (env.example might be empty or missing).", style="yellow")
         raise typer.Exit(1)


    for key in keys_to_configure:
        default_value = default_env_vars.get(key, "") # Default from env.example
        current_value = existing_specific_env_vars.get(key, default_value) # Current from specific file, or default
        prompt_message_rich = f"  Enter value for [green]{key}[/green]"
        
        # Pre-fill with resolved credentials where applicable
        prefilled_value = None
        if key == "WALLET_HOLDER_ADDRESS":
            prefilled_value = get_credential("WALLET_HOLDER_ADDRESS", chain_name_upper, None, configured_chain_identity)
        elif key == "SIGNER_ACCOUNT_ADDRESS":
            prefilled_value = get_credential("SIGNER_ACCOUNT_ADDRESS", chain_name_upper, None, configured_chain_identity)
        elif key == "SIGNER_ACCOUNT_PRIVATE_KEY":
            prefilled_value = get_credential("SIGNER_ACCOUNT_PRIVATE_KEY", chain_name_upper, None, configured_chain_identity)
        elif key == "SOURCE_RPC_URL": # This should be specific to the market's source chain
             prefilled_value = get_source_chain_rpc_url(selected_market_config.sourceChain, user_settings)
        elif key == "POWERLOOM_RPC_URL": # This should be specific to the selected Powerloom chain
            prefilled_value = str(selected_powerloom_chain_config.powerloomChain.rpcURL)

        if prefilled_value:
            current_value = prefilled_value # Prioritize identity/market config over existing file content for prompt
            prompt_message_rich += f" (default from identity/market: [cyan]{'(hidden for private key)' if 'PRIVATE_KEY' in key and prefilled_value else prefilled_value}[/cyan])"
        elif current_value:
             prompt_message_rich += f" (current: [cyan]{'(hidden for private key)' if 'PRIVATE_KEY' in key and current_value else current_value}[/cyan])"
        else:
            prompt_message_rich += " (no current value)"

        is_sensitive = "PRIVATE_KEY" in key
        
        # Print the Rich-formatted prompt first
        console.print(prompt_message_rich, end=" ")
        # Then use Typer prompt with a minimal actual prompt string, using default for display
        user_input = typer.prompt("", default=current_value if not is_sensitive else "(hidden)", hide_input=is_sensitive, show_default=not is_sensitive)
        
        if is_sensitive and user_input == "(hidden)" and current_value:
            # If sensitive and user effectively chose the default (which was displayed as "(hidden)")
            output_env_vars[key] = current_value
        elif is_sensitive and not user_input and current_value: # User pressed enter on sensitive field with existing value, typer returns empty string
            output_env_vars[key] = current_value
        else:
            output_env_vars[key] = user_input

    # --- Write Configuration File ---
    try:
        with open(env_file_path, 'w') as f:
            f.write(f"# Configuration for Powerloom Chain: {selected_powerloom_chain_config.powerloomChain.name}\n")
            f.write(f"# Data Market: {selected_market_config.name} (Source: {selected_market_config.sourceChain})\n")
            f.write(f"# Generated by snapshotter-cli configure\n\n")
            for k, v in output_env_vars.items():
                f.write(f"{k}={v}\n")
        console.print(f"✅ Successfully generated/updated configuration: [bold green]{env_file_path}[/bold green]", style="green")
    except IOError as e:
        console.print(f"❌ Error writing configuration file: {e}", style="bold red")
        raise typer.Exit(1)
