import os
import sys
import time
import json
import argparse
from dotenv import load_dotenv
from web3 import Web3

OUTPUT_WORTHY_ENV_VARS = ['SOURCE_RPC_URL', 'SIGNER_ACCOUNT_ADDRESS', 'WALLET_HOLDER_ADDRESS']

DATA_MARKET_CHOICE_NAMESPACES = {
    '1': 'AAVEV3',
    '2': 'UNISWAPV2'
}


def get_user_slots(contract_obj, wallet_owner_addr):
    holder_slots = contract_obj.functions.getUserOwnedNodeIds(wallet_owner_addr).call()
    return holder_slots


def kill_screen_sessions():
    kill_screens = input('Do you want to kill all running containers and screen sessions of testnet nodes? (y/n) : ')
    if kill_screens.lower() == 'y':
        print('Killing running containers....')
        os.system("docker container ls | grep powerloom-testnet | cut  -d ' ' -f1 | xargs docker container stop")
        print('Sleeping for 10...')
        time.sleep(10)
        print('Killing running screen sessions....')
        os.system("screen -ls | grep powerloom-testnet | cut -d. -f1 | awk '{print $1}' | xargs kill")

    print(f'Spawned screen session for docker containers {repo_name}')


def namespaced_env_file_template() -> str:
    with open('env.singlenode.example', 'r') as f:
        env_contents = f.read()
    return env_contents


def main(data_market_choice: int):
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
    print('☑️ Do you want to deploy all slots? (y/n)')
    deploy_all_slots = input('🫸 ▶︎ Please enter your choice: ')
    if deploy_all_slots.lower() == 'n':
        start_slot = input('🫸 ▶︎ Please enter the start slot ID: ')
        end_slot = input('🫸 ▶︎ Please enter the end slot ID: ')
        start_slot = int(start_slot)
        end_slot = int(end_slot)
        # find index of start_slot and end_slot in slot_ids
        start_slot_idx = slot_ids.index(start_slot)
        end_slot_idx = slot_ids.index(end_slot)
        deploy_slots = slot_ids[start_slot_idx:end_slot_idx+1]
    else:
        deploy_slots = slot_ids

    print(f'Deploying slots: {deploy_slots}')

    if not data_market_choice:
        print("\n🔍 Select a data market contract:")
        for key, value in DATA_MARKET_CHOICE_NAMESPACES.items():
            print(f"{key}. {value}")
        data_market = input("\n🫸 ▶︎ Please enter your choice (1/2): ")
    
        # Get namespace from the data market choice
        namespace = DATA_MARKET_CHOICE_NAMESPACES[data_market]
        print(f"\n🟢 Selected data market namespace: {namespace}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PowerLoom pre-mainnet multi-node setup')
    parser.add_argument('--data-market', choices=['1', '2'],
                    help='Data market choice (1: AAVEV3, 2: UNISWAPV2)')
    
    args = parser.parse_args()
    
    data_market = args.data_market if args.data_market else 0
    main(data_market_choice=int(data_market))