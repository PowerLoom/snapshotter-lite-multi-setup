from email.policy import default
import os
import json
from threading import local
import time
from web3 import Web3
from dotenv import load_dotenv
from os import environ
import subprocess
import re
import sys

LOCAL_COLLECTOR_NEW_BUILD_THRESHOLD = 200

# get from slot contract and set in redis
def get_user_slots(contract_obj, wallet_owner_addr):
    holder_slots = contract_obj.functions.getUserOwnedSlotIds(wallet_owner_addr).call()
    print(holder_slots)
    return holder_slots


def env_file_template(
        source_rpc_url: str,
        signer_addr: str,
        signer_pkey: str,
        prost_chain_id: str,
        prost_rpc_url: str,
        namespace: str,
        data_market_contract: str,
        protocol_state_contract: str,
        local_collector_port: int,
        powerloom_reporting_url: str,
        slot_id: str,
        core_api_port: int,
        subnet_third_octet: int,
        ipfs_url: str = '',
        ipfs_api_key: str = '',
        ipfs_api_secret: str = '',
        slack_reporting_url: str = '',
        web3_storage_token: str = ''
) -> str:
    return f"""
SOURCE_RPC_URL={source_rpc_url}
SIGNER_ACCOUNT_ADDRESS={signer_addr}
SIGNER_ACCOUNT_PRIVATE_KEY={signer_pkey}
PROST_CHAIN_ID={prost_chain_id}
PROST_RPC_URL={prost_rpc_url}
NAMESPACE={namespace}
PROTOCOL_STATE_CONTRACT={protocol_state_contract}
DATA_MARKET_CONTRACT={data_market_contract}
POWERLOOM_REPORTING_URL={powerloom_reporting_url}
SLOT_ID={slot_id}
CORE_API_PORT={core_api_port}
LOCAL_COLLECTOR_PORT={local_collector_port}
SUBNET_THIRD_OCTET={subnet_third_octet}
# OPTIONAL
IPFS_URL={ipfs_url}
IPFS_API_KEY={ipfs_api_key}
IPFS_API_SECRET={ipfs_api_secret}
SLACK_REPORTING_URL={slack_reporting_url}
WEB3_STORAGE_TOKEN={web3_storage_token}
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


def clone_lite_repo_with_slot(env_contents: str, slot_id, new_collector_instance, dev_mode=False, lite_node_branch='main'):
    repo_name = f'powerloom-testnet-v2-{slot_id}'
    if os.path.exists(repo_name):
        print(f'Deleting existing dir {repo_name}')
        os.system(f'rm -rf {repo_name}')
    os.system(f'cp -R snapshotter-lite-v2 {repo_name}')
    with open(f'{repo_name}/.env', 'w+') as f:
        f.write(env_contents)
    os.chdir(repo_name)
    # docker build and run
    print('--'*20 + f'Spinning up docker containers for slot {slot_id}' + '--'*20)
    # this works well when there are no existing screen sessions for the same slot
    # TODO: handle case when there are existing screen sessions for the same slot
    os.system(f'screen -dmS {repo_name}')
    if not dev_mode:
        if new_collector_instance:
            # run docker pull first
            print('Pulling docker images...')
            if lite_node_branch == 'main':
                image_tag = 'latest'
            else:
                image_tag = 'dockerify'
            print('Selecting image tag : ', image_tag)
            command = f"""
source .env
export IMAGE_TAG={image_tag}
if ! [ -x "$(command -v docker-compose)" ]; then
    docker compose -f docker-compose.yaml pull
else
    docker-compose -f docker-compose.yaml pull
fi
"""
            os.system(command)
            os.system(f'screen -S {repo_name} -p 0 -X stuff "./build.sh\n"')
        else:
            os.system(f'screen -S {repo_name} -p 0 -X stuff "./build.sh no_collector\n"')
    else:
        os.system(f'screen -S {repo_name} -p 0 -X stuff "./build-dev.sh\n"')
    print(f'Spawned screen session for docker containers {repo_name}') 
    # os.system('./build.sh')
    time.sleep(2)

def check_existing_networks(slot_ids):
    # Run docker network ls command
    result = subprocess.run(['docker', 'network', 'ls', '--format', '{{.Name}}'], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error running docker network ls: {result.stderr}")
        sys.exit(1)
    
    # Get the list of network names
    networks = result.stdout.strip().split('\n')
    
    # Create patterns for each slot ID
    patterns = [f'snapshotter-lite-v2-{slot_id}' for slot_id in slot_ids]
    
    # Find matching networks
    matching_networks = [net for net in networks if any(net == pattern for pattern in patterns)]
    
    if matching_networks:
        print("Found existing networks for the provided slot IDs:")
        for net in matching_networks:
            print(f"- {net}")
        print("""Please remove these networks before continuing. The following command can be used to remove the networks:
docker network rm <network_name>  ...OR...
docker network prune
""")
        sys.exit(1)
    else:
        print("No existing networks found for the provided slot IDs. Continuing...")

def main():
    load_dotenv('.env')
    dev_mode = os.getenv("DEV_MODE")
    if not dev_mode:
        dev_mode = False
    else:
        dev_mode = True if dev_mode.lower() == 'true' else False
    if dev_mode:
        print('*' * 40 + 'Running in dev mode' + '*' * 40)
    lite_node_branch = os.getenv("LITE_NODE_BRANCH")
    if not lite_node_branch:
        lite_node_branch = 'main'
    else:
        lite_node_branch = lite_node_branch.strip()
    source_rpc_url = os.getenv("SOURCE_RPC_URL")
    signer_addr = os.getenv("SIGNER_ACCOUNT_ADDRESS")
    wallet_holder_address = os.getenv("WALLET_HOLDER_ADDRESS")
    signer_pkey = os.getenv("SIGNER_ACCOUNT_PRIVATE_KEY")
    slot_rpc_url = os.getenv("SLOT_RPC_URL")
    slot_rpc_url_base = os.getenv("SLOT_RPC_URL_BASE")
    prost_rpc_url = os.getenv("PROST_RPC_URL")
    protocol_state_contract = os.getenv("PROTOCOL_STATE_CONTRACT")
    slot_contract_addr = os.getenv('SLOT_CONTROLLER_ADDRESS')
    slot_contract_addr_base = os.getenv('SLOT_CONTROLLER_ADDRESS_BASE')
    namespace = os.getenv("NAMESPACE")
    prost_chain_id = os.getenv("PROST_CHAIN_ID")
    powerloom_reporting_url = os.getenv("POWERLOOM_REPORTING_URL")
    prost_chain_id = os.getenv("PROST_CHAIN_ID")
    data_market_contract = os.getenv("DATA_MARKET_CONTRACT")
    if not all([
        source_rpc_url, signer_addr, signer_pkey, slot_rpc_url, prost_rpc_url, slot_contract_addr, 
        namespace, powerloom_reporting_url, protocol_state_contract, data_market_contract, prost_chain_id,
    ]):
        print('Missing environment variables')
        return
    w3 = Web3(Web3.HTTPProvider(slot_rpc_url))
    w3_base = Web3(Web3.HTTPProvider(slot_rpc_url_base))
    with open('MintContract.json', 'r') as f:
        nft_contract_abi = json.load(f)
    with open('MintContractBase.json', 'r') as f:
        nft_contract_base_abi = json.load(f)
    wallet_holder_address = Web3.to_checksum_address(wallet_holder_address)
    protocol_state_contract = Web3.to_checksum_address(protocol_state_contract)
    slot_contract_addr = Web3.to_checksum_address(slot_contract_addr)
    slot_contract_addr_base = Web3.to_checksum_address(slot_contract_addr_base)
    slot_contract = w3.eth.contract(
        address=slot_contract_addr, abi=nft_contract_abi,
    )
    slot_contract_base = w3_base.eth.contract(
        address=slot_contract_addr_base, abi=nft_contract_base_abi,
    )
    slot_ids = get_user_slots(slot_contract, wallet_holder_address)
    slot_ids_base = get_user_slots(slot_contract_base, wallet_holder_address)
    slot_ids.extend(slot_ids_base)
    local_collector_port = 50051
    core_api_port = 8002
    print(f'Got {len(slot_ids)} slots against wallet holder address')
    if not slot_ids:
        print('No slots found against wallet holder address')
        return
    elif len(slot_ids) > 1:
        if os.path.exists('snapshotter-lite-v2'):
            os.system('rm -rf snapshotter-lite-v2')
        print('Cloning lite node branch : ', lite_node_branch)
        os.system(f'git clone https://github.com/PowerLoom/snapshotter-lite-v2 --single-branch --branch ' + lite_node_branch)
        kill_screen_sessions()
        default_deploy = input('Do you want to deploy all slots? (y/n) : ')
        if default_deploy.lower() == 'y':
            # Check for existing networks with all the slot IDs
            check_existing_networks(slot_ids)
            for idx, each_slot in enumerate(slot_ids):
                if idx > 0:
                    os.chdir('..')
                print(f'Cloning for slot {each_slot}')
                if idx % LOCAL_COLLECTOR_NEW_BUILD_THRESHOLD == 0: 
                    if idx > 1:
                        local_collector_port += 1
                    new_collector_instance = True
                else:
                    new_collector_instance = False
                env_contents = env_file_template(
                    source_rpc_url=source_rpc_url,
                    signer_addr=signer_addr,
                    signer_pkey=signer_pkey,
                    prost_chain_id=prost_chain_id,
                    prost_rpc_url=prost_rpc_url,
                    protocol_state_contract=protocol_state_contract,
                    namespace=namespace,
                    powerloom_reporting_url=powerloom_reporting_url,
                    slot_id=each_slot,
                    local_collector_port=local_collector_port,
                    core_api_port=core_api_port,
                    data_market_contract=data_market_contract,
                    # this is fine since we can only have 100 max slots against a wallet
                    subnet_third_octet=idx + 1  # Simply use idx + 1 for unique values
                )
                clone_lite_repo_with_slot(env_contents, each_slot, new_collector_instance, dev_mode=dev_mode, lite_node_branch=lite_node_branch)
                core_api_port += 1
        else:
            custom_deploy_index = input('Enter custom index of slot IDs to deploy \n'
                                    '(indices begin at 0, enter in the format [begin, end])? (indices/n) : ')
            index_str = custom_deploy_index.strip('[]')
            begin, end = index_str.split(',')
            try:
                begin = int(begin)
                end = int(end)
            except ValueError:
                print('Invalid indices')
                return
            if begin < 0 or end < 0 or begin > end or end >= len(slot_ids):
                print('Invalid indices')
                return
            # Check for existing networks with the provided slot IDs
            check_existing_networks(slot_ids[begin:end+1])
            for idx, each_slot in enumerate(slot_ids[begin:end+1], start=begin):
                if idx > begin:
                    os.chdir('..')
                if idx % LOCAL_COLLECTOR_NEW_BUILD_THRESHOLD == 0: 
                    if idx > begin + 1:
                        local_collector_port += 1
                    new_collector_instance = True
                else:
                    new_collector_instance = False
                print(f'Cloning for slot {each_slot}')
                env_contents = env_file_template(
                    source_rpc_url=source_rpc_url,
                    signer_addr=signer_addr,
                    signer_pkey=signer_pkey,
                    prost_chain_id=prost_chain_id,
                    prost_rpc_url=prost_rpc_url,
                    protocol_state_contract=protocol_state_contract,
                    namespace=namespace,
                    powerloom_reporting_url=powerloom_reporting_url,
                    slot_id=each_slot,
                    local_collector_port=local_collector_port,
                    core_api_port=core_api_port,
                    data_market_contract=data_market_contract,
                    # this is fine since we can only have 100 max slots against a wallet
                    subnet_third_octet=idx + 1  # Simply use idx + 1 for unique values
                )
                clone_lite_repo_with_slot(env_contents, each_slot, new_collector_instance, dev_mode=dev_mode, lite_node_branch=lite_node_branch)
                core_api_port += 1
    else:
        kill_screen_sessions()
        check_existing_networks(slot_ids)
        if os.path.exists('snapshotter-lite-v2'):
            os.system('rm -rf snapshotter-lite-v2')
        os.system(f'git clone https://github.com/PowerLoom/snapshotter-lite-v2 --single-branch --branch ' + lite_node_branch)
        env_contents = env_file_template(
            source_rpc_url=source_rpc_url,
            signer_addr=signer_addr,
            signer_pkey=signer_pkey,
            prost_chain_id=prost_chain_id,
            prost_rpc_url=prost_rpc_url,
            protocol_state_contract=protocol_state_contract,
            namespace=namespace,
            powerloom_reporting_url=powerloom_reporting_url,
            slot_id=slot_ids[0],
            local_collector_port=local_collector_port,
            core_api_port=core_api_port,
            data_market_contract=data_market_contract,
            subnet_third_octet=1
        )
        clone_lite_repo_with_slot(env_contents, slot_ids[0], True, dev_mode=dev_mode, lite_node_branch=lite_node_branch)
        # print(env_contents)

if __name__ == '__main__':
    main()
