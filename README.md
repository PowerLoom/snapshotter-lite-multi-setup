# Multi node setup for multiple Powerloom Snapshotter Lite: Protocol V2 slot holders on Linux VPS


## Table of Contents

- [Multi node setup for multiple Powerloom Snapshotter Lite: Protocol V2 slot holders on Linux VPS](#multi-node-setup-for-multiple-powerloom-snapshotter-lite-protocol-v2-slot-holders-on-linux-vps)
  - [Table of Contents](#table-of-contents)
  - [0. Preparation](#0-preparation)
  - [1. System Check and Environment Setup](#1-system-check-and-environment-setup)
    - [1.1 Run Diagnostics](#11-run-diagnostics)
    - [1.2 Initialize Environment](#12-initialize-environment)
  - [1. Setup Python environment](#1-setup-python-environment)
    - [1.1 Install `pyenv`](#11-install-pyenv)
    - [1.2 Install `pyenv-virtualenv`](#12-install-pyenv-virtualenv)
  - [2. Setup](#2-setup)
    - [2.1. Pre-mainnet and testnet snapshotters: Running mainnet setup for the first time](#21-pre-mainnet-and-testnet-snapshotters-running-mainnet-setup-for-the-first-time)
      - [Bootstrap](#bootstrap)
      - [2.1.2 Run the deploy script](#212-run-the-deploy-script)
      - [2.1.3. Deploying a subset of slots](#213-deploying-a-subset-of-slots)
      - [2.1.4. Deploying all slots](#214-deploying-all-slots)
    - [2.2 Deploy subset of slots with different configs](#22-deploy-subset-of-slots-with-different-configs)
  - [3. Monitoring, diagnostics and cleanup](#3-monitoring-diagnostics-and-cleanup)
    - [3.1 Cleanup\[optional\]](#31-cleanupoptional)
      - [3.1.1 Stop and remove all powerloom containers](#311-stop-and-remove-all-powerloom-containers)
      - [3.1.2 Remove all Docker subnets assigned to the snapshotter-lite containers](#312-remove-all-docker-subnets-assigned-to-the-snapshotter-lite-containers)
      - [3.1.3 Cleanup stale images and networks and cache](#313-cleanup-stale-images-and-networks-and-cache)
  - [\[OPTIONAL\] Dev mode setup](#optional-dev-mode-setup)

> [!NOTE]
> This setup is for Lite nodes participating in the latest V2 of Powerloom Protocol with multiple data markets. [Protocol V1 setup](https://github.com/PowerLoom/snapshotter-lite-multi-setup/tree/main) is deprecated and its data markets are archived. Your submission data, rewards on it are finalized and recorded as [announced on Discord](https://discord.com/channels/777248105636560948/1146931631039463484/1242876184509812847).

## 0. Preparation

Clone this repository and change into the repository's directory. All commands will be run within there henceforth.

```bash
git clone https://github.com/PowerLoom/snapshotter-lite-multi-setup.git
cd snapshotter-lite-multi-setup
```

## 1. System Check and Environment Setup

### 1.1 Run Diagnostics
First, run the diagnostic tool to check your system and clean up any existing deployments:
```bash
./diagnose.sh
```
This will help you:
- Verify system requirements
- Detect and manage running instances
- Clean up stale deployments and Docker resources
- Ensure a clean setup environment

### 1.2 Initialize Environment
```bash
./bootstrap.sh
```
This will:
- Back up any existing configuration
- Guide you through setting up required variables
- Create a new .env file with your settings
- This step will require you to inform the RPC URL, snapshotter owner wallet address, signer wallet address and signer wallet private key. When you paste or type the private key, it will look like nothing is typed or pasted, but that´s due to the sensitive information, simply paste and press enter!

## 1. Setup Python environment

This is of utmost importance. We want to setup an isolated virtual environment with the right Python version and modules without affecting any global Python installations on the VPS or your local machine.

### 1.1 Install `pyenv`

Detailed instructions and troubleshotting can be found on the [pyenv Github repo README](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation). In general, the following should take care of the installation on an Ubuntu VPS.

```
sudo apt install build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev curl libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
curl https://pyenv.run | bash
pyenv install 3.11.5
source ~/.bashrc
```
### 1.2 Install `pyenv-virtualenv`

Detailed instructions can be [found here](https://github.com/pyenv/pyenv-virtualenv).

```
git clone https://github.com/pyenv/pyenv-virtualenv.git $(pyenv root)/plugins/pyenv-virtualenv
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
pyenv virtualenv 3.11.5 ss_lite_multi_311
pyenv local ss_lite_multi_311
```

## 2. Setup

```bash
# install all python requirements
pip install -r requirements.txt
```

### 2.1. Pre-mainnet and testnet snapshotters: Running mainnet setup for the first time

If you have only run the node so far for the Lite Node testnet and pre-mainnet, we recommend you to follow the steps below to setup the mainnet snapshotter correctly.

#### Bootstrap

Run the bootstrap script to backup the old .env file and generate a new one that will help you participate in the mainnet

```bash
./bootstrap.sh
```

At the following prompt, enter `y` to backup the old .env file.

```
🟢 .env file already found to be initialized! If you wish to change any of the values, please backup the .env file at the following prompt.
Do you wish to backup the .env file?
```

It will show you the old .env file and offer you an option to keep the existing values or enter new values.
```
🟢 .env file backed up to .env.backup.20250113023753
creating .env file...
creating .env file...
🫸 ▶︎ Please enter the WALLET_HOLDER_ADDRESS (press enter to keep current value: <current wallet holder address>):

🫸 ▶︎ Please enter the SOURCE_RPC_URL (press enter to keep current value: ): 


🫸 ▶︎ Please enter the SIGNER_ACCOUNT_ADDRESS (press enter to keep current value: <current signer account address>): 

🫸 ▶︎ Please enter the SIGNER_ACCOUNT_PRIVATE_KEY (press enter to keep current value: <current signer account private key>): 

🫸 ▶︎ Please enter the TELEGRAM_CHAT_ID (press enter to skip): 

🟢 .env file created successfully!
```

#### 2.1.2 Run the deploy script

```bash
python multi_clone.py
```

#### 2.1.3. Deploying a subset of slots
Enter `n` when asked if you want to deploy all slots. Proceed with the begin and end slot IDs for your deployment.

#### 2.1.4. Deploying all slots
Enter `y` when asked if you want to deploy all slots.

You will see an output like the following:

```
🟢 .env file found with following env variables...
SOURCE_RPC_URL=<your data source rpc url>
SIGNER_ACCOUNT_ADDRESS=<your signer account address>
WALLET_HOLDER_ADDRESS=<your slot holding wallet address>
PROST_RPC_URL=https://rpc.powerloom.network
PROST_CHAIN_ID=7865
TELEGRAM_CHAT_ID=<your telegram chat id>
POWERLOOM_REPORTING_URL=https://mainnet-lite-reporting.powerloom.network
Found n slots for wallet holder address
[list of slot ids]
☑️ Do you want to deploy all slots? (y/n)n
🫸 ▶︎ Enter the start slot ID: xxx1
🫸 ▶︎ Enter the end slot ID: xxx2
```

Choose the data market namespace you want to deploy, UniswapV2 by default.

```
🔍 Select a data market contract (UNISWAPV2 is default):
1. AAVEV3
2. UNISWAPV2

🫸 ▶︎ Please enter your choice (1/2) [default: 2 - UNISWAPV2]: 2
```

And you will see the following output:

```
🟠 Deploying node for slot xxx1 in data market UNISWAPV2
----------------------------------------Spinning up docker containers for slot xxx1----------------------------------------
Sleeping for 30 seconds to allow docker containers to spin up...

...

🟠 Deploying node for slot xxx2 in data market UNISWAPV2
----------------------------------------Spinning up docker containers for slot xxx2----------------------------------------
Sleeping for 10 seconds to allow docker containers to spin up...
```
### 2.2 Deploy subset of slots with different configs

> [!TIP]
> This is useful if you want to deploy your slots in custom ranges with different configs, for eg the SOURCE_RPC_URL or any of the other configurations prompted to you during [bootstrap](#bootstrap).

The same instructions as above apply here in the following sequence:

1. During the bootstrap, choose `y` to backup the old .env file.
2. In the next prompt, enter the new values for the fields you want to change.
3. Run the deploy script with the new .env file as shown in [2.1.2 Run the deploy script](#212-run-the-deploy-script).

## 3. Monitoring, diagnostics and cleanup

The multi setup comes bundled with a diagnostic and cleanup script.

```bash
./diagnose.sh -y
```
> [!NOTE]
> The `-y` flag is recommended to be used as it will skip all the prompts and cleanup existing Powerloom containers and legacy Docker networks without asking for confirmation. If you want to run the script with prompts, you can run it without the `-y` flag.

The following output may vary depending on whether you have run snapshotter node(s) before this setup or not.

```
./diagnose.sh
🔍 Starting PowerLoom Node Diagnostics...

📦 Checking Docker installation...
✅ Docker is installed and running

🐳 Checking docker-compose...
✅ Docker Compose is available

🔌 Checking default ports...
⚠️ Port 8002 is in use
✅ Next available Core API port: 8003
⚠️ Port 50051 is in use
✅ Next available Collector port: 50052

🔍 Checking existing PowerLoom containers...
Found existing PowerLoom containers:
snapshotter-lite-v2-xxx1-mainnet-UNISWAPV2-ETH
snapshotter-lite-local-collector-xxx1-mainnet-UNISWAPV2-ETH
snapshotter-lite-v2-xxx2-mainnet-UNISWAPV2-ETH
```
If you want to cleanup the existing containers, follow along to the next section

### 3.1 Cleanup[optional]

> [!TIP]
> This is particularly useful if you find your nodes are not running as expected and want a fresh start.


#### 3.1.1 Stop and remove all powerloom containers


If the diagnostic script finds any running containers tagged with `snapshotter-lite`, it will ask you if you want to stop and remove them.

Select `y` at the following prompt and you see some logs like the following:

```
Would you like to stop and remove existing PowerLoom containers? (y/n): y 

Stopping running containers... (timeout: 30s per container)
Attempting to stop container snapshotter-lite-v2-xxx1-mainnet-UNISWAPV2-ETH...
snapshotter-lite-v2-xxx1-mainnet-UNISWAPV2-ETH
Attempting to stop container snapshotter-lite-local-collector-xxx1-mainnet-UNISWAPV2-ETH...
snapshotter-lite-local-collector-xxx1-mainnet-UNISWAPV2-ETH

Removing containers...
Removing container snapshotter-lite-v2-xxx1-mainnet-UNISWAPV2-ETH...
Removing container snapshotter-lite-local-collector-xxx1-mainnet-UNISWAPV2-ETH...

Removing container snapshotter-lite-v2-xxx2-mainnet-UNISWAPV2-ETH...
```


#### 3.1.2 Remove all Docker subnets assigned to the snapshotter-lite containers

Enter `y` at the following prompt and you see some logs like the following:

```
Would you like to remove existing PowerLoom networks? (y/n): y

Removing networks...
snapshotter-lite-v2-xxx1-mainnet-UNISWAPV2-ETH
snapshotter-lite-v2-xxx2-mainnet-UNISWAPV2-ETH
✅ Networks removed
```

#### 3.1.3 Cleanup stale images and networks and cache

> [!NOTE]
> This is a cleanup step that removes all stale images, networks and cache from Docker. Proceed only if all other attempts at running the node have failed after following our guides.

Enter `y` at the following prompt and you see some logs like the following. Press `y` again at the end to confirm with Docker.

```
Would you like to remove unused Docker resources (only unused images, networks, and cache)? (y/n): y 

Removing unused Docker resources...

Running docker network prune...

Running docker system prune...
WARNING! This will remove:
  - all stopped containers
  - all networks not used by at least one container
  - all images without at least one container associated to them
  - all build cache

Are you sure you want to continue? [y/N] y

Deleted Images:
untagged: ghcr.io/powerloom/snapshotter-lite-v2:latest
untagged: ghcr.io/powerloom/snapshotter-lite-v2@sha256:15e05050bbf1473a3b4345a188c44bb37fb343f89d24f9ce731e3c3df190ec98
deleted: sha256:33d723744d4cb306c9be663247464f497698682fb0d577290831114b825bc84a

Total reclaimed space: 1.614GB
✅ Cleanup complete

✅ Diagnostic check complete
```

If you encounter any issues, please contact us on [discord](https://discord.com/invite/powerloom).


## [OPTIONAL] Dev mode setup

> [!WARNING]
>This section is not required if you are not planning on running a customized setup. For any related assistance, contact us on [discord](https://discord.com/invite/powerloom).


If you wish to customize the docker containers being launched by not using the published images from Powerloom, and instead clone the underlying snapshotter components locally and building their images, we support that as well now.

Ref: [Step 2](#2-run-the-setup), after running `./init.sh` , you can edit the generated `.env` file for the following fields

```bash
DEV_MODE=False  # you can set this to True
# subseqeuently you can specify the branch of https://github.com/PowerLoom/snapshotter-lite-v2 that you wish to run
LITE_NODE_BRANCH=main
```
