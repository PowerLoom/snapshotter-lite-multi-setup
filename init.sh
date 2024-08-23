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

    echo "Enter WALLET_HOLDER_ADDRESS: ";
    read WALLET_HOLDER_ADDRESS;
    sed -i'.backup' "s#<wallet-holder-address>#$WALLET_HOLDER_ADDRESS#" .env

    # fill defaults 

    # replace PROTOCOL_STATE_CONTRACT in .env
    sed -i'.backup' 's/^PROTOCOL_STATE_CONTRACT=.*/PROTOCOL_STATE_CONTRACT='"0xE88E5f64AEB483d7057645326AdDFA24A3B312DF"'/' .env
    # replace DATA_MARKET_CONTRACT in .env
    sed -i'.backup' 's/^DATA_MARKET_CONTRACT=.*/DATA_MARKET_CONTRACT='"0x0C2E22fe7526fAeF28E7A58c84f8723dEFcE200c"'/' .env
    # replace PROST_CHAIN_ID in .env
    sed -i'.backup' 's/^PROST_CHAIN_ID=.*/PROST_CHAIN_ID='"11169"'/' .env
    
fi
echo ".env file populated! Run python multi_clone.py next";
