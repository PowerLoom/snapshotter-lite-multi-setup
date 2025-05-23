import os
import typer
import rich
from rich.console import Console
import requests
from typing import Dict, List, Optional
import json
from enum import Enum
from pathlib import Path
from .commands.diagnose import diagnose_command
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from .commands.configure import configure_command
from .commands.identity import identity_app, load_settings as load_user_identity_settings
from .utils.models import CLIContext, ChainConfig, ChainMarketData, MarketConfig, ComputeConfig, PowerloomChainConfig, UserSettings
from .utils.evm import fetch_owned_slots


console = Console()

MARKETS_CONFIG_URL = "https://raw.githubusercontent.com/PowerLoom/curated-datamarkets/refs/heads/feat/mainnet-devnet-add/sources.json"


def fetch_markets_config() -> List[PowerloomChainConfig]:
    """Fetch markets configuration from GitHub"""
    try:
        response = requests.get(MARKETS_CONFIG_URL)
        response.raise_for_status()
        raw_data = response.json()
        return [PowerloomChainConfig(**chain) for chain in raw_data]
    except Exception as e:
        console.print(f"⚠️ Failed to fetch markets config: {e}", style="bold red")
        return []

def load_default_config(ctx: typer.Context):
    """Load default configuration, available markets, and user settings"""
    markets_config = fetch_markets_config()
    user_settings = load_user_identity_settings()
    
    # Create chain-to-markets mapping
    chain_markets_map: Dict[str, ChainMarketData] = {}
    for chain in markets_config:
        chain_name = chain.powerloomChain.name.upper()
        chain_markets_map[chain_name] = ChainMarketData(
            chain_config=chain.powerloomChain,
            markets={
                market.name.upper(): market
                for market in chain.dataMarkets
            }
        )
    
    ctx.obj = CLIContext(
        markets_config=markets_config,
        chain_markets_map=chain_markets_map,
        available_environments=set(chain_markets_map.keys()),
        available_markets={
            market_name 
            for chain_data in chain_markets_map.values() 
            for market_name in chain_data.markets.keys()
        },
        user_settings=user_settings
    )

app = typer.Typer(
    name="powerloom",
    help="PowerLoom Snapshotter Node Management CLI",
    add_completion=False,
    callback=load_default_config,
    no_args_is_help=True
)

app.add_typer(identity_app, name="identity")

class Environment(str, Enum):
    pass

class DataMarket(str, Enum):
    pass

@app.command()
def diagnose(
    clean: bool = typer.Option(False, "--clean", "-c", help="Clean up existing deployments"),
    force: bool = typer.Option(False, "--force", "-f", help="Force cleanup without confirmation")
):
    """
    Run diagnostics on the system and optionally clean up existing deployments
    """
    diagnose_command(clean, force)

