import os
import subprocess
import sys
import time
import json
import argparse
from dotenv import load_dotenv
from web3 import Web3
import psutil

OUTPUT_WORTHY_ENV_VARS = [
    'SOURCE_RPC_URL', 
    'SIGNER_ACCOUNT_ADDRESS', 
    'WALLET_HOLDER_ADDRESS', 
    'TELEGRAM_CHAT_ID',
    'POWERLOOM_RPC_URL',
]

DATA_MARKET_CHOICE_NAMESPACES = {
    '1': 'AAVEV3',
    '2': 'UNISWAPV2'
}

# legacy data market choices
DATA_MARKET_CHOICES_PROTOCOL_STATE = {
    'AAVEV3': {
        'DATA_MARKET_CONTRACT': "0x0000000000000000000000000000000000000000",
        'SNAPSHOTTER_CONFIG_REPO': 'https://github.com/PowerLoom/snapshotter-configs.git',
        'SNAPSHOTTER_COMPUTE_REPO': 'https://github.com/PowerLoom/snapshotter-computes.git',
        'SNAPSHOTTER_CONFIG_REPO_BRANCH': "eth_aavev3_lite_v2",
        'SNAPSHOTTER_COMPUTE_REPO_BRANCH': "eth_aavev3_lite"
    },
    'UNISWAPV2': {
        'DATA_MARKET_CONTRACT': "0x21cb57C1f2352ad215a463DD867b838749CD3b8f",
        'SNAPSHOTTER_CONFIG_REPO': 'https://github.com/PowerLoom/snapshotter-configs.git',
        'SNAPSHOTTER_COMPUTE_REPO': 'https://github.com/PowerLoom/snapshotter-computes.git',
        'SNAPSHOTTER_CONFIG_REPO_BRANCH': "eth_uniswapv2-lite_v2",
        'SNAPSHOTTER_COMPUTE_REPO_BRANCH': "eth_uniswapv2_lite_v2",
    }
}
POWERLOOM_CHAIN = 'mainnet'
SOURCE_CHAIN = 'ETH'
POWERLOOM_RPC_URL = 'https://rpc-v2.powerloom.network'
PROTOCOL_STATE_CONTRACT = "0x000AA7d3a6a2556496f363B59e56D9aA1881548F"


def get_user_slots(contract_obj, wallet_owner_addr):
    holder_slots = contract_obj.functions.getUserOwnedNodeIds(wallet_owner_addr).call()
    return holder_slots


def env_file_template(
    source_rpc_url: str,
    signer_addr: str,
    signer_pkey: str,
    powerloom_rpc_url: str,
    namespace: str,
    data_market_contract: str,
    slot_id: str,
    snapshot_config_repo: str,
    snapshot_config_repo_branch: str,
    snapshotter_compute_repo: str,
    snapshotter_compute_repo_branch: str,
    data_market_in_request: str = 'false',
    telegram_reporting_url: str = '',
    telegram_chat_id: str = '',
    powerloom_chain: str = POWERLOOM_CHAIN,
    source_chain: str = SOURCE_CHAIN,
    local_collector_port: int = 50051,
    max_stream_pool_size: int = 2,
    stream_pool_health_check_interval: int = 30,
    local_collector_image_tag: str = 'latest',
    telegram_notification_cooldown: int = 300,
    connection_refresh_interval_sec: int = 60,
) -> str:
    full_namespace = f'{powerloom_chain}-{namespace}-{source_chain}'
    docker_network_name = f"snapshotter-lite-v2-{full_namespace}"
    return f"""
# Required
SOURCE_RPC_URL={source_rpc_url}
SIGNER_ACCOUNT_ADDRESS={signer_addr}
SIGNER_ACCOUNT_PRIVATE_KEY={signer_pkey}
SLOT_ID={slot_id}
SNAPSHOT_CONFIG_REPO={snapshot_config_repo}
SNAPSHOT_CONFIG_REPO_BRANCH={snapshot_config_repo_branch}
SNAPSHOTTER_COMPUTE_REPO={snapshotter_compute_repo}
SNAPSHOTTER_COMPUTE_REPO_BRANCH={snapshotter_compute_repo_branch}
DOCKER_NETWORK_NAME={docker_network_name}
POWERLOOM_RPC_URL={powerloom_rpc_url}
DATA_MARKET_CONTRACT={data_market_contract}
NAMESPACE={namespace}
POWERLOOM_CHAIN={powerloom_chain}
SOURCE_CHAIN={source_chain}
FULL_NAMESPACE={full_namespace}
LOCAL_COLLECTOR_PORT={local_collector_port}
MAX_STREAM_POOL_SIZE={max_stream_pool_size}
STREAM_POOL_HEALTH_CHECK_INTERVAL={stream_pool_health_check_interval}
DATA_MARKET_IN_REQUEST={data_market_in_request}
# Optional
LOCAL_COLLECTOR_IMAGE_TAG={local_collector_image_tag}
TELEGRAM_REPORTING_URL={telegram_reporting_url}
TELEGRAM_CHAT_ID={telegram_chat_id}
CONNECTION_REFRESH_INTERVAL_SEC={connection_refresh_interval_sec}
TELEGRAM_NOTIFICATION_COOLDOWN={telegram_notification_cooldown}
"""

