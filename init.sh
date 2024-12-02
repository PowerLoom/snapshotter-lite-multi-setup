#!/bin/bash

# check if .env exists
if [ ! -f .env ]; then
    echo ".env file not found, please create one!";
    echo "creating .env file...";
    cp env.example .env;

    # ask user for SOURCE_RPC_URL and replace it in .env
    echo "Enter SOURCE_RPC_URL: ";
    read SOURCE_RPC_URL;
    sed -i'.backup' "s#<source-rpc-url>#$SOURCE_RPC_URL#" .env

    # ask user for SIGNER_ACCOUNT_ADDRESS and replace it in .env
    
    echo "Enter SIGNER_ACCOUNT_ADDRESS: ";
    read SIGNER_ACCOUNT_ADDRESS;
    sed -i'.backup' "s#<signer-account-address>#$SIGNER_ACCOUNT_ADDRESS#" .env

    # ask user for SIGNER_ACCOUNT_PRIVATE_KEY and replace it in .env
    echo "Enter SIGNER_ACCOUNT_PRIVATE_KEY: ";
    read SIGNER_ACCOUNT_PRIVATE_KEY;
    sed -i'.backup' "s#<signer-account-private-key>#$SIGNER_ACCOUNT_PRIVATE_KEY#" .env

    # ask user for SLOT_ID and replace it in .env
    echo "Enter SLOT_ID (Enter 0 for multi-slot deployment): ";
    read SLOT_ID;
    sed -i'.backup' "s#<slot-id>#$SLOT_ID#" .env

    # ask user for WALLET_HOLDER_ADDRESS and replace it in .env

    echo "Enter WALLET_HOLDER_ADDRESS (Enter empty for single slot deployment): ";
    read WALLET_HOLDER_ADDRESS;
    sed -i'.backup' "s#<wallet-holder-address>#$WALLET_HOLDER_ADDRESS#" .env

    # fill defaults 

    # replace PROTOCOL_STATE_CONTRACT in .env
    sed -i'.backup' 's/^PROTOCOL_STATE_CONTRACT=.*/PROTOCOL_STATE_CONTRACT='"0xF68342970beF978697e1104223b2E1B6a1D7764d"'/' .env
    # replace DATA_MARKET_CONTRACT in .env
    sed -i'.backup' 's/^DATA_MARKET_CONTRACTS=.*/DATA_MARKET_CONTRACTS='"0xc390a15BcEB89C2d4910b2d3C696BfD21B190F07,0x8023BD7A9e8386B10336E88294985e3Fbc6CF23F"'/' .env
    # replace PROST_CHAIN_ID in .env
    sed -i'.backup' 's/^PROST_CHAIN_ID=.*/PROST_CHAIN_ID='"11169"'/' .env
    
fi
echo ".env file populated! Run python multi_clone.py for single slot deployment or python multi_clone.py multi for multiple slot ids";
