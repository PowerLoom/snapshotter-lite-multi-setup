#! /bin/bash

create_env() {
    echo "creating .env file..."
    # Only copy from example if no backup exists
    if [ ! -f "$BACKUP_FILE" ]; then
        cp env.example ".env"
    else
        cp "$BACKUP_FILE" ".env"
    fi

    # Function to get existing value from .env
    get_existing_value() {
        local key=$1
        grep "^$key=" .env | cut -d'=' -f2-
    }

    # Function to prompt user with existing value
    prompt_with_existing() {
        local prompt=$1
        local key=$2
        local existing_value=$(get_existing_value "$key")
        
        if [ -n "$existing_value" ]; then
            echo "🫸 ▶︎ $prompt (press enter to keep current value: $existing_value): "
        else
            echo "🫸 ▶︎ $prompt: "
        fi
    }

    # Function to update env value
    update_env_value() {
        local placeholder=$1
        local value=$2
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|$placeholder|${value}|g" .env
        else
            sed -i "s|$placeholder|${value}|g" .env
        fi
    }

    # WALLET_HOLDER_ADDRESS
    prompt_with_existing "Please enter the WALLET_HOLDER_ADDRESS" "WALLET_HOLDER_ADDRESS"
    read input
    [ -n "$input" ] && update_env_value "<wallet-holder-address>" "$input"

    # SOURCE_RPC_URL
    prompt_with_existing "Please enter the SOURCE_RPC_URL" "SOURCE_RPC_URL"
    read input
    [ -n "$input" ] && update_env_value "<source-rpc-url>" "$input"

    # SIGNER_ACCOUNT_ADDRESS
    prompt_with_existing "Please enter the SIGNER_ACCOUNT_ADDRESS" "SIGNER_ACCOUNT_ADDRESS"
    read input
    [ -n "$input" ] && update_env_value "<signer-account-address>" "$input"

    # SIGNER_ACCOUNT_PRIVATE_KEY
    prompt_with_existing "Please enter the SIGNER_ACCOUNT_PRIVATE_KEY" "SIGNER_ACCOUNT_PRIVATE_KEY"
    read -s input
    echo "" # add a newline after hidden input
    [ -n "$input" ] && update_env_value "<signer-account-private-key>" "$input"

    # TELEGRAM_CHAT_ID
    prompt_with_existing "Please enter the TELEGRAM_CHAT_ID (press enter to skip)" "TELEGRAM_CHAT_ID"
    read input
    [ -n "$input" ] && update_env_value "<telegram-chat-id>" "$input"

    echo "🟢 .env file created successfully!"
}

# Main script flow
if [ ! -f ".env" ]; then
    echo "🟡 .env file not found, please follow the instructions below to create one!"
    create_env
else
    echo "🟢 .env file already found to be initialized! If you wish to change any of the values, please backup the .env file at the following prompt."
    TIMESTAMP=$(date +%Y%m%d%H%M%S)
    BACKUP_FILE=".env.backup.${TIMESTAMP}"
    echo "Do you wish to backup the .env file? (y/n)"
    read BACKUP_CHOICE
    if [ "$BACKUP_CHOICE" == "y" ]; then
        mv .env $BACKUP_FILE
        echo "🟢 .env file backed up to $BACKUP_FILE"
        create_env
    fi
fi