def generate_env_file_contents(data_market_namespace: str, **kwargs) -> str:
    return env_file_template(
        source_rpc_url=kwargs['source_rpc_url'],
        signer_addr=kwargs['signer_addr'],
        signer_pkey=kwargs['signer_pkey'],
        powerloom_rpc_url=kwargs['powerloom_rpc_url'],
        namespace=data_market_namespace,
        data_market_contract=kwargs['data_market_contract'],
        slot_id=kwargs['slot_id'],
        snapshot_config_repo=kwargs['snapshotter_config_repo'],
        snapshot_config_repo_branch=kwargs['snapshotter_config_repo_branch'],
        snapshotter_compute_repo=kwargs['snapshotter_compute_repo'],
        snapshotter_compute_repo_branch=kwargs['snapshotter_compute_repo_branch'],
        telegram_chat_id=kwargs['telegram_chat_id'],
        telegram_reporting_url=kwargs['telegram_reporting_url'],
        max_stream_pool_size=kwargs['max_stream_pool_size'],
        stream_pool_health_check_interval=kwargs['stream_pool_health_check_interval'],
        local_collector_image_tag=kwargs['local_collector_image_tag'],
        connection_refresh_interval_sec=kwargs['connection_refresh_interval_sec'],
    )

def run_snapshotter_lite_v2(deploy_slots: list, data_market_contract_number: int, data_market_namespace: str, **kwargs):
    protocol_state = DATA_MARKET_CHOICES_PROTOCOL_STATE[data_market_namespace]
    full_namespace = f'{POWERLOOM_CHAIN}-{data_market_namespace}-{SOURCE_CHAIN}'

    for idx, slot_id in enumerate(deploy_slots):
        print(f'🟠 Deploying node for slot {slot_id} in data market {data_market_namespace}')
        if idx > 0:
            os.chdir('..')
            collector_profile_string = '--no-collector --no-autoheal-launch'
        else:
            collector_profile_string = ''
        repo_name = f'powerloom-mainnet-v2-{slot_id}-{data_market_namespace}'
        if os.path.exists(repo_name):
            print(f'Deleting existing dir {repo_name}')
            os.system(f'rm -rf {repo_name}')
        os.system(f'cp -R snapshotter-lite-v2 {repo_name}')
        os.chdir(repo_name)
        env_file_contents = generate_env_file_contents(
            data_market_namespace=data_market_namespace,
            source_rpc_url=kwargs['source_rpc_url'],
            signer_addr=kwargs['signer_addr'],
            signer_pkey=kwargs['signer_pkey'],
            powerloom_rpc_url=kwargs['powerloom_rpc_url'],
            namespace=data_market_namespace,
            data_market_contract=protocol_state['DATA_MARKET_CONTRACT'],
            snapshotter_config_repo_branch=protocol_state['SNAPSHOTTER_CONFIG_REPO_BRANCH'],
            snapshotter_compute_repo_branch=protocol_state['SNAPSHOTTER_COMPUTE_REPO_BRANCH'],
            snapshotter_config_repo=protocol_state['SNAPSHOTTER_CONFIG_REPO'],
            snapshotter_compute_repo=protocol_state['SNAPSHOTTER_COMPUTE_REPO'],
            telegram_chat_id=kwargs['telegram_chat_id'],
            telegram_reporting_url=kwargs['telegram_reporting_url'],
            max_stream_pool_size=kwargs['max_stream_pool_size'],
            stream_pool_health_check_interval=kwargs['stream_pool_health_check_interval'],
            local_collector_image_tag=kwargs['local_collector_image_tag'],
            slot_id=slot_id,
            connection_refresh_interval_sec=kwargs['connection_refresh_interval_sec'],
        )
        with open(f'.env-{full_namespace}', 'w+') as f:
            f.write(env_file_contents)
        # docker build and run
        print('--'*20 + f'Spinning up docker containers for slot {slot_id}' + '--'*20) 
        os.system(f"""
screen -dmS {repo_name}
screen -r {repo_name} -p 0 -X stuff "./build.sh {collector_profile_string} --skip-credential-update --data-market-contract-number {data_market_contract_number}\n"
        """)
        sleep_duration = 30 if idx == 0 else 10
        print(f'Sleeping for {sleep_duration} seconds to allow docker containers to spin up...')
        time.sleep(sleep_duration)

