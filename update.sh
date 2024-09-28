#!/bin/bash

# Ensure the script exits immediately if any command fails
set -e

# Reset the current branch to match the remote main branch
echo "Resetting local changes to match the remote repository..."
git reset --hard origin/main

# Fetch the latest changes from the remote repository
echo "Fetching the latest updates from the remote repository..."
git fetch origin

# Pull the latest changes from the remote main branch
echo "Pulling the latest changes from the remote main branch..."
git pull origin main

# Provide user feedback on successful completion
echo "✅ Update completed successfully!"
echo "To initialize the model, run the following command:"
echo "   python3 moderation_model.py"

chmod +x update.sh