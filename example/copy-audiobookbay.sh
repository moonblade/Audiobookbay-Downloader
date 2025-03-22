#!/bin/bash
echo "Running custom startup script: Copying audiobookbay.json"
if [ -f /config/audiobookbay.json ]; then
  cp /config/audiobookbay.json /config/Jackett/Indexers/audiobookbay.json
  echo "Copy complete."
else
  echo "No audiobookbay.json found in /config."
fi
