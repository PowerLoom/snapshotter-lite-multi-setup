import os
import subprocess
import sys
import time
import json
import argparse
from dotenv import load_dotenv
from web3 import Web3

OUTPUT_WORTHY_ENV_VARS = [
    'SOURCE_RPC_URL', 
    'SIGNER_ACCOUNT_ADDRESS', 
    'WALLET_HOLDER_ADDRESS', 
    'TELEGRAM_CHAT_ID',
    'POWERLOOM_REPORTING_URL',
    'PROST_RPC_URL',
    'PROST_CHAIN_ID',
]

DATA_MARKET_CHOICE_NAMESPACES = {
    '1': 'AAVEV3',
    '2': 'UNISWAPV2'
}
PROST_RPC_URL = 'https://rpc-prost1m.powerloom.io'
DATA_MARKET_CHOICES_PROTOCOL_STATE = {
    'AAVEV3': {
        'DATA_MARKET_CONTRACT': "0xdE95f6d0D1A7B8411fCbfc60d5c2C5Df69d667a9",
        'SNAPSHOTTER_CONFIG_REPO': 'https://github.com/PowerLoom/snapshotter-configs.git',
        'SNAPSHOTTER_COMPUTE_REPO': 'https://github.com/PowerLoom/snapshotter-computes.git',
        'SNAPSHOTTER_CONFIG_REPO_BRANCH': "eth_aavev3_lite_v2",
        'SNAPSHOTTER_COMPUTE_REPO_BRANCH': "eth_aavev3_lite"
    },
    'UNISWAPV2': {
        'DATA_MARKET_CONTRACT': "0xC53ad4C6A8A978fC4A91F08A21DcE847f5Bc0E27",
        'SNAPSHOTTER_CONFIG_REPO': 'https://github.com/PowerLoom/snapshotter-configs.git',
        'SNAPSHOTTER_COMPUTE_REPO': 'https://github.com/PowerLoom/snapshotter-computes.git',
        'SNAPSHOTTER_CONFIG_REPO_BRANCH': "eth_uniswapv2-lite_v2",
        'SNAPSHOTTER_COMPUTE_REPO_BRANCH': "eth_uniswapv2_lite_v2",
    }
}
POWERLOOM_CHAIN = 'mainnet'
SOURCE_CHAIN = 'ETH'

def get_user_slots(contract_obj, wallet_owner_addr):
    holder_slots = contract_obj.functions.getUserOwnedNodeIds(wallet_owner_addr).call()
    return holder_slots


