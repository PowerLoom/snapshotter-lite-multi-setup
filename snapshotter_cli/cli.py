import typer
import rich
from rich.console import Console
from rich.table import Table
from enum import Enum
from pathlib import Path
from typing import Optional, List

console = Console()
app = typer.Typer(
    name="powerloom",
    help="PowerLoom Snapshotter Node Management CLI",
    add_completion=False,
)

class Environment(str, Enum):
    MAINNET = "mainnet"
    STAGING = "staging"
    DEVNET = "devnet"

class DataMarket(str, Enum):
    AAVEV3 = "aavev3"
    UNISWAPV2 = "uniswapv2"

@app.command()
def diagnose(
    clean: bool = typer.Option(False, "--clean", "-c", help="Clean up existing deployments"),
    force: bool = typer.Option(False, "--force", "-f", help="Force cleanup without confirmation")
):
    """
    Run diagnostics on the system and optionally clean up existing deployments
    """
    console.print("🔍 Running system diagnostics...", style="bold blue")
    # TODO: Port diagnose.sh functionality here

@app.command()
def deploy(
    environment: Environment = typer.Option(..., "--env", "-e", help="Deployment environment"),
    data_markets: List[DataMarket] = typer.Option(None, "--market", "-m", help="Data markets to deploy"),
    slots: List[int] = typer.Option(None, "--slot", "-s", help="Specific slot IDs to deploy"),
):
    """
    Deploy snapshotter nodes for specified environment and data markets
    """
    console.print(f"🚀 Deploying to {environment.value}...", style="bold green")
    
    if not data_markets:
        data_markets = typer.prompt(
            "Select data markets (comma-separated)", 
            type=str,
            default="aavev3,uniswapv2"
        ).split(",")

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

if __name__ == "__main__":
    app()
