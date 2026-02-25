#!/bin/bash
# setup-jackett.sh - Initialize Jackett with AudiobookBay indexer pre-configured
#
# This script copies the default Jackett configuration with AudiobookBay
# pre-configured if the config doesn't already exist.

set -e

CONFIG_DIR="${1:-./jackett-config}"
EXAMPLE_DIR="./example/jackett-config"

# Create config directory if it doesn't exist
mkdir -p "$CONFIG_DIR/Jackett/Indexers"

# Copy ServerConfig.json if it doesn't exist
if [ ! -f "$CONFIG_DIR/Jackett/ServerConfig.json" ]; then
    echo "Initializing Jackett configuration..."
    
    # Generate a random API key
    API_KEY=$(cat /dev/urandom | LC_ALL=C tr -dc 'a-z0-9' | fold -w 32 | head -n 1)
    
    # Copy and update ServerConfig.json with the new API key
    if [ -f "$EXAMPLE_DIR/Jackett/ServerConfig.json" ]; then
        sed "s/CHANGE_ME_TO_RANDOM_STRING/$API_KEY/" "$EXAMPLE_DIR/Jackett/ServerConfig.json" > "$CONFIG_DIR/Jackett/ServerConfig.json"
        echo "Created ServerConfig.json with API key: $API_KEY"
    else
        echo "Warning: Example ServerConfig.json not found at $EXAMPLE_DIR/Jackett/ServerConfig.json"
    fi
fi

# Copy AudiobookBay indexer config if it doesn't exist
if [ ! -f "$CONFIG_DIR/Jackett/Indexers/audiobookbay.json" ]; then
    if [ -f "$EXAMPLE_DIR/Jackett/Indexers/audiobookbay.json" ]; then
        cp "$EXAMPLE_DIR/Jackett/Indexers/audiobookbay.json" "$CONFIG_DIR/Jackett/Indexers/"
        echo "Added AudiobookBay indexer configuration"
    else
        echo "Warning: Example audiobookbay.json not found"
    fi
fi

# Output the API key for use in docker-compose
if [ -f "$CONFIG_DIR/Jackett/ServerConfig.json" ]; then
    API_KEY=$(grep -o '"APIKey": "[^"]*"' "$CONFIG_DIR/Jackett/ServerConfig.json" | cut -d'"' -f4)
    echo ""
    echo "=============================================="
    echo "Jackett API Key: $API_KEY"
    echo "=============================================="
    echo ""
    echo "Use this API key in your docker-compose.yml:"
    echo "  JACKETT_API_KEY=$API_KEY"
    echo ""
fi
