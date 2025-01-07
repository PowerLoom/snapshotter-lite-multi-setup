import os
import typer
from rich.console import Console
from rich.panel import Panel
from typing import Dict
from glob import glob
from snapshotter_cli.utils.models import CLIContext

console = Console()

# powerloomChainId_dataMarketName_sourceChainName
ENV_FILENAME_TEMPLATE = ".env-{}-{}-{}"

def configure_command(ctx: typer.Context):
    """Handle the configuration of environment settings and credentials"""
    cli_context: CLIContext = ctx.obj
    
    all_chains = [chain.powerloomChain.name
                 for chain in cli_context.markets_config]
    
    chain_list = "\n".join(
        f"[bold green]{i+1}.[/] [cyan]{chain}[/]" 
        for i, chain in enumerate(all_chains)
    )
    panel = Panel(
        chain_list,
        title="[bold blue]Available Chains[/]",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(panel)
    
    selection = typer.prompt("👉🏼 Select a chain (enter number or name)", type=str)
    
    if selection.isdigit():
        index = int(selection) - 1
        if 0 <= index < len(all_chains):
            selected_chain = all_chains[index]
        else:
            console.print("❌ Invalid selection number", style="bold red")
            raise typer.Exit(1)
    else:
        selected_chain = selection

    if selected_chain not in all_chains:
        console.print("❌ Invalid chain selection: ", style="bold red")
        raise typer.Exit(1)

    chain_config = next((chain for chain in cli_context.markets_config 
                      if chain.powerloomChain.name.upper() == selected_chain.upper()), None)
    
    console.print(f"🔎 Selected Chain details:", style="bold green")
    console.print(f"  Chain ID: {chain_config.powerloomChain.chainId}")
    console.print(f"  Chain Name: {chain_config.powerloomChain.name}")
    console.print(f"  Chain RPC URL: {chain_config.powerloomChain.rpcURL}")
    env_filename_pattern = ENV_FILENAME_TEMPLATE.format(
        chain_config.powerloomChain.chainId, 
        '*', 
        '*'
    )
    matching_env_files = glob(env_filename_pattern)
    
    if matching_env_files:
        console.print("🔑 Environment files already exist for this chain:", style="bold red")
        for env_file in matching_env_files:
            # extract the data market name and source chain name from the env file name
            env_file_name = os.path.basename(env_file)
            data_market_name = env_file_name.split('-')[2]
            source_chain_name = env_file_name.split('-')[3]
            console.print(f"  - {env_file} (Data Market: {data_market_name}, Source Chain: {source_chain_name})")
        raise typer.Exit(1)
    else:
        console.print("🔑 No existing environment files found for this chain", style="bold green")