def env_file_template(
    source_rpc_url: str,
    signer_addr: str,
    signer_pkey: str,
    prost_chain_id: str,
    prost_rpc_url: str,
    namespace: str,
    data_market_contract: str,
    slot_id: str,
    snapshot_config_repo: str,
    snapshot_config_repo_branch: str,
    snapshotter_compute_repo: str,
    snapshotter_compute_repo_branch: str,
    powerloom_reporting_url: str,
    subnet_third_octet: int,
    core_api_port: int,
    data_market_in_request: str = 'false',
    ipfs_url: str = '',
    ipfs_api_key: str = '',
    ipfs_api_secret: str = '',
    slack_reporting_url: str = '',
    web3_storage_token: str = '',
    dashboard_enabled: str = 'false',
    telegram_reporting_url: str = '',
    telegram_chat_id: str = '',
    powerloom_chain: str = POWERLOOM_CHAIN,
    source_chain: str = SOURCE_CHAIN,
    local_collector_port: int = 50051,
    max_stream_pool_size: int = 2,
    stream_pool_health_check_interval: int = 30,
) -> str:
    full_namespace = f'{powerloom_chain}-{namespace}-{source_chain}'
    docker_network_name = f"snapshotter-lite-v2-{slot_id}-{full_namespace}"
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
PROST_RPC_URL={prost_rpc_url}
DATA_MARKET_CONTRACT={data_market_contract}
NAMESPACE={namespace}
POWERLOOM_CHAIN={powerloom_chain}
SOURCE_CHAIN={source_chain}
FULL_NAMESPACE={full_namespace}
POWERLOOM_REPORTING_URL={powerloom_reporting_url}
PROST_CHAIN_ID={prost_chain_id}
LOCAL_COLLECTOR_PORT={local_collector_port}
CORE_API_PORT={core_api_port}
SUBNET_THIRD_OCTET={subnet_third_octet}
MAX_STREAM_POOL_SIZE={max_stream_pool_size}
STREAM_POOL_HEALTH_CHECK_INTERVAL={stream_pool_health_check_interval}
DATA_MARKET_IN_REQUEST={data_market_in_request}
# Optional
IPFS_URL={ipfs_url}
IPFS_API_KEY={ipfs_api_key}
IPFS_API_SECRET={ipfs_api_secret}
SLACK_REPORTING_URL={slack_reporting_url}
WEB3_STORAGE_TOKEN={web3_storage_token}
DASHBOARD_ENABLED={dashboard_enabled}
TELEGRAM_REPORTING_URL={telegram_reporting_url}
TELEGRAM_CHAT_ID={telegram_chat_id}
"""

def generate_env_file_contents(data_market_namespace: str, **kwargs) -> str:
    return env_file_template(
        source_rpc_url=kwargs['source_rpc_url'],
        signer_addr=kwargs['signer_addr'],
        signer_pkey=kwargs['signer_pkey'],
        prost_chain_id=kwargs['prost_chain_id'],
        prost_rpc_url=kwargs['prost_rpc_url'],
        namespace=data_market_namespace,
        data_market_contract=kwargs['data_market_contract'],
        slot_id=kwargs['slot_id'],
        snapshot_config_repo=kwargs['snapshotter_config_repo'],
        snapshot_config_repo_branch=kwargs['snapshotter_config_repo_branch'],
        snapshotter_compute_repo=kwargs['snapshotter_compute_repo'],
        snapshotter_compute_repo_branch=kwargs['snapshotter_compute_repo_branch'],
        powerloom_reporting_url=kwargs['powerloom_reporting_url'],
        telegram_chat_id=kwargs['telegram_chat_id'],
        telegram_reporting_url=kwargs['telegram_reporting_url'],
        subnet_third_octet=kwargs['subnet_third_octet'],
        core_api_port=kwargs['core_api_port'],
    )

def run_snapshotter_lite_v2(deploy_slots: list, data_market_contract_number: int, data_market_namespace: str, lite_node_branch: str, **kwargs):
    protocol_state = DATA_MARKET_CHOICES_PROTOCOL_STATE[data_market_namespace]
    core_api_port = 8002
    subnet_third_octet = 1
    full_namespace = f'{POWERLOOM_CHAIN}-{data_market_namespace}-{SOURCE_CHAIN}'
    image_tag = 'dockerify' if lite_node_branch == 'dockerify' else 'latest'

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
            prost_chain_id=kwargs['prost_chain_id'],
            prost_rpc_url=kwargs['prost_rpc_url'],
            namespace=data_market_namespace,
            data_market_contract=protocol_state['DATA_MARKET_CONTRACT'],
            snapshotter_config_repo_branch=protocol_state['SNAPSHOTTER_CONFIG_REPO_BRANCH'],
            snapshotter_compute_repo_branch=protocol_state['SNAPSHOTTER_COMPUTE_REPO_BRANCH'],
            snapshotter_config_repo=protocol_state['SNAPSHOTTER_CONFIG_REPO'],
            snapshotter_compute_repo=protocol_state['SNAPSHOTTER_COMPUTE_REPO'],
            powerloom_reporting_url=kwargs['powerloom_reporting_url'],
            telegram_chat_id=kwargs['telegram_chat_id'],
            telegram_reporting_url=kwargs['telegram_reporting_url'],
            slot_id=slot_id,
            subnet_third_octet=subnet_third_octet+idx,
            core_api_port=core_api_port+idx,
        )
        with open(f'.env-{full_namespace}', 'w+') as f:
            f.write(env_file_contents)
        env_file_name = f'.env-{full_namespace}'
        project_name = f'snapshotter-lite-v2-{slot_id}-{full_namespace}'
        project_name_lower = project_name.lower()
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

def main(data_market_choice: str):
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
    if incomplete_env:
        print('🟡 .env file may be incomplete or corrupted during a previous faulty initialization. Do you want to clear the .env file and re-run ./bootstrap.sh? (y/n)')
        clear_env = input('🫸 ▶︎ Please enter your choice: ')
        if clear_env.lower() == 'y':
            os.remove('.env')
            print('🟢 .env file removed, please run ./bootstrap.sh to re-initialize the .env file...')
            sys.exit(0)
    load_dotenv(override=True)
    
    # Setup Web3 connections
    wallet_holder_address = os.getenv("WALLET_HOLDER_ADDRESS")
    slot_contract_address = os.getenv("SLOT_CONTROLLER_ADDRESS")
    prost_rpc_url = os.getenv("PROST_RPC_URL")
    lite_node_branch = os.getenv("LITE_NODE_BRANCH", 'main')
    if not all([wallet_holder_address, slot_contract_address, prost_rpc_url]):
        print('Missing slot configuration environment variables')
        sys.exit(1)

    # Initialize Web3 and contract connections
    w3 = Web3(Web3.HTTPProvider(prost_rpc_url))
    
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

    print(f'Found {len(slot_ids)} slots for wallet holder address')
    print(slot_ids)
    deploy_slots = list()
    # choose range of slots to deploy
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
    data_market_contract_number = int(data_market_choice, 10) if data_market_choice != '0' else 0
    if not data_market_contract_number:
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
    run_snapshotter_lite_v2(
        deploy_slots,
        data_market_contract_number,
        namespace,
        lite_node_branch,
        source_rpc_url=os.getenv('SOURCE_RPC_URL'),
        signer_addr=os.getenv('SIGNER_ACCOUNT_ADDRESS'),
        signer_pkey=os.getenv('SIGNER_ACCOUNT_PRIVATE_KEY'),
        prost_chain_id=os.getenv('PROST_CHAIN_ID'),
        prost_rpc_url=os.getenv('PROST_RPC_URL'),
        powerloom_reporting_url=os.getenv('POWERLOOM_REPORTING_URL'),
        telegram_chat_id=os.getenv('TELEGRAM_CHAT_ID'),
        telegram_reporting_url=os.getenv('TELEGRAM_REPORTING_URL', 'https://tg-testing.powerloom.io'),
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PowerLoom mainnet multi-node setup')
    parser.add_argument('--data-market', choices=['1', '2'],
                    help='Data market choice (1: AAVEV3, 2: UNISWAPV2)')
    
    args = parser.parse_args()
    
    data_market = args.data_market if args.data_market else '0'
    main(data_market_choice=data_market)