def docker_running():
    try:
        # Check if Docker is running
        subprocess.check_output(['docker', 'info'])
        return True
    except subprocess.CalledProcessError:
        return False

def main(data_market_choice: str, non_interactive: bool = False, latest_only: bool = False):
    # check if Docker is running
    if not docker_running():
        print('🟡 Docker is not running, please start Docker and try again!')
        sys.exit(1)
    # check if .env file exists
    if not os.path.exists('.env'):
        print("🟡 .env file not found, please run bootstrap.sh to create one!")
        sys.exit(1)
    print('🟢 .env file found with following env variables...')
    incomplete_env = False
    with open('.env', 'r') as f:
        for line in f:
            # if the line contains any of the OUTPUT_WORTHY_ENV_VARS, print it
            if any(var in line for var in OUTPUT_WORTHY_ENV_VARS):
                print(line.strip())
                if line.strip() == '' or '<' in line.strip() or '>' in line.strip():
                    incomplete_env = True
    if incomplete_env and not non_interactive:
        print('🟡 .env file may be incomplete or corrupted during a previous faulty initialization. Do you want to clear the .env file and re-run ./bootstrap.sh? (y/n)')
        clear_env = input('🫸 ▶︎ Please enter your choice: ')
        if clear_env.lower() == 'y':
            os.remove('.env')
            print('🟢 .env file removed, please run ./bootstrap.sh to re-initialize the .env file...')
            sys.exit(0)
    elif incomplete_env and non_interactive:
        print('🟡 .env file may be incomplete or corrupted. Please run bootstrap.sh manually to fix it.')
        sys.exit(1)
        
    load_dotenv(override=True)
    # force uniswapv2 for now
    data_market_choice = '2'
    data_market_contract_number = int(data_market_choice, 10)
    namespace = DATA_MARKET_CHOICE_NAMESPACES[str(data_market_contract_number)]
    # Setup Web3 connections
    wallet_holder_address = os.getenv("WALLET_HOLDER_ADDRESS")
    powerloom_rpc_url = os.getenv("POWERLOOM_RPC_URL")

    if not powerloom_rpc_url:
        print('🟡 POWERLOOM_RPC_URL is not set in .env file, using default value...')
        powerloom_rpc_url = POWERLOOM_RPC_URL

    lite_node_branch = os.getenv("LITE_NODE_BRANCH", 'main')
    local_collector_image_tag = os.getenv("LOCAL_COLLECTOR_IMAGE_TAG", '')
    if not local_collector_image_tag:
        if lite_node_branch != 'dockerify':
            local_collector_image_tag = 'latest'
        else:
            local_collector_image_tag = 'dockerify'
    print(f'🟢 Using local collector image tag: {local_collector_image_tag}')
    if not wallet_holder_address:
        print('Missing wallet holder address environment variable')
        sys.exit(1)

    # Initialize Web3 and contract connections
    w3 = Web3(Web3.HTTPProvider(powerloom_rpc_url))
    # Load contract ABIs
    with open('ProtocolState.json', 'r') as f:
        protocol_state_abi = json.load(f)
    with open('PowerloomNodes.json', 'r') as f:
        powerloom_nodes_abi = json.load(f)

    try:
        block_number = w3.eth.get_block_number()
        print(f"✅ Successfully fetched the latest block number {block_number}. Your ISP is supported!")
    except Exception as e:
        print(f"❌ Failed to fetch the latest block number. Your ISP/VPS region is not supported ⛔️ . Exception: {e}")
        sys.exit(1)

    protocol_state_address = w3.to_checksum_address(PROTOCOL_STATE_CONTRACT)
    protocol_state_contract = w3.eth.contract(
        address=protocol_state_address,
        abi=protocol_state_abi,
    )

    slot_contract_address = protocol_state_contract.functions.snapshotterState().call()
    slot_contract_address = w3.to_checksum_address(slot_contract_address)

    print(f'🔎 Against protocol state contract {protocol_state_address} found snapshotter state contract {slot_contract_address}')

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

    print(f'Found {len(slot_ids)} slots for wallet holder address')
    print(slot_ids)
    deploy_slots = list()
    # choose range of slots to deploy
    if latest_only:
        # Deploy only the latest (highest) slot
        latest_slot = max(slot_ids)
        deploy_slots = [latest_slot]
        print(f'🟢 Latest-only mode: Deploying only the latest slot {latest_slot}')
    elif non_interactive:
        deploy_slots = slot_ids
        print('🟢 Non-interactive mode: Deploying all slots')
    else:
        deploy_all_slots = input('☑️ Do you want to deploy all slots? (y/n)')
        if deploy_all_slots.lower() == 'n':
            start_slot = input('🫸 ▶︎ Enter the start slot ID: ')
            end_slot = input('🫸 ▶︎ Enter the end slot ID: ')
            start_slot = int(start_slot)
            end_slot = int(end_slot)
            # find index of start_slot and end_slot in slot_ids
            start_slot_idx = slot_ids.index(start_slot)
            end_slot_idx = slot_ids.index(end_slot)
            deploy_slots = slot_ids[start_slot_idx:end_slot_idx+1]
        else:
            deploy_slots = slot_ids

    print(f'🎰 Final list of slots to deploy: {deploy_slots}')
    
    if not data_market_contract_number:
        if non_interactive:
            # Default to UNISWAPV2 in non-interactive mode
            data_market = '2'
            namespace = DATA_MARKET_CHOICE_NAMESPACES[data_market]
            data_market_contract_number = int(data_market, 10)
            print(f"\n🟢 Non-interactive mode: Defaulting to {namespace}")
        else:
            print("\n🔍 Select a data market contract (UNISWAPV2 is default):")
            for key, value in DATA_MARKET_CHOICE_NAMESPACES.items():
                print(f"{key}. {value}")
            data_market = input("\n🫸 ▶︎ Please enter your choice (1/2) [default: 2 - UNISWAPV2]: ").strip()
            
            # Default to UNISWAPV2 if input is empty or invalid
            if not data_market or data_market not in DATA_MARKET_CHOICE_NAMESPACES:
                data_market = '2'  # Default to UNISWAPV2
                print(f"\n🟢 Defaulting to UNISWAPV2")

            # Get namespace from the data market choice
            namespace = DATA_MARKET_CHOICE_NAMESPACES[data_market]
            data_market_contract_number = int(data_market, 10)
            print(f"\n🟢 Selected data market namespace: {namespace}")
    else:
        namespace = DATA_MARKET_CHOICE_NAMESPACES[data_market_choice]
        print(f"\n🟢 Selected data market namespace: {namespace}")

    if os.path.exists('snapshotter-lite-v2'):
        print('🟡 Previously cloned snapshotter-lite-v2 repo already exists, deleting...')
        os.system('rm -rf snapshotter-lite-v2')
    print('⚙️ Cloning snapshotter-lite-v2 repo from main branch...')
    os.system(f'git clone https://github.com/PowerLoom/snapshotter-lite-v2 --single-branch --branch {lite_node_branch}')
    # recommended max stream pool size
    cpus = psutil.cpu_count(logical=True)
    if cpus >= 2 and cpus < 4:
        recommended_max_stream_pool_size = 40
    elif cpus >= 4:
        recommended_max_stream_pool_size = 100
    else:
        recommended_max_stream_pool_size = 20
    if os.getenv('MAX_STREAM_POOL_SIZE'):
        try:
            max_stream_pool_size = int(os.getenv('MAX_STREAM_POOL_SIZE', '0'))
        except Exception:
            max_stream_pool_size = 0
        else:
            print(f'🟢 Using MAX_STREAM_POOL_SIZE from .env file: {max_stream_pool_size}')
    if not max_stream_pool_size:
        max_stream_pool_size = recommended_max_stream_pool_size
        print(f'🟢 Using recommended MAX_STREAM_POOL_SIZE for {cpus} logical CPUs: {max_stream_pool_size}')
    if max_stream_pool_size > recommended_max_stream_pool_size:
        print(f'⚠️ MAX_STREAM_POOL_SIZE is greater than the recommended {recommended_max_stream_pool_size} for {cpus} logical CPUs, this may cause instability!')
        print('Switching to recommended MAX_STREAM_POOL_SIZE...')
        max_stream_pool_size = recommended_max_stream_pool_size
    if len(deploy_slots) < max_stream_pool_size and len(slot_ids) < max_stream_pool_size:
        print(f'🟡 Only {len(deploy_slots)} slots are being deployed out of {len(slot_ids)}, but MAX_STREAM_POOL_SIZE is set to {max_stream_pool_size}. This may cause instability!')
        print('Scaling down MAX_STREAM_POOL_SIZE to match the total number of slots...')
        max_stream_pool_size = len(slot_ids)
    run_snapshotter_lite_v2(
        deploy_slots,
        data_market_contract_number,
        namespace,
        source_rpc_url=os.getenv('SOURCE_RPC_URL'),
        signer_addr=os.getenv('SIGNER_ACCOUNT_ADDRESS'),
        signer_pkey=os.getenv('SIGNER_ACCOUNT_PRIVATE_KEY'),
        powerloom_rpc_url=os.getenv('POWERLOOM_RPC_URL'),
        telegram_chat_id=os.getenv('TELEGRAM_CHAT_ID'),
        telegram_reporting_url=os.getenv('TELEGRAM_REPORTING_URL', 'https://tg-testing.powerloom.io'),
        max_stream_pool_size=max_stream_pool_size,
        stream_pool_health_check_interval=os.getenv('STREAM_POOL_HEALTH_CHECK_INTERVAL', 120),
        local_collector_image_tag=local_collector_image_tag,
        connection_refresh_interval_sec=os.getenv('CONNECTION_REFRESH_INTERVAL_SEC', 60),
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PowerLoom mainnet multi-node setup')
    parser.add_argument('--data-market', choices=['1', '2'],
                    help='Data market choice (1: AAVEV3, 2: UNISWAPV2)')
    parser.add_argument('-y', '--yes', action='store_true',
                    help='Deploy all nodes without prompting for confirmation')
    parser.add_argument('--latest-only', action='store_true',
                    help='Deploy only the latest (highest) slot')
    
    args = parser.parse_args()
    
    data_market = args.data_market if args.data_market else '0'
    main(data_market_choice=data_market, non_interactive=args.yes, latest_only=args.latest_only)
