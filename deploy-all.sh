#!/bin/bash

# Stop all nodes without prompting
echo "🔴 Stopping all running nodes..."
./diagnose.sh -y

# Wait a moment for all processes to terminate
echo "⏳ Waiting for processes to terminate..."
sleep 5

# Run multi_clone.py with -y flag to deploy all slots without prompting
echo "🟢 Starting automatic redeployment of all slots..."
python3 multi_clone.py -y

#There is no need for this message as multi_clone.py will print the final message
#echo "✅ Deployment process completed!"
