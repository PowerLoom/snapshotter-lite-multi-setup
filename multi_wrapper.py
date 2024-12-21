import os
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
        'DATA_MARKET_CONTRACT': "0xc390a15BcEB89C2d4910b2d3C696BfD21B190F07",
        'SNAPSHOTTER_CONFIG_REPO': 'https://github.com/PowerLoom/snapshotter-configs.git',
        'SNAPSHOTTER_COMPUTE_REPO': 'https://github.com/PowerLoom/snapshotter-computes.git',
        'SNAPSHOTTER_CONFIG_REPO_BRANCH': "eth_aavev3_lite_v2",
        'SNAPSHOTTER_COMPUTE_REPO_BRANCH': "eth_aavev3_lite"
    },
    'UNISWAPV2': {
        'DATA_MARKET_CONTRACT': "0x8023BD7A9e8386B10336E88294985e3Fbc6CF23F",
        'SNAPSHOTTER_CONFIG_REPO': 'https://github.com/PowerLoom/snapshotter-configs.git',
        'SNAPSHOTTER_COMPUTE_REPO': 'https://github.com/PowerLoom/snapshotter-computes.git',
        'SNAPSHOTTER_CONFIG_REPO_BRANCH': "eth_uniswapv2-lite_v2",
        'SNAPSHOTTER_COMPUTE_REPO_BRANCH': "eth_uniswapv2_lite_v2",
    }
}


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
    telegram_chat_id: str = ''
) -> str:
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
PROST_RPC_URL={prost_rpc_url}
DATA_MARKET_CONTRACT={data_market_contract}
NAMESPACE={namespace}
POWERLOOM_REPORTING_URL={powerloom_reporting_url}
PROST_CHAIN_ID={prost_chain_id}
DATA_MARKET_IN_REQUEST={data_market_in_request}
SUBNET_THIRD_OCTET={subnet_third_octet}
CORE_API_PORT={core_api_port}
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
        subnet_third_octet=kwargs['subnet_third_octet'],
        core_api_port=kwargs['core_api_port'],
    )

def run_snapshotter_lite_v2(deploy_slots: list, data_market_contract_number: int, data_market_namespace: str, **kwargs):
    protocol_state = DATA_MARKET_CHOICES_PROTOCOL_STATE[data_market_namespace]
    core_api_port = 8002
    subnet_third_octet = 1
    for idx, slot_id in enumerate(deploy_slots):
        print(f'🟠 Deploying node for slot {slot_id} in data market {data_market_namespace}')
        if idx > 0:
            os.chdir('..')
            collector_flag = '--no-collector'
        else:
            collector_flag = ''
        repo_name = f'powerloom-premainnet-v2-{slot_id}-{data_market_namespace}'
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
            slot_id=slot_id,
            subnet_third_octet=subnet_third_octet+idx,
            core_api_port=core_api_port+idx,
        )
        with open(f'.env-{data_market_namespace}', 'w+') as f:
            f.write(env_file_contents)
        # docker build and run
        print('--'*20 + f'Spinning up docker containers for slot {slot_id}' + '--'*20) 
        os.system(f"""
screen -dmS {repo_name}
export DATA_MARKET_CONTRACT_NUMBER={data_market_contract_number}
export NAMESPACE={data_market_namespace}
screen -S {repo_name} -p 0 -X stuff "./build.sh --skip-credential-update --data-market-contract-number {data_market_contract_number} {collector_flag} \n"
        """)
        time.sleep(3)

def main(data_market_choice: str):
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
    data_market_contract_number = int(data_market_choice, 10)
    if not data_market_contract_number:
        print("\n🔍 Select a data market contract:")
        for key, value in DATA_MARKET_CHOICE_NAMESPACES.items():
            print(f"{key}. {value}")
        data_market = input("\n🫸 ▶︎ Please enter your choice (1/2): ")
    
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
    os.system(f'git clone https://github.com/PowerLoom/snapshotter-lite-v2 --single-branch --branch feat/flexible-build-support-multi-nodes')
    run_snapshotter_lite_v2(
        deploy_slots,
        data_market_contract_number,
        namespace,
        source_rpc_url=os.getenv('SOURCE_RPC_URL'),
        signer_addr=os.getenv('SIGNER_ACCOUNT_ADDRESS'),
        signer_pkey=os.getenv('SIGNER_ACCOUNT_PRIVATE_KEY'),
        prost_chain_id=os.getenv('PROST_CHAIN_ID'),
        prost_rpc_url=os.getenv('PROST_RPC_URL'),
        powerloom_reporting_url=os.getenv('POWERLOOM_REPORTING_URL'),
        telegram_chat_id=os.getenv('TELEGRAM_CHAT_ID'),
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PowerLoom pre-mainnet multi-node setup')
    parser.add_argument('--data-market', choices=['1', '2'],
                    help='Data market choice (1: AAVEV3, 2: UNISWAPV2)')
    
    args = parser.parse_args()
    
    data_market = args.data_market if args.data_market else '0'
    main(data_market_choice=data_market)
