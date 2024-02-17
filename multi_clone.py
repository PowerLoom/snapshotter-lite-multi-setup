import os
import json
import time
from web3 import Web3
from dotenv import load_dotenv
from os import environ

# get from slot contract and set in redis
def get_user_slots(contract_obj, signer_addr):
    holder_slots = contract_obj.functions.getUserOwnedSlotIds(signer_addr).call()
    print(holder_slots)
    return holder_slots


def env_file_template(
        source_rpc_url: str,
        signer_addr: str,
        signer_pkey: str,
        prost_chain_id: str,
        prost_rpc_url: str,
        namespace: str,
        relayer_host: str,
        protocol_state_contract: str,
        powerloom_reporting_url: str,
        slot_id: str,
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
RELAYER_HOST={relayer_host}
PROTOCOL_STATE_CONTRACT={protocol_state_contract}
POWERLOOM_REPORTING_URL={powerloom_reporting_url}
SLOT_ID={slot_id}
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


def clone_lite_repo_with_slot(env_contents: str, slot_id):
    repo_name = f'powerloom-testnet-{slot_id}'
    if os.path.exists(repo_name):
        print(f'Deleting existing dir {repo_name}')
        os.system(f'rm -rf {repo_name}')
    os.system(f'cp -R snapshotter-lite {repo_name}')
    with open(f'{repo_name}/.env', 'w+') as f:
        f.write(env_contents)
    os.chdir(repo_name)
    # docker build and run
    print('--'*20 + f'Spinning up docker containers for slot {slot_id}' + '--'*20)
    # this works well when there are no existing screen sessions for the same slot
    # TODO: handle case when there are existing screen sessions for the same slot
    os.system(f'screen -dmS {repo_name}')
    os.system(f'screen -S {repo_name} -p 0 -X stuff "./build.sh\n"')
    print(f'Spawned screen session for docker containers {repo_name}') 
    # os.system('./build.sh')

def main():
    load_dotenv('.env')
    source_rpc_url = os.getenv("SOURCE_RPC_URL")
    signer_addr = os.getenv("SIGNER_ACCOUNT_ADDRESS")
    wallet_holder_address = os.getenv("WALLET_HOLDER_ADDRESS")
    signer_pkey = os.getenv("SIGNER_ACCOUNT_PRIVATE_KEY")
    slot_rpc_url = os.getenv("SLOT_RPC_URL")
    prost_rpc_url = os.getenv("PROST_RPC_URL")
    protocol_state_contract = os.getenv("PROTOCOL_STATE_CONTRACT")
    slot_contract_addr = os.getenv('SLOT_CONTROLLER_ADDRESS')
    relayer_host = os.getenv("RELAYER_HOST")
    namespace = os.getenv("NAMESPACE")
    powerloom_reporting_url = os.getenv("POWERLOOM_REPORTING_URL")
    prost_chain_id = os.getenv("PROST_CHAIN_ID")
    w3 = Web3(Web3.HTTPProvider(slot_rpc_url))
    with open('MintContract.json', 'r') as f:
        protocol_abi = json.load(f)
    slot_contract = w3.eth.contract(
        address=slot_contract_addr, abi=protocol_abi,
    )
    slot_ids = get_user_slots(slot_contract, wallet_holder_address)
    print(f'Got {len(slot_ids)} slots against wallet holder address')
    if not slot_ids:
        print('No slots found against wallet holder address')
        return
    elif len(slot_ids) > 1:
        if os.path.exists('snapshotter-lite'):
            os.system('rm -rf snapshotter-lite')
        os.system(f'git clone https://github.com/PowerLoom/snapshotter-lite')
        kill_screen_sessions()
        custom_deploy_index = input('Do you want to deploy a custom index of slot IDs \n'
                                    '(indices begin at 0, enter in the format [begin, end])? (indices/n) : ')
        if custom_deploy_index.lower() == 'n':
            batch_size = input('Enter batch size into which you wish to split the deployment : ')
            try:
                batch_size = int(batch_size)
            except ValueError:
                print('Invalid batch size')
                return
            if batch_size < 1:
                print('Invalid batch size')
                return
            if batch_size > len(slot_ids):
                print('Batch size is greater than total slots')
                return
            slot_ids_batched = [slot_ids[i:i + batch_size] for i in range(0, len(slot_ids), batch_size)]
            for idx, batch in enumerate(slot_ids_batched):
                print(f'Cloning for batch {idx + 1} of {len(slot_ids_batched)}')
                for idx, each_slot in enumerate(batch):
                    if idx > 0:
                        os.chdir('..')
                    print(f'Cloning for slot {each_slot}')
                    env_contents = env_file_template(
                        source_rpc_url=source_rpc_url,
                        signer_addr=signer_addr,
                        signer_pkey=signer_pkey,
                        prost_chain_id=prost_chain_id,
                        prost_rpc_url=prost_rpc_url,
                        protocol_state_contract=protocol_state_contract,
                        namespace=namespace,
                        relayer_host=relayer_host,
                        powerloom_reporting_url=powerloom_reporting_url,
                        slot_id=each_slot
                    )
                    clone_lite_repo_with_slot(env_contents, each_slot)
        else:
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
            for idx, each_slot in enumerate(slot_ids[begin:end+1]):
                if idx > 0:
                    os.chdir('..')
                print(f'Cloning for slot {each_slot}')
                env_contents = env_file_template(
                    source_rpc_url=source_rpc_url,
                    signer_addr=signer_addr,
                    signer_pkey=signer_pkey,
                    prost_chain_id=prost_chain_id,
                    prost_rpc_url=prost_rpc_url,
                    protocol_state_contract=protocol_state_contract,
                    namespace=namespace,
                    relayer_host=relayer_host,
                    powerloom_reporting_url=powerloom_reporting_url,
                    slot_id=each_slot
                )
                clone_lite_repo_with_slot(env_contents, each_slot)
    else:
        kill_screen_sessions()
        if os.path.exists('snapshotter-lite'):
            os.system('rm -rf snapshotter-lite')
        os.system(f'git clone https://github.com/PowerLoom/snapshotter-lite')
        env_contents = env_file_template(
            source_rpc_url=source_rpc_url,
            signer_addr=signer_addr,
            signer_pkey=signer_pkey,
            prost_chain_id=prost_chain_id,
            prost_rpc_url=prost_rpc_url,
            protocol_state_contract=protocol_state_contract,
            namespace=namespace,
            relayer_host=relayer_host,
            powerloom_reporting_url=powerloom_reporting_url,
            slot_id=slot_ids[0]
        )
        clone_lite_repo_with_slot(env_contents, slot_ids[0])
        # print(env_contents)

if __name__ == '__main__':
    main()
