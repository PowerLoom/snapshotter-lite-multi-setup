import os
import subprocess
import sys
import time
import json
import argparse
from dotenv import load_dotenv
from web3 import Web3
import psutil
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from threading import Semaphore

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

def deploy_single_node(slot_id: int, idx: int, data_market_namespace: str, data_market_contract_number: int, 
                      protocol_state: dict, full_namespace: str, base_dir: str, semaphore=None, **kwargs):
    """Deploy a single node in a thread-safe manner"""
    try:
        # Use semaphore to control concurrent deployments if provided
        if semaphore:
            # print(f"⏳ [Worker {threading.current_thread().name}] Waiting for slot to deploy {slot_id}...")
            with semaphore:
                return _deploy_single_node_impl(slot_id, idx, data_market_namespace, data_market_contract_number,
                                               protocol_state, full_namespace, base_dir, **kwargs)
        else:
            return _deploy_single_node_impl(slot_id, idx, data_market_namespace, data_market_contract_number,
                                           protocol_state, full_namespace, base_dir, **kwargs)
    except Exception as e:
        return (slot_id, "error", f"Failed to deploy node {slot_id}: {str(e)}")


def _deploy_single_node_impl(slot_id: int, idx: int, data_market_namespace: str, data_market_contract_number: int, 
                            protocol_state: dict, full_namespace: str, base_dir: str, **kwargs):
    """Implementation of single node deployment"""
    try:
        print(f'🟠 [Worker {threading.current_thread().name}] Starting deployment for slot {slot_id}')
        
        # Determine collector profile
        if idx > 0:
            collector_profile_string = '--no-collector --no-autoheal-launch'
        else:
            collector_profile_string = ''
        
        repo_name = f'powerloom-mainnet-v2-{slot_id}-{data_market_namespace}'
        repo_path = os.path.join(base_dir, repo_name)
        
        # Clean up existing directory
        if os.path.exists(repo_path):
            print(f'Deleting existing dir {repo_name}')
            subprocess.run(['rm', '-rf', repo_path], check=True)
        
        # Copy template directory
        subprocess.run(['cp', '-R', os.path.join(base_dir, 'snapshotter-lite-v2'), repo_path], check=True)
        
        # Generate environment file
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
        
        env_file_path = os.path.join(repo_path, f'.env-{full_namespace}')
        with open(env_file_path, 'w+') as f:
            f.write(env_file_contents)
        
        # Launch in screen session
        print('--'*20 + f'Spinning up docker containers for slot {slot_id}' + '--'*20)
        
        # Create and launch screen session
        screen_cmd = f"""cd {repo_path} && screen -dmS {repo_name} bash -c './build.sh {collector_profile_string} --skip-credential-update --data-market-contract-number {data_market_contract_number}'"""
        subprocess.run(screen_cmd, shell=True, check=True)
        
        # Wait for the deployment to reach a stable state
        # This ensures we don't release the semaphore too early
        if idx == 0:
            # First node needs more time for collector initialization
            time.sleep(5)
        else:
            # Subsequent nodes need less time but still need to wait
            # for Docker containers to actually start
            time.sleep(3)
        
        return (slot_id, "success", f"Node {slot_id} deployed successfully")
    
    except Exception as e:
        return (slot_id, "error", f"Failed to deploy node {slot_id}: {str(e)}")