@app.command()
def deploy(
    ctx: typer.Context,
    environment: str = typer.Option(..., "--env", "-e", help="Deployment environment"),
    data_markets: List[str] = typer.Option(None, "--market", "-m", help="Data markets to deploy"),
    slots: Optional[List[int]] = typer.Option(None, "--slot", "-s", help="Specific slot IDs to deploy. If not provided, all owned slots will be used."),
    wallet_address: Optional[str] = typer.Option(None, "--wallet", "-w", help="Wallet address (0x...) holding the slots. Overrides configured identity and env var."),
    signer_address: Optional[str] = typer.Option(None, "--signer-address", help="Signer account address (0x...). Overrides configured identity and env var."),
    signer_key: Optional[str] = typer.Option(None, "--signer-key", help="Signer account private key. Overrides configured identity and env var. USE WITH CAUTION.", hide_input=True)
):
    """Deploy snapshotter nodes for specified environment and data markets"""
    cli_context: CLIContext = ctx.obj
    user_settings: UserSettings = cli_context.user_settings
    
    # Validate environment
    env_config = next((chain for chain in cli_context.markets_config 
                      if chain.powerloomChain.name.upper() == environment.upper()), None)
    if not env_config:
        console.print(f"❌ Invalid environment: {environment}", style="bold red")
        console.print(f"Available environments are: {', '.join(cli_context.available_environments)}")
        raise typer.Exit(1)
    
    console.print(f"🚀 Deploying to {environment}...", style="bold green")

    # Determine Wallet Holder Address
    final_wallet_address = wallet_address 
    if not final_wallet_address:
        final_wallet_address = os.getenv("WALLET_HOLDER_ADDRESS")
        if final_wallet_address:
            console.print(f"ℹ️ Using wallet holder address from WALLET_HOLDER_ADDRESS env var: {final_wallet_address}", style="dim")
        elif user_settings.wallet_address:
            final_wallet_address = user_settings.wallet_address
            console.print(f"ℹ️ Using wallet holder address from configured identity: {final_wallet_address}", style="dim")
        else:
            console.print("❌ Wallet Holder Address not provided or configured.", style="bold red")
            console.print("   Use --wallet, set WALLET_HOLDER_ADDRESS, or run 'snapshotter-cli identity set'.", style="yellow")
            raise typer.Exit(1)
    else:
        console.print(f"ℹ️ Using wallet holder address from --wallet option: {final_wallet_address}", style="dim")

    # Determine Signer Account Address
    final_signer_address = signer_address
    if not final_signer_address:
        final_signer_address = os.getenv("SIGNER_ACCOUNT_ADDRESS")
        if final_signer_address:
            console.print(f"ℹ️ Using signer address from SIGNER_ACCOUNT_ADDRESS env var: {final_signer_address}", style="dim")
        elif user_settings.signer_account_address:
            final_signer_address = user_settings.signer_account_address
            console.print(f"ℹ️ Using signer address from configured identity: {final_signer_address}", style="dim")
        else:
            console.print("❌ Signer Account Address not provided or configured.", style="bold red")
            console.print("   Use --signer-address, set SIGNER_ACCOUNT_ADDRESS, or run 'snapshotter-cli identity set'.", style="yellow")
            raise typer.Exit(1)
    else:
        console.print(f"ℹ️ Using signer address from --signer-address option: {final_signer_address}", style="dim")

    # Determine Signer Account Private Key
    final_signer_key = signer_key
    if not final_signer_key:
        final_signer_key = os.getenv("SIGNER_ACCOUNT_PRIVATE_KEY")
        if final_signer_key:
            console.print(f"ℹ️ Using signer private key from SIGNER_ACCOUNT_PRIVATE_KEY env var.", style="dim")
        elif user_settings.signer_account_private_key:
            final_signer_key = user_settings.signer_account_private_key
            console.print(f"ℹ️ Using signer private key from configured identity.", style="dim")
        else:
            console.print("❌ Signer Account Private Key not provided or configured.", style="bold red")
            console.print("   Use --signer-key, set SIGNER_ACCOUNT_PRIVATE_KEY, or run 'snapshotter-cli identity set'.", style="yellow")
            console.print("   [yellow]Warning: Passing private keys via CLI history or insecure environment variables can be risky.[/yellow]")
            raise typer.Exit(1)
    else:
        console.print(f"ℹ️ Using signer private key from --signer-key option.", style="dim")
        console.print("   [yellow]Warning: Passing private keys via CLI history can be risky.[/yellow]")

    # Fetch owned slots if specific slots are not provided
    deploy_slots: Optional[List[int]] = slots
    if not deploy_slots:
        console.print(f"ℹ️ No specific slots provided. Fetching all slots owned by {final_wallet_address} on {env_config.powerloomChain.name}...", style="dim")
        owned_slots = fetch_owned_slots(
            wallet_address=final_wallet_address,
            powerloom_chain_name=env_config.powerloomChain.name,
            rpc_url=env_config.powerloomChain.rpcURL
        )
        if owned_slots is None: # Error occurred during fetch
            console.print(f"❌ Could not fetch slots for wallet {final_wallet_address}. Please check errors above.", style="bold red")
            raise typer.Exit(1)
        if not owned_slots:
            console.print(f"🤷 No slots found for wallet {final_wallet_address} on {env_config.powerloomChain.name}. Nothing to deploy.", style="yellow")
            raise typer.Exit(0)
        deploy_slots = owned_slots
    
    if not deploy_slots:
        console.print(f"🤷 No slots to deploy. If you provided slots via --slot, check your input. Otherwise, no slots were found for the wallet.", style="yellow")
        raise typer.Exit(0)

    console.print(f"🎰 Targeting the following slots for deployment: {deploy_slots}", style="bold blue")
    console.print(f"🔑 Using Signer Address: {final_signer_address}", style="bold blue")
    # (Private key is not printed for security)

    # Handle data markets selection
    available_markets = [m.name for m in env_config.dataMarkets]
    if not data_markets:
        markets_str = ",".join(available_markets)
        data_markets = typer.prompt(
            "Select data markets (comma-separated)", 
            type=str,
            default=markets_str
        ).split(",")
    
    # Validate selected markets
    for market_name_raw in data_markets:
        market_name_upper = market_name_raw.strip().upper()
        if market_name_upper not in [m.upper() for m in available_markets]:
            console.print(f"❌ Invalid market for {environment}: {market_name_raw}", style="bold red")
            console.print(f"Available markets for {environment}: {', '.join(available_markets)}", style="yellow")
            raise typer.Exit(1)
    
    # Use the market configurations for deployment
    selected_markets_configs = [
        market_config for market_config in env_config.dataMarkets
        if market_config.name.upper() in [m.strip().upper() for m in data_markets]
    ]
    
    # Actual deployment loop will go here
    for market_conf in selected_markets_configs:
        console.print(f"📦 Processing market {market_conf.name}...", style="bold blue")
        for slot_id in deploy_slots:
            console.print(f"   🔩 Deploying slot {slot_id} for market {market_conf.name}...", style="green")
            # TODO: Here call a function similar to generate_env_file_contents and run_snapshotter_lite_v2
            # Pass: market_conf, slot_id, final_signer_address, final_signer_key, 
            #       env_config.powerloomChain.rpcURL, env_config.powerloomChain.name, etc.
            pass 

