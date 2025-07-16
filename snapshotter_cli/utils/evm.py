import json
from pathlib import Path
from typing import List, Optional

from rich.console import Console

console = Console()


ABI_DIR = Path(__file__).parent / "abi"  # ABI folder is at snapshotter_cli/utils/abi

def fetch_owned_slots(
    wallet_address: str,
    powerloom_chain_name: str,
    rpc_url: str,
    protocol_state_contract_address: Optional[str] = None,
) -> Optional[List[int]]:
    """
    Fetches the slot IDs owned by a given wallet address on a Powerloom chain.
    """
    if not wallet_address:
        console.print("[bold red]Error: Wallet address not provided or found.[/bold red]")
        return None

    if not rpc_url:
        console.print("[bold red]Error: Powerloom RPC URL not provided.[/bold red]")
        return None

    if not protocol_state_contract_address:
        console.print("[bold red]Error: Protocol State Contract address not provided.[/bold red]")
        return None

    try:
        from web3 import Web3
        
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            console.print(f"[bold red]Error: Failed to connect to Powerloom RPC URL: {rpc_url}[/bold red]")
            return None
        
        # Load ABIs
        protocol_state_abi_path = ABI_DIR / "ProtocolState.json"
        powerloom_nodes_abi_path = ABI_DIR / "PowerloomNodes.json"

        if not protocol_state_abi_path.exists() or not powerloom_nodes_abi_path.exists():
            console.print(f"[bold red]Error: ABI files not found in {ABI_DIR}. Make sure ProtocolState.json and PowerloomNodes.json are present.[/bold red]")
            return None

        with open(protocol_state_abi_path, 'r') as f:
            protocol_state_abi = json.load(f)
        with open(powerloom_nodes_abi_path, 'r') as f:
            powerloom_nodes_abi = json.load(f)

        # Get ProtocolState contract
        checksum_protocol_state_address = w3.to_checksum_address(protocol_state_contract_address)
        protocol_state_contract = w3.eth.contract(
            address=checksum_protocol_state_address,
            abi=protocol_state_abi,
        )

        # Get SnapshotterState (PowerloomNodes) contract address from ProtocolState
        snapshotter_state_address = protocol_state_contract.functions.snapshotterState().call()
        checksum_snapshotter_state_address = w3.to_checksum_address(snapshotter_state_address)

        # Get PowerloomNodes contract
        powerloom_nodes_contract = w3.eth.contract(
            address=checksum_snapshotter_state_address,
            abi=powerloom_nodes_abi,
        )

        # Fetch user slots
        checksum_wallet_address = w3.to_checksum_address(wallet_address)
        slot_ids = powerloom_nodes_contract.functions.getUserOwnedNodeIds(checksum_wallet_address).call()

        if not slot_ids:
            console.print(f"No slots found for wallet address {wallet_address} on {powerloom_chain_name}.")
            return []
        
        console.print(f"Found {len(slot_ids)} slots for wallet {wallet_address} on {powerloom_chain_name}: {slot_ids}", style="green")
        return slot_ids

    except Exception as e:
        console.print(f"[bold red]Error fetching slots: {e}[/bold red]")
        return None

if __name__ == '__main__':
    # Example Usage (for testing this script directly)
    # Ensure you have a .env file in snapshotter-lite-multi-setup or export these vars
    import os
    from dotenv import load_dotenv
    project_root = Path(__file__).parent.parent.parent # This should be snapshotter-lite-multi-setup
    load_dotenv(dotenv_path=project_root / '.env')

    test_wallet = os.getenv("WALLET_HOLDER_ADDRESS")
    test_rpc_url_mainnet = "https://rpc-v2.powerloom.network" # or from env
    test_rpc_url_devnet = "https://rpc-devnet.powerloom.dev" # or from env
    test_protocol_state_mainnet = os.getenv("PROTOCOL_STATE_CONTRACT_MAINNET")
    test_protocol_state_devnet = os.getenv("PROTOCOL_STATE_CONTRACT_DEVNET")
    
    if test_wallet:
        console.print(f"--- Testing MAINNET with wallet: {test_wallet} ---")
        slots_mainnet = fetch_owned_slots(
            test_wallet,
            "MAINNET",
            test_rpc_url_mainnet,
            test_protocol_state_mainnet
        )
        if slots_mainnet is not None:
            console.print(f"Mainnet Slots: {slots_mainnet}")

        console.print(f"\n--- Testing DEVNET with wallet: {test_wallet} ---")
        slots_devnet = fetch_owned_slots(
            test_wallet,
            "DEVNET",
            test_rpc_url_devnet,
            test_protocol_state_devnet
        )
        if slots_devnet is not None:
            console.print(f"Devnet Slots: {slots_devnet}")
    else:
        console.print("Set WALLET_HOLDER_ADDRESS in .env for testing evm.py directly.") 