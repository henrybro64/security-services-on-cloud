#!/bin/bash
# Deployment script for Azure infrastructure
# Sets required environment variables and runs Terraform

set -e

# Get subscription ID from Azure CLI
SUBSCRIPTION_ID=$(az account show --query id -o tsv 2>/dev/null)

if [ -z "$SUBSCRIPTION_ID" ]; then
    echo "Error: Not logged in to Azure CLI. Please run 'az login' first."
    exit 1
fi

echo "Using Azure subscription: $SUBSCRIPTION_ID"
export ARM_SUBSCRIPTION_ID="$SUBSCRIPTION_ID"

# Run terraform with provided arguments
terraform "$@"

