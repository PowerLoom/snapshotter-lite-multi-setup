import os
import sys
import time
import json

from dotenv import load_dotenv
from web3 import Web3

LOCAL_COLLECTOR_NEW_BUILD_THRESHOLD = 200


def get_user_slots(contract_obj, wallet_owner_addr):
    holder_slots = contract_obj.functions.getUserOwnedNodeIds(wallet_owner_addr).call()
    print(holder_slots)
    return holder_slots


def env_file_template(
    source_rpc_url: str,
    signer_account_address: str,
    signer_account_private_key: str,
    prost_chain_id: str,
    prost_rpc_url: str,
    namespace: str,
    data_market_contract: str,
    protocol_state_contract: str,
    local_collector_port: int,
    powerloom_reporting_url: str,
    slot_id: str,
    core_api_port: int,
    snapshot_config_repo: str,
    snapshot_config_repo_branch: str,
    snapshotter_compute_repo: str,
    snapshotter_compute_repo_branch: str,
    docker_network_name: str = '',
    subnet_third_octet: int = 1,
    max_stream_pool_size: int = 2,
    stream_pool_health_check_interval: int = 30,
    ipfs_url: str = '',
    ipfs_api_key: str = '',
    ipfs_api_secret: str = '',
    slack_reporting_url: str = '',
    web3_storage_token: str = '',
    dashboard_enabled: str = '',
    telegram_reporting_url: str = '',
    telegram_chat_id: str = '',
    override_defaults: bool = True,
    dev_mode: bool = False
) -> str:
    return f"""
# Required
SOURCE_RPC_URL={source_rpc_url}
SIGNER_ACCOUNT_ADDRESS={signer_account_address}
SIGNER_ACCOUNT_PRIVATE_KEY={signer_account_private_key}
SLOT_ID={slot_id}
SNAPSHOT_CONFIG_REPO={snapshot_config_repo}
SNAPSHOT_CONFIG_REPO_BRANCH={snapshot_config_repo_branch}
SNAPSHOTTER_COMPUTE_REPO={snapshotter_compute_repo}
SNAPSHOTTER_COMPUTE_REPO_BRANCH={snapshotter_compute_repo_branch}
DOCKER_NETWORK_NAME={docker_network_name}
PROST_RPC_URL={prost_rpc_url}
PROTOCOL_STATE_CONTRACT={protocol_state_contract}
DATA_MARKET_CONTRACT={data_market_contract}
NAMESPACE={namespace}
POWERLOOM_REPORTING_URL={powerloom_reporting_url}
PROST_CHAIN_ID={prost_chain_id}
LOCAL_COLLECTOR_PORT={local_collector_port}
CORE_API_PORT={core_api_port}
SUBNET_THIRD_OCTET={subnet_third_octet}
MAX_STREAM_POOL_SIZE={max_stream_pool_size}
STREAM_POOL_HEALTH_CHECK_INTERVAL={stream_pool_health_check_interval}
# Optional
IPFS_URL={ipfs_url}
IPFS_API_KEY={ipfs_api_key}
IPFS_API_SECRET={ipfs_api_secret}
SLACK_REPORTING_URL={slack_reporting_url}
WEB3_STORAGE_TOKEN={web3_storage_token}
DASHBOARD_ENABLED={dashboard_enabled}
TELEGRAM_REPORTING_URL={telegram_reporting_url}
TELEGRAM_CHAT_ID={telegram_chat_id}
OVERRIDE_DEFAULTS={'true' if override_defaults else 'false'}
DEV_MODE={dev_mode}
"""


def kill_screen_sessions():
    kill_screens = input('Do you want to kill all running containers and screen sessions of testnet nodes? (y/n) : ')
    if kill_screens.lower() == 'y':
        print('Killing running containers....')
        os.system("docker container ls | grep powerloom-testnet | cut  -d ' ' -f1 | xargs docker container stop")
        print('Sleeping for 10...')
        time.sleep(10)
        print('Killing running screen sessions....')
        os.system("screen -ls | grep powerloom-testnet | cut -d. -f1 | awk '{print $1}' | xargs kill")


