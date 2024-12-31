# 🚀 PowerLoom Protocol V2: Multi-Node Setup Release for multiple data markets

We're excited to announce the release of our Multi-Node Setup Framework for PowerLoom Protocol V2! This framework significantly simplifies the process of running PowerLoom nodes, whether you're operating a single node or managing multiple slots **for multiple data markets**.

### 🔮 Underlying `snapshotter-lite-v2` also has a latest release with fixes that will ensure your nodes are able to submit snapshots to the exact sequencer meant for your data market. https://github.com/PowerLoom/snapshotter-lite-v2/releases/tag/v2.2 . Please pull the latest changes from the repo and restart your nodes.

### ✅ The latest snapshotter dashboard now also shows the submission counts for each data market. https://snapshotter-dashboard.powerloom.network/

## 🌟 Key Features
- Single command setup: `./bootstrap.sh`
- Cleanup and diagnostics with `./diagnose.sh`
- Pick specific slots to run 
- AAVEV3 & UNISWAPV2 data market support

## 🛠️ Getting Started

1. Clone the repository:
```bash
git clone https://github.com/PowerLoom/snapshotter-lite-multi-setup.git
cd snapshotter-lite-multi-setup
```

2. Run diagnostics to check and clean up any existing deployments:
```bash
./diagnose.sh
```
This tool will:
- Check for system requirements
- Detect running instances
- Find stale deployments
- Identify Docker networks and images
- Offer cleanup options for existing resources

3. Initialize your environment:
```bash
./bootstrap.sh
```
This will:
- Back up any existing .env file
- Guide you through setting up a new configuration
- Automatically populate required environment variables
- Rerun `./bootstrap.sh` if you have backed up an older `.env` file.

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Launch your node(s):
```bash
python multi_clone.py
```


## 🔗 Documentation & Support

For detailed setup instructions, please refer to our [README](https://github.com/PowerLoom/snapshotter-lite-multi-setup/blob/feat/snapshotter-lite-v2/README.md).

Need help? Join our [Discord](https://discord.gg/powerloom) community for support and updates.

## 🎯 Who Should Use This?

- Single slot holders looking for a simplified setup process
- Multi-slot operators wanting efficient management of multiple nodes
- Developers interested in running nodes for multiple data markets
- Anyone looking to participate in the PowerLoom Protocol V2 network
