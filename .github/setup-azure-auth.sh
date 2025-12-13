#!/bin/bash
# Quick setup script for Azure authentication in GitHub Actions
# This creates a Service Principal and outputs the values you need for GitHub Secrets

set -e

echo "🔐 Setting up Azure authentication for GitHub Actions..."
echo ""

# Get subscription and tenant info
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)

echo "📋 Subscription: $SUBSCRIPTION_NAME"
echo "   Subscription ID: $SUBSCRIPTION_ID"
echo "   Tenant ID: $TENANT_ID"
echo ""

# Create service principal
SP_NAME="github-actions-$(date +%s)"
echo "🔨 Creating Service Principal: $SP_NAME"

SP_OUTPUT=$(az ad sp create-for-rbac \
  --name "$SP_NAME" \
  --role "Contributor" \
  --scopes "/subscriptions/$SUBSCRIPTION_ID" \
  --sdk-auth)

CLIENT_ID=$(echo "$SP_OUTPUT" | jq -r '.clientId')
CLIENT_SECRET=$(echo "$SP_OUTPUT" | jq -r '.clientSecret')

echo "✅ Service Principal created!"
echo ""

# Get ACR info if it exists
ACR_NAME="securityserviceacr"
RESOURCE_GROUP="securityproj-rg"

if az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
  echo "🔐 Assigning ACR permissions..."
  az role assignment create \
    --role "AcrPush" \
    --assignee "$CLIENT_ID" \
    --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ContainerRegistry/registries/$ACR_NAME" \
    --output none
  echo "✅ ACR permissions assigned"
  echo ""
fi

echo "=========================================="
echo "📝 Add these to GitHub Secrets:"
echo "=========================================="
echo ""
echo "1. Go to: https://github.com/YOUR_USERNAME/security-services-on-cloud/settings/secrets/actions"
echo ""
echo "2. Add the following secrets:"
echo ""
echo "   AZURE_CLIENT_ID:"
echo "   $CLIENT_ID"
echo ""
echo "   AZURE_TENANT_ID:"
echo "   $TENANT_ID"
echo ""
echo "   AZURE_SUBSCRIPTION_ID:"
echo "   $SUBSCRIPTION_ID"
echo ""
echo "   AZURE_CREDENTIALS (optional - if using service principal method):"
echo "   $SP_OUTPUT"
echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo "=========================================="
echo ""
echo "⚠️  IMPORTANT: Save the CLIENT_SECRET now - you won't be able to see it again!"
echo "   CLIENT_SECRET: $CLIENT_SECRET"
echo ""
echo "   If you need to use OIDC instead, see .github/SETUP_AZURE_AUTH.md"

