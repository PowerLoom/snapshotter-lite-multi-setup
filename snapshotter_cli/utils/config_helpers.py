import os
from typing import Optional, Dict
from rich.console import Console
from pathlib import Path # Added for CWD .env logic

# Import models carefully to avoid circular dependencies if this grows
from .models import ChainSpecificIdentity, UserSettings 

console = Console()


# Utility function to parse .env files
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

def get_credential(
    cred_type: str, 
    chain_name_for_env: str, # Still needed for settings.json context
    cli_option_value: Optional[str],
    configured_chain_identity: Optional[ChainSpecificIdentity],
    namespaced_env_vars: Optional[Dict[str, str]] = None
) -> Optional[str]:
    # 1. CLI option
    if cli_option_value:
        # console.print(f"ℹ️ Using {cred_type.replace('_', ' ').title()} from command-line option.", style="dim")
        # if cred_type == "SIGNER_ACCOUNT_PRIVATE_KEY": console.print("   [yellow]Warning: Passing private keys via CLI history can be risky.[/yellow]")
        return cli_option_value

    # 2. Global Environment Variable (e.g., WALLET_HOLDER_ADDRESS)
    # No chain-specific prefix for shell env vars for credentials like WALLET_HOLDER_ADDRESS
    env_val = os.getenv(cred_type) 
    if env_val:
        # console.print(f"ℹ️ Using {cred_type.replace('_', ' ').title()} from {cred_type} env var.", style="dim")
        return env_val

    # 3. Check CWD .env file if no explicit namespaced_env_vars were passed
    if namespaced_env_vars is None: # Only if we are not already in a market-specific context
        cwd_dot_env_path = Path(os.getcwd()) / ".env"
        if cwd_dot_env_path.exists():
            # console.print(f"  ℹ️ Checking for {cred_type} in {cwd_dot_env_path}", style="dim")
            cwd_env_vars = parse_env_file_vars(str(cwd_dot_env_path))
            if cred_type in cwd_env_vars:
                # console.print(f"    Found {cred_type} in {cwd_dot_env_path}", style="dim")
                return cwd_env_vars[cred_type]

    # 4. Namespaced .env file (e.g., from .env.chain.market.source)
    if namespaced_env_vars and cred_type in namespaced_env_vars:
        # console.print(f"ℹ️ Using {cred_type.replace('_', ' ').title()} from namespaced .env file.", style="dim")
        return namespaced_env_vars[cred_type]

    # 5. Configured Identity for the specific chain (settings.json)
    # This is where chain_name_for_env becomes relevant for WALLET_HOLDER_ADDRESS
    if configured_chain_identity: # This object is already chain-specific
        if cred_type == "WALLET_HOLDER_ADDRESS" and configured_chain_identity.wallet_address:
            # console.print(f"ℹ️ Using Wallet Holder Address from configured identity for {chain_name_for_env}.", style="dim")
            return configured_chain_identity.wallet_address
        if cred_type == "SIGNER_ACCOUNT_ADDRESS" and configured_chain_identity.signer_account_address:
            # console.print(f"ℹ️ Using Signer Account Address from configured identity for {chain_name_for_env}.", style="dim")
            return configured_chain_identity.signer_account_address
        if cred_type == "SIGNER_ACCOUNT_PRIVATE_KEY" and configured_chain_identity.signer_account_private_key:
            # console.print(f"ℹ️ Using Signer Private Key from configured identity for {chain_name_for_env}.", style="dim")
            return configured_chain_identity.signer_account_private_key
            
    return None

def get_source_chain_rpc_url(
    source_chain_name: str, 
    user_settings: UserSettings,
    namespaced_env_vars: Optional[Dict[str, str]] = None
) -> Optional[str]:
    env_var_suffix = source_chain_name.upper().replace("-", "_")
    
    # Priority 1: Environment Variable (e.g., SOURCE_RPC_ETH_MAINNET)
    env_var_name = f"SOURCE_RPC_{env_var_suffix}" # No prefix
    env_rpc_url = os.getenv(env_var_name)
    if env_rpc_url:
        # console.print(f"ℹ️ Using Source RPC URL for {source_chain_name} from {env_var_name} env var.", style="dim")
        return env_rpc_url

    # Priority 2: Check CWD .env file if no explicit namespaced_env_vars were passed
    if namespaced_env_vars is None: 
        cwd_dot_env_path = Path(os.getcwd()) / ".env"
        if cwd_dot_env_path.exists():
            cwd_env_vars = parse_env_file_vars(str(cwd_dot_env_path))
            # Try generic SOURCE_RPC_URL first
            if "SOURCE_RPC_URL" in cwd_env_vars:
                return cwd_env_vars["SOURCE_RPC_URL"]
            # Then try source-chain specific, e.g. SOURCE_RPC_ETH_MAINNET, from CWD .env
            source_specific_key_in_cwd_env = f"SOURCE_RPC_{env_var_suffix}"
            if source_specific_key_in_cwd_env in cwd_env_vars:
                return cwd_env_vars[source_specific_key_in_cwd_env]

    # Priority 3: Namespaced .env file (e.g., from .env.chain.market.source, passed in explicitly)
    # The key in the market-specific namespaced .env file is expected to be SOURCE_RPC_URL
    if namespaced_env_vars and "SOURCE_RPC_URL" in namespaced_env_vars:
        # console.print(f"ℹ️ Using Source RPC URL for {source_chain_name} from namespaced .env file.", style="dim")
        return namespaced_env_vars["SOURCE_RPC_URL"]

    # Priority 4: Configured user settings (settings.json)
    if source_chain_name.upper() in user_settings.source_chain_rpcs:
        conf_rpc_url_obj = user_settings.source_chain_rpcs[source_chain_name.upper()]
        # console.print(f"ℹ️ Using Source RPC URL for {source_chain_name} from configured settings.", style="dim")
        return str(conf_rpc_url_obj)
    
    return None 