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
    sed -i'.backup' 's/^PROTOCOL_STATE_CONTRACT=.*/PROTOCOL_STATE_CONTRACT='"0x10c5E2ee14006B3860d4FdF6B173A30553ea6333"'/' .env
    # replace PROST_CHAIN_ID in .env
    sed -i'.backup' 's/^PROST_CHAIN_ID=.*/PROST_CHAIN_ID='"11165"'/' .env
    # replace SEQUENCER_ID in .env
    sed -i'.backup' 's/^SEQUENCER_ID=.*/SEQUENCER_ID='"QmdJbNsbHpFseUPKC9vLt4vMsfdxA4dyHPzsAWuzYz3Yxx"'/' .env
    # replace RELAYER_RENDEZVOUS_POINT in .env
    sed -i'.backup' 's/^RELAYER_RENDEZVOUS_POINT=.*/RELAYER_RENDEZVOUS_POINT='"Relayer_POP_test_simulation_phase_1"'/' .env
    # replace CLIENT_RENDEZVOUS_POINT in .env
    sed -i'.backup' 's/^CLIENT_RENDEZVOUS_POINT=.*/CLIENT_RENDEZVOUS_POINT='"POP_Client_simulation_test_alpha"'/' .env
    
fi
echo ".env file populated! Run python multi_clone.py next";