@app.command()
def configure(ctx: typer.Context):
    """
    Configure environment settings and credentials (Legacy - consider using 'identity set')
    """
    console.print("ℹ️  For wallet configuration, please use: [bold cyan]snapshotter-cli identity set[/bold cyan]")
    console.print(" This command is placeholder. For other configurations, direct file edit might be needed or expand this command.")

@app.command()
def status():
    """
    Show status of all deployed nodes
    """
    console.print("📊 Checking node status...", style="bold magenta")

@app.command()
def list(ctx: typer.Context):
    """
    Display available PowerLoom chains and their data markets
    """
    cli_context: CLIContext = ctx.obj
    chain_markets_map = cli_context.chain_markets_map
    
    # Create a tree for hierarchical display
    tree = Tree("🌐 [bold cyan]Available PowerLoom Chains[/]")
    
    for chain_name, chain_data in chain_markets_map.items():
        chain_config = chain_data.chain_config
        markets = chain_data.markets
        
        # Create chain branch with details
        chain_details = f"[bold green]{chain_name}[/] ([dim]Chain ID: {chain_config.chainId}[/])"
        chain_branch = tree.add(chain_details)
        
        # Add markets under this chain
        for market_name, market_config in markets.items():
            market_details = (
                f"[bold blue]{market_name}[/] - "
                f"Source: [yellow]{market_config.sourceChain}[/]"
            )
            market_branch = chain_branch.add(market_details)
            
            # Add compute and config details
            compute = market_config.compute
            config = market_config.config
            market_branch.add(f"[dim]Compute: {compute.repo} ({compute.branch})[/]")
            market_branch.add(f"[dim]Config: {config.repo} ({config.branch})[/]")
            if hasattr(market_config, 'sequencer') and market_config.sequencer:
                 market_branch.add(f"[dim]Sequencer: {market_config.sequencer}[/]")
            if hasattr(market_config, 'contractAddress') and market_config.contractAddress:
                 market_branch.add(f"[dim]Market Contract: {market_config.contractAddress}[/]")
            if hasattr(market_config, 'powerloomProtocolStateContractAddress') and market_config.powerloomProtocolStateContractAddress:
                 market_branch.add(f"[dim]Market Protocol State: {market_config.powerloomProtocolStateContractAddress}[/]")
    
    # Print the tree
    console.print("\n")
    console.print(tree)
    console.print("\n")

if __name__ == "__main__":
    app()
