#!/bin/zsh

# Define variables
VPS_USER="robert"
VPS_IP="10.1.50.126"
VPS_FOLDER="/home/robert/insbluemin-filestash"
IGNORE_FILE=".rsyncignore"  # The file that contains the list of files/directories to ignore

# Check if required variables are set
if [ -z "$VPS_USER" ]; then
  echo "Error: VPS_USER is not set. Please define the VPS_USER variable."
  exit 1
fi

if [ -z "$VPS_IP" ]; then
  echo "Error: VPS_IP is not set. Please define the VPS_IP variable."
  exit 1
fi

if [ -z "$VPS_FOLDER" ]; then
  echo "Error: VPS_FOLDER is not set. Please define the VPS_FOLDER variable."
  exit 1
fi

if [ -z "$IGNORE_FILE" ]; then
  echo "Error: IGNORE_FILE is not set. Please define the IGNORE_FILE variable."
  exit 1
fi

# Check if ignore file exists
if [ ! -f "$IGNORE_FILE" ]; then
  echo "Error: Ignore file $IGNORE_FILE not found. Please create it with files/directories to ignore."
  exit 1
fi

# Print confirmation of variable values
echo "Deploying to VPS with the following settings:"
echo "VPS_USER: $VPS_USER"
echo "VPS_IP: $VPS_IP"
echo "VPS_FOLDER: $VPS_FOLDER"
echo "Using ignore list from: $IGNORE_FILE"

# Sync local folder to VPS with ignore list
sshpass -p "$VPS_PASSWORD" rsync -avz --delete --exclude-from="$IGNORE_FILE" -e "ssh -o StrictHostKeyChecking=no" ./ "$VPS_USER@$VPS_IP:$VPS_FOLDER"

# Output message
echo "Deployment completed successfully!"
