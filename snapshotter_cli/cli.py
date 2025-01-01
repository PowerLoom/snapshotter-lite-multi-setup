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


console = Console()

MARKETS_CONFIG_URL = "https://raw.githubusercontent.com/PowerLoom/curated-datamarkets/refs/heads/main/sources.json"

def fetch_markets_config() -> Dict:
    """Fetch markets configuration from GitHub"""
    try:
        response = requests.get(MARKETS_CONFIG_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        console.print(f"⚠️ Failed to fetch markets config: {e}", style="bold red")
        return dict()

def load_default_config(ctx: typer.Context):
    """Load default configuration and available markets"""
    ctx.ensure_object(dict)
    markets_config = fetch_markets_config()
    
    # Create chain-to-markets mapping
    chain_markets_map = {}
    for chain in markets_config:
        chain_name = chain["powerloomChain"]["name"].upper()
        chain_markets_map[chain_name] = {
            "chain_config": chain["powerloomChain"],
            "markets": {
                market["name"].upper(): market 
                for market in chain["dataMarkets"]
            }
        }
    
    # Store both the raw config and the organized mapping
    ctx.obj["markets_config"] = markets_config
    ctx.obj["chain_markets_map"] = chain_markets_map
    ctx.obj["available_environments"] = set(chain_markets_map.keys())
    ctx.obj["available_markets"] = {
        market_name 
        for chain_data in chain_markets_map.values() 
        for market_name in chain_data["markets"].keys()
    }

app = typer.Typer(
    name="powerloom",
    help="PowerLoom Snapshotter Node Management CLI",
    add_completion=False,
    callback=load_default_config
)

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
    slots: List[int] = typer.Option(None, "--slot", "-s", help="Specific slot IDs to deploy"),
):
    """
    Deploy snapshotter nodes for specified environment and data markets
    """
    chain_markets_map = ctx.obj["chain_markets_map"]
    
    # Validate environment
    env_config = next((chain for chain in ctx.obj["markets_config"] 
                      if chain["powerloomChain"]["name"].upper() == environment.upper()), None)
    if not env_config:
        console.print(f"❌ Invalid environment: {environment}", style="bold red")
        raise typer.Exit(1)
    
    console.print(f"🚀 Deploying to {environment}...", style="bold green")
    
    # Handle data markets selection
    available_markets = [m["name"] for m in env_config["dataMarkets"]]
    if not data_markets:
        markets_str = ",".join(available_markets)
        data_markets = typer.prompt(
            "Select data markets (comma-separated)", 
            type=str,
            default=markets_str
        ).split(",")
    
    # Validate selected markets
    for market in data_markets:
        if market.upper() not in [m.upper() for m in available_markets]:
            console.print(f"❌ Invalid market for {environment}: {market}", style="bold red")
            raise typer.Exit(1)
    
    # Here you can access full market configuration
    selected_markets = [
        market for market in env_config["dataMarkets"]
        if market["name"].upper() in [m.upper() for m in data_markets]
    ]
    
    # Use the market configurations for deployment
    for market in selected_markets:
        console.print(f"📦 Configuring {market['name']}...", style="bold blue")
        # Access market["compute"], market["config"], etc. for deployment

@app.command()
def configure(
    environment: Environment = typer.Option(..., "--env", "-e", help="Environment to configure"),
    reset: bool = typer.Option(False, "--reset", "-r", help="Reset existing configuration")
):
    """
    Configure environment settings and credentials
    """
    console.print(f"⚙️ Configuring {environment.value} environment...", style="bold yellow")

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
    chain_markets_map = ctx.obj["chain_markets_map"]
    
    # Create a tree for hierarchical display
    tree = Tree("🌐 [bold cyan]Available PowerLoom Chains[/]")
    
    for chain_name, chain_data in chain_markets_map.items():
        chain_config = chain_data["chain_config"]
        markets = chain_data["markets"]
        
        # Create chain branch with details
        chain_details = f"[bold green]{chain_name}[/] ([dim]Chain ID: {chain_config['chainId']}[/])"
        chain_branch = tree.add(chain_details)
        
        # Add markets under this chain
        for market_name, market_config in markets.items():
            market_details = (
                f"[bold blue]{market_name}[/] - "
                f"Source: [yellow]{market_config['sourceChain']}[/]"
            )
            market_branch = chain_branch.add(market_details)
            
            # Add compute and config details
            compute = market_config["compute"]
            config = market_config["config"]
            market_branch.add(f"[dim]Compute: {compute['repo']} ({compute['branch']})[/]")
            market_branch.add(f"[dim]Config: {config['repo']} ({config['branch']})[/]")
    
    # Print the tree
    console.print("\n")
    console.print(tree)
    console.print("\n")

if __name__ == "__main__":
    app()