def run_snapshotter_lite_v2(deploy_slots: list, data_market_contract_number: int, data_market_namespace: str, **kwargs):
    protocol_state = DATA_MARKET_CHOICES_PROTOCOL_STATE[data_market_namespace]
    full_namespace = f'{POWERLOOM_CHAIN}-{data_market_namespace}-{SOURCE_CHAIN}'
    base_dir = os.getcwd()
    
    # Check if sequential mode is requested
    sequential_mode = kwargs.get('sequential', False)
    
    if sequential_mode:
        print("📌 Running in sequential mode (parallel deployment disabled)")
        # Original sequential logic
        for idx, slot_id in enumerate(deploy_slots):
            result = deploy_single_node(
                slot_id, idx, data_market_namespace, data_market_contract_number,
                protocol_state, full_namespace, base_dir, **kwargs
            )
            
            if result[1] == "error":
                print(f"❌ Failed to deploy node {slot_id}: {result[2]}")
                continue
            
            sleep_duration = 30 if idx == 0 else 10
            print(f'Sleeping for {sleep_duration} seconds to allow docker containers to spin up...')
            time.sleep(sleep_duration)
        return
    
    # Parallel deployment mode
    # Phase 1: Deploy first node with collector
    if deploy_slots:
        print("🚀 Phase 1: Deploying first node with collector service...")
        result = deploy_single_node(
            deploy_slots[0], 0, data_market_namespace, data_market_contract_number,
            protocol_state, full_namespace, base_dir, **kwargs
        )
        
        if result[1] == "error":
            print(f"❌ Failed to deploy first node: {result[2]}")
            return
        
        print(f"✅ First node deployed successfully. Waiting 30 seconds for collector initialization...")
        time.sleep(30)
    
    # Phase 2: Parallel deployment of remaining nodes
    if len(deploy_slots) > 1:
        print(f"\n🚀 Phase 2: Deploying {len(deploy_slots) - 1} remaining nodes in parallel...")
        
        # Determine number of workers
        cpu_cores = psutil.cpu_count(logical=True)
        default_workers = min(max(4, cpu_cores // 2), 8)
        max_workers = kwargs.get('parallel_workers')
        
        if max_workers is None:
            max_workers = default_workers
            print(f"📊 Using {max_workers} parallel workers (auto-detected based on {cpu_cores} CPU cores)")
        else:
            print(f"📊 Using {max_workers} parallel workers (user-specified, detected {cpu_cores} CPU cores)")
        
        # Deploy remaining nodes in batches with controlled concurrency
        print(f"📋 Starting parallel deployment of {len(deploy_slots) - 1} nodes with {max_workers} workers...")
        
        # Create a semaphore to limit concurrent deployments
        deployment_semaphore = Semaphore(max_workers)
        
        # Process nodes in batches
        remaining_slots = deploy_slots[1:]
        batch_size = max_workers * 2  # Process 2x workers at a time
        completed = 0
        total = len(remaining_slots)
        
        for batch_start in range(0, len(remaining_slots), batch_size):
            batch_end = min(batch_start + batch_size, len(remaining_slots))
            batch = remaining_slots[batch_start:batch_end]
            batch_num = (batch_start // batch_size) + 1
            total_batches = (len(remaining_slots) + batch_size - 1) // batch_size
            
            print(f"\n📦 Processing batch {batch_num}/{total_batches} ({len(batch)} nodes)...")
            
            with ThreadPoolExecutor(max_workers=max_workers * 2) as executor:
                # Create a mapping of future to slot_id for tracking
                future_to_slot = {}
                for idx_in_batch, (idx, slot_id) in enumerate(enumerate(batch, 1)):
                    actual_idx = batch_start + idx
                    future = executor.submit(
                        deploy_single_node, slot_id, actual_idx + 1, data_market_namespace, 
                        data_market_contract_number, protocol_state, full_namespace, base_dir, 
                        semaphore=deployment_semaphore, **kwargs
                    )
                    future_to_slot[future] = slot_id
                
                # Monitor progress for this batch
                for future in as_completed(future_to_slot, timeout=300):
                    slot_id = future_to_slot[future]
                    try:
                        result = future.result()
                        completed += 1
                        if result[1] == "success":
                            print(f"✅ [{completed}/{total}] {result[2]}")
                        else:
                            print(f"❌ [{completed}/{total}] {result[2]}")
                    except Exception as e:
                        completed += 1
                        print(f"❌ [{completed}/{total}] Node {slot_id} deployment failed with exception: {e}")
            
            # Check system state between batches
            if batch_end < len(remaining_slots):
                print(f"\n🔍 Checking system state before next batch...")
                
                # Wait for Docker pulls to stabilize
                wait_time = 0
                max_wait = 30
                while wait_time < max_wait:
                    docker_pull_lock = "/tmp/powerloom_docker_pull.lock"
                    if os.path.exists(docker_pull_lock):
                        print(f"⏳ Docker pulls in progress, waiting... ({wait_time}s)")
                        time.sleep(5)
                        wait_time += 5
                    else:
                        break
                
                # Brief pause between batches
                print("⏸️  Pausing 5 seconds before next batch...")
                time.sleep(5)
        
        # Check if deployments are actually complete
        print("\n⏳ Waiting for all background deployments to complete...")
        print("📊 Checking Docker activity...")
        
        # Wait for Docker pulls to complete
        max_wait_time = 300  # 5 minutes max
        check_interval = 5
        elapsed = 0
        
        while elapsed < max_wait_time:
            # Check if docker pull lock exists (indicates ongoing pulls)
            docker_pull_lock = "/tmp/powerloom_docker_pull.lock"
            if os.path.exists(docker_pull_lock):
                print(f"🔄 Docker pulls still in progress... ({elapsed}s elapsed)")
                time.sleep(check_interval)
                elapsed += check_interval
                continue
            
            # Check for active docker-compose processes in screen sessions
            try:
                # Count active build.sh processes
                result = subprocess.run(
                    "ps aux | grep -E 'build\\.sh|docker-compose.*up' | grep -v grep | wc -l",
                    shell=True, capture_output=True, text=True
                )
                active_builds = int(result.stdout.strip())
                
                if active_builds > 0:
                    print(f"🔄 {active_builds} deployments still active... ({elapsed}s elapsed)")
                    time.sleep(check_interval)
                    elapsed += check_interval
                else:
                    print("✅ All background deployments appear to be complete!")
                    break
            except:
                # If we can't check, wait a bit more
                time.sleep(check_interval)
                elapsed += check_interval
        
        if elapsed >= max_wait_time:
            print("⚠️ Timeout waiting for deployments to complete. Some may still be running in background.")
        
        # Show active screen sessions
        print("\n📺 Active screen sessions:")
        try:
            result = subprocess.run("screen -ls | grep powerloom || echo 'No active sessions found'", 
                                  shell=True, capture_output=True, text=True)
            print(result.stdout.strip())
        except:
            pass
        
        print("\n✅ Deployment process completed!")

def docker_running():
    try:
        # Check if Docker is running
        subprocess.check_output(['docker', 'info'])
        return True
    except subprocess.CalledProcessError:
        return False

def calculate_connection_refresh_interval(num_slots):
    # Base minimum interval
    MIN_INTERVAL = 60  # seconds
    
    if num_slots <= 10:
        return MIN_INTERVAL
    
    # Linear scaling with some adjustments
    # Formula: 4 seconds per slot + baseline of 60
    interval = (4 * num_slots) + MIN_INTERVAL
    
    # Cap at reasonable maximum
    MAX_INTERVAL = 900  # 15 minutes
    return min(interval, MAX_INTERVAL)

def main(data_market_choice: str, non_interactive: bool = False, latest_only: bool = False, use_env_refresh_interval: bool = False, parallel_workers: int = None, sequential: bool = False):
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
        deploy_all_slots = input('☑️ Do you want to deploy all slots? (y/n) ')
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
    
    # Display deployment configuration
    print("\n📋 Deployment Configuration:")
    cpu_cores = psutil.cpu_count(logical=True)
    if parallel_workers is not None:
        print(f"   • Parallel Workers: {parallel_workers} (user-specified)")
    else:
        default_workers = min(max(4, cpu_cores // 2), 8)
        print(f"   • Parallel Workers: {default_workers} (auto-detected from {cpu_cores} CPU cores)")
    
    if sequential:
        print("   • Mode: Sequential (parallel deployment disabled)")
    else:
        print("   • Mode: Parallel")
    
    print(f"   • Total Slots: {len(deploy_slots)}")
    if not sequential and len(deploy_slots) > 1:
        workers = parallel_workers if parallel_workers is not None else default_workers
        estimated_time = 30 + ((len(deploy_slots) - 1) // workers + 1) * 10
        print(f"   • Estimated Time: ~{estimated_time} seconds")
    print()
    
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
    
    # Calculate appropriate connection refresh interval based on number of slots
    suggested_refresh_interval = calculate_connection_refresh_interval(len(deploy_slots))
    connection_refresh_interval = os.getenv('CONNECTION_REFRESH_INTERVAL_SEC')
    connection_refresh_interval = int(connection_refresh_interval) if connection_refresh_interval else 0
    if use_env_refresh_interval:
        if not connection_refresh_interval:
            print('🟡 CONNECTION_REFRESH_INTERVAL_SEC is not set in .env file, using calculated value...')
            connection_refresh_interval = suggested_refresh_interval
        else:
            if connection_refresh_interval != suggested_refresh_interval:
                print(f'⚠️ Current CONNECTION_REFRESH_INTERVAL_SEC ({connection_refresh_interval}s) is different from the suggested value ({suggested_refresh_interval}s) for {len(deploy_slots)} slots\n'
                       'BE WARNED: This may cause connection instability under high load!\n'
                       '⚡ Moving ahead with overridden value from environment...')      
    else:
        if connection_refresh_interval != suggested_refresh_interval:
            if (connection_refresh_interval == 0):
                print(f'✔️ Using suggested connection refresh interval value of {suggested_refresh_interval}s for {len(deploy_slots)} slots')
            else:
                print(f'⚠️ Current CONNECTION_REFRESH_INTERVAL_SEC ({connection_refresh_interval}s) in .env file is different from the suggested value ({suggested_refresh_interval}s) for {len(deploy_slots)} slots\n'
                       '⛑️ Using suggested value for safety... If you know what you are doing, you can override this by passing --use-env-connection-refresh-interval to the script')
            connection_refresh_interval = suggested_refresh_interval
    
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
        connection_refresh_interval_sec=connection_refresh_interval,
        parallel_workers=parallel_workers,
        sequential=sequential,
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PowerLoom mainnet multi-node setup')
    parser.add_argument('--data-market', choices=['1', '2'],
                    help='Data market choice (1: AAVEV3, 2: UNISWAPV2)')
    parser.add_argument('-y', '--yes', action='store_true',
                    help='Deploy all nodes without prompting for confirmation')
    parser.add_argument('--latest-only', action='store_true',
                    help='Deploy only the latest (highest) slot')
    parser.add_argument('--use-env-connection-refresh-interval', action='store_true',
                    help='Use CONNECTION_REFRESH_INTERVAL_SEC from environment instead of calculating based on slots')
    parser.add_argument('--parallel-workers', type=int, metavar='N',
                    help='Number of parallel workers for deployment (1-8, default: auto-detect based on CPU cores)')
    parser.add_argument('--sequential', action='store_true',
                    help='Disable parallel deployment and use sequential mode (backward compatibility)')
    
    args = parser.parse_args()
    
    data_market = args.data_market if args.data_market else '0'
    
    # Validate parallel workers if provided
    if args.parallel_workers is not None:
        if args.parallel_workers < 1 or args.parallel_workers > 8:
            parser.error("--parallel-workers must be between 1 and 8")
    
    main(data_market_choice=data_market, 
         non_interactive=args.yes, 
         latest_only=args.latest_only,
         use_env_refresh_interval=args.use_env_connection_refresh_interval,
         parallel_workers=args.parallel_workers,
         sequential=args.sequential)