def clone_lite_repo(env_contents: str, new_collector_instance: bool, namespace: str, dev_mode: bool, slot_id: int = None):
    repo_name = f'powerloom-testnet-v2-{namespace}'
    if slot_id is not None:
        repo_name = repo_name + f'-{slot_id}'
    if os.path.exists(repo_name):
        print(f'Deleting existing dir {repo_name}')
        os.system(f'rm -rf {repo_name}')

    # Clean up any existing network before creating new one
    network_name = f'snapshotter-lite-v2-{namespace}'
    if slot_id is not None:
        network_name = f'snapshotter-lite-v2-{namespace}-{slot_id}'
    os.system(f'docker network rm {network_name} 2>/dev/null || true')
    time.sleep(1)

    os.system(f'cp -R snapshotter-lite-v2 {repo_name}')
    with open(f'{repo_name}/.env', 'w+') as f:
        f.write(env_contents)
    os.chdir(repo_name)
    print('--'*20 + f'Spinning up docker containers for namespace {namespace}' + '--'*20)
    os.system(f'screen -dmS {repo_name}')
    if not dev_mode:
        if new_collector_instance:
            print('Building new collector instance')
            os.system(f'screen -S {repo_name} -p 0 -X stuff "./build.sh\n"')
        else:
            print('Building existing collector instance')
            os.system(f'screen -S {repo_name} -p 0 -X stuff "./build.sh no_collector\n"')
    else:
        print('Building dev mode')
        if new_collector_instance:
            print('Building new collector instance in dev mode')
            os.system(f'screen -S {repo_name} -p 0 -X stuff "./build-dev.sh\n"')
        else:
            print('Building existing collector instance in dev mode')
            os.system(f'screen -S {repo_name} -p 0 -X stuff "./build-dev.sh no_collector\n"')
    print(f'Spawned screen session for docker containers {repo_name}')

    


def collect_env_vars():
    # Load environment variables with override=True to force update existing vars
    load_dotenv('.env', override=True)
    
    # Required environment variables
    required_vars = [
        "SOURCE_RPC_URL", "SIGNER_ACCOUNT_ADDRESS", "SIGNER_ACCOUNT_PRIVATE_KEY",
        "SLOT_ID", "SNAPSHOT_CONFIG_REPO", "PROST_RPC_URL", 
        "PROTOCOL_STATE_CONTRACT", "POWERLOOM_REPORTING_URL", "PROST_CHAIN_ID",
        "LOCAL_COLLECTOR_PORT", "CORE_API_PORT", "SUBNET_THIRD_OCTET",
        "MAX_STREAM_POOL_SIZE", "STREAM_POOL_HEALTH_CHECK_INTERVAL",
        "SNAPSHOTTER_COMPUTE_REPO"
    ]
    
    # Optional environment variables with default values
    optional_vars = {
        "DOCKER_NETWORK_NAME": "",
        "IPFS_URL": "",
        "IPFS_API_KEY": "",
        "IPFS_API_SECRET": "",
        "SLACK_REPORTING_URL": "",
        "WEB3_STORAGE_TOKEN": "",
        "DASHBOARD_ENABLED": "",
        "TELEGRAM_REPORTING_URL": "",
        "TELEGRAM_CHAT_ID": "",
        "OVERRIDE_DEFAULTS": "false",
        "DEV_MODE": "false",
    }
    
    # Create env_vars dictionary
    env_vars = {}
    
    # Load required variables
    for var in required_vars:
        env_vars[var.lower()] = os.getenv(var)

    # Check if any required variables are missing
    if not all(env_vars[var.lower()] for var in required_vars):
        print('Missing environment variables')
        return
    
    # Load optional variables with defaults
    for var, default in optional_vars.items():
        env_vars[var.lower()] = os.getenv(var, default)

    lite_node_branch = os.getenv('LITE_NODE_BRANCH', 'main')
    dev_mode = os.getenv('DEV_MODE', '').lower() == 'true'
    print('dev_mode:', dev_mode)

    if os.path.exists('snapshotter-lite-v2'):
        print('Deleting existing snapshotter-lite-v2 dir')
        os.system('rm -rf snapshotter-lite-v2')
    print('Cloning lite node branch : ', lite_node_branch)
    os.system(f'git clone https://github.com/PowerLoom/snapshotter-lite-v2 --single-branch --branch ' + lite_node_branch)
    kill_screen_sessions()

    namespaces = os.getenv('NAMESPACES', '').split(',')
    data_market_contracts = os.getenv('DATA_MARKET_CONTRACTS', '').split(',')
    config_repo_branches = os.getenv('SNAPSHOT_CONFIG_REPO_BRANCHES', '').split(',')
    compute_repo_branches = os.getenv('SNAPSHOTTER_COMPUTE_REPO_BRANCHES', '').split(',')
    node_mapping = zip(namespaces, data_market_contracts, config_repo_branches, compute_repo_branches)
    return node_mapping, env_vars, dev_mode


