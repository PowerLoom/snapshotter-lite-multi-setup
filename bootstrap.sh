#! /bin/bash

# if .env not found

if [ ! -f ".env" ]; then
    echo "🟡 .env file not found, please follow the instructions below to create one!"
    echo "creating .env file..."
    cp env.example ".env"
    # get the WALLET_HOLDER_ADDRESS from the user
    echo "🫸 ▶︎ Please enter the WALLET_HOLDER_ADDRESS: "
    read WALLET_HOLDER_ADDRESS
    # Get the OS type
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/<wallet-holder-address>/${WALLET_HOLDER_ADDRESS}/g" .env
    else
        # Linux and others
        sed -i "s/<wallet-holder-address>/${WALLET_HOLDER_ADDRESS}/g" .env
    fi
    # get the SOURCE_RPC_URL from the user
    echo "🫸 ▶︎ Please enter the SOURCE_RPC_URL: "
    read SOURCE_RPC_URL
    # replace the SOURCE_RPC_URL in the .env file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|<source-rpc-url>|${SOURCE_RPC_URL}|g" .env
    else
        # Linux and others
        sed -i "s|<source-rpc-url>|${SOURCE_RPC_URL}|g" .env
    fi
    # get the SIGNER_ACCOUNT_ADDRESS from the user
    echo "🫸 ▶︎ Please enter the SIGNER_ACCOUNT_ADDRESS: "
    read SIGNER_ACCOUNT_ADDRESS
    # replace the SIGNER_ACCOUNT_ADDRESS in the .env file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/<signer-account-address>/${SIGNER_ACCOUNT_ADDRESS}/g" .env
    else
        # Linux and others
        sed -i "s/<signer-account-address>/${SIGNER_ACCOUNT_ADDRESS}/g" .env
    fi
    # get the SIGNER_ACCOUNT_PRIVATE_KEY from the user
    echo "🫸 ▶︎ Please enter the SIGNER_ACCOUNT_PRIVATE_KEY: "
    read -s SIGNER_ACCOUNT_PRIVATE_KEY
    echo "" # add a newline after hidden input
    # replace the SIGNER_ACCOUNT_PRIVATE_KEY in the .env file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/<signer-account-private-key>/${SIGNER_ACCOUNT_PRIVATE_KEY}/g" .env
    else
        # Linux and others
        sed -i "s/<signer-account-private-key>/${SIGNER_ACCOUNT_PRIVATE_KEY}/g" .env
    fi
    # get the TELEGRAM_CHAT_ID from the user
    echo "🫸 ▶︎ Please enter the TELEGRAM_CHAT_ID (press enter to skip): "
    read TELEGRAM_CHAT_ID
    # replace the TELEGRAM_CHAT_ID in the .env file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/<telegram-chat-id>/${TELEGRAM_CHAT_ID}/g" .env
    else
        # Linux and others
        sed -i "s/<telegram-chat-id>/${TELEGRAM_CHAT_ID}/g" .env
    fi
    echo "🟢 .env file created successfully!"
else
    echo "🟢 .env file already found to be initialized! If you wish to change any of the values, please backup the .env file at the following prompt."
    # add timestamp to the backup file name
    TIMESTAMP=$(date +%Y%m%d%H%M%S)
    BACKUP_FILE=".env.backup.${TIMESTAMP}"
    # prompt the user to backup
    echo "Do you wish to backup the .env file? (y/n)"
    read BACKUP_CHOICE
    if [ "$BACKUP_CHOICE" == "y" ]; then
        mv .env $BACKUP_FILE
        echo "🟢 .env file backed up to $BACKUP_FILE"
    fi
fi