def deploy_single():
    node_mapping, env_vars, dev_mode = collect_env_vars()
    for idx, (namespace, data_market_contract, config_repo_branch, compute_repo_branch) in enumerate(node_mapping):
        print('Cloning market for namespace : ', namespace)
        if idx > 0:
            os.chdir('..')
        if idx % LOCAL_COLLECTOR_NEW_BUILD_THRESHOLD == 0:
            if idx > 1:
                env_vars['local_collector_port'] += 1
            new_collector_instance = True
        else:
            new_collector_instance = False
        
        env_vars['namespace'] = namespace
        env_vars['data_market_contract'] = data_market_contract
        env_vars['snapshot_config_repo_branch'] = config_repo_branch
        env_vars['snapshotter_compute_repo_branch'] = compute_repo_branch
        env_contents = env_file_template(
            **env_vars
        )

        clone_lite_repo(env_contents, new_collector_instance, namespace, dev_mode)
        env_vars['core_api_port'] = str(int(env_vars['core_api_port']) + 1)


def deploy_multiple():
    node_mapping, env_vars, dev_mode = collect_env_vars()
    
    # Setup Web3 connections
    wallet_holder_address = os.getenv("WALLET_HOLDER_ADDRESS")
    slot_contract_address = os.getenv("SLOT_CONTROLLER_ADDRESS")

    if not all([wallet_holder_address, slot_contract_address]):
        print('Missing slot configuration environment variables')
        return

    # Initialize Web3 and contract connections
    w3 = Web3(Web3.HTTPProvider(env_vars['prost_rpc_url']))
    
    # Load contract ABIs
    with open('PowerloomNodes.json', 'r') as f:
        powerloom_nodes_abi = json.load(f)

    # Setup contract instances
    wallet_holder_address = Web3.to_checksum_address(wallet_holder_address)
    slot_contract = w3.eth.contract(
        address=Web3.to_checksum_address(slot_contract_address),
        abi=powerloom_nodes_abi,
    )

    # Get all slots
    slot_ids = get_user_slots(slot_contract, wallet_holder_address)

    if not slot_ids:
        print('No slots found for wallet holder address')
        return

    if len(slot_ids) == 1:
        print('Only one slot found for wallet holder address. Please use single deploy mode.')
        return

    print(f'Found {len(slot_ids)} slots for wallet holder address')
    print(slot_ids)

    # Convert node_mapping iterator to list for indexing
    market_configs = list(node_mapping)
    num_markets = len(market_configs)

    # Deploy nodes for each slot
    for idx, slot_id in enumerate(slot_ids):
        print(f'Deploying node for slot {slot_id}')
        if idx > 0:
            os.chdir('..')
            
        # Determine if we need a new collector instance
        if idx % LOCAL_COLLECTOR_NEW_BUILD_THRESHOLD == 0:
            if idx > 1:
                env_vars['local_collector_port'] = str(int(env_vars['local_collector_port']) + 1)
            new_collector_instance = True
        else:
            new_collector_instance = False

        # Select market configuration based on slot index
        market_idx = idx % num_markets
        namespace, data_market_contract, config_repo_branch, compute_repo_branch = market_configs[market_idx]
        print(f'Deploying market {namespace} for slot {slot_id}')
        
        # Update environment variables for this deployment
        env_vars['namespace'] = namespace
        env_vars['data_market_contract'] = data_market_contract
        env_vars['snapshot_config_repo_branch'] = config_repo_branch
        env_vars['snapshotter_compute_repo_branch'] = compute_repo_branch
        env_vars['slot_id'] = str(slot_id)
        
        # Create environment file and deploy
        env_contents = env_file_template(**env_vars)
        clone_lite_repo(
            env_contents, 
            new_collector_instance, 
            namespace, 
            dev_mode,
            slot_id=slot_id
        )
        
        # Increment core API port for next deployment
        env_vars['core_api_port'] = str(int(env_vars['core_api_port']) + 1)
        # Increment subnet for each deployment to avoid conflicts
        env_vars['subnet_third_octet'] = str(int(env_vars['subnet_third_octet']) + idx)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "multi":
        deploy_multiple()
    else:
        deploy_single()


if __name__ == "__main__":
    main()