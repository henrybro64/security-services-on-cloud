# Setting Up Azure Authentication for GitHub Actions

This guide explains how to configure Azure authentication for your GitHub Actions workflows.

## Option 1: OIDC Authentication (Recommended)

OIDC is more secure as it doesn't require storing credentials. Follow these steps:

### Step 1: Create Azure AD App Registration

```bash
# Get your subscription and tenant IDs
az account show --query "{subscriptionId:id, tenantId:tenantId}" -o table

# Create an App Registration
APP_NAME="github-actions-oidc"
APP_ID=$(az ad app create --display-name "$APP_NAME" --query appId -o tsv)
echo "App ID: $APP_ID"

# Create a Service Principal
SP_ID=$(az ad sp create --id "$APP_ID" --query id -o tsv)
echo "Service Principal ID: $SP_ID"
```

### Step 2: Create Federated Identity Credential

```bash
# Replace these with your values
GITHUB_ORG="your-github-org-or-username"  # e.g., "henrybro" or your org name
GITHUB_REPO="security-services-on-cloud"
SUBSCRIPTION_ID="your-subscription-id"  # From Step 1

# Create federated identity credential
az ad app federated-credential create \
  --id "$APP_ID" \
  --parameters "{\"name\":\"github-actions\",\"issuer\":\"https://token.actions.githubusercontent.com\",\"subject\":\"repo:${GITHUB_ORG}/${GITHUB_REPO}:ref:refs/heads/main\",\"audiences\":[\"api://AzureADTokenExchange\"]}"
```

### Step 3: Assign Permissions to Service Principal

```bash
# Get your subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# Assign Contributor role (or more specific roles as needed)
az role assignment create \
  --role "Contributor" \
  --assignee "$APP_ID" \
  --scope "/subscriptions/$SUBSCRIPTION_ID"

# For ACR access (if needed separately)
ACR_NAME="securityserviceacr"
az role assignment create \
  --role "AcrPush" \
  --assignee "$APP_ID" \
  --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/securityproj-rg/providers/Microsoft.ContainerRegistry/registries/$ACR_NAME"
```

### Step 4: Add GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions, and add:

- `AZURE_CLIENT_ID`: The App ID from Step 1
- `AZURE_TENANT_ID`: Your tenant ID from Step 1
- `AZURE_SUBSCRIPTION_ID`: Your subscription ID

### Step 5: Update Workflow Permissions

The workflows need `id-token: write` permission. This should already be in the workflow files, but verify:

```yaml
permissions:
  id-token: write
  contents: read
```

---

## Option 2: Service Principal with Credentials (Simpler, but less secure)

### Step 1: Create Service Principal

```bash
# Get your subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# Create service principal with Contributor role
az ad sp create-for-rbac \
  --name "github-actions-sp" \
  --role "Contributor" \
  --scopes "/subscriptions/$SUBSCRIPTION_ID" \
  --sdk-auth
```

This will output JSON like:
```json
{
  "clientId": "...",
  "clientSecret": "...",
  "subscriptionId": "...",
  "tenantId": "..."
}
```

### Step 2: Add GitHub Secret

Go to your GitHub repository → Settings → Secrets and variables → Actions, and add:

- `AZURE_CREDENTIALS`: The entire JSON output from Step 1

### Step 3: Update Workflow Files

Update the workflow files to use `creds` instead of individual secrets:

```yaml
- name: Azure login
  uses: azure/login@v2
  with:
    creds: ${{ secrets.AZURE_CREDENTIALS }}
```

---

## Additional Secrets Needed

You'll also need these secrets for the workflows:

### For backend-aks.yml:
- `ACR_USERNAME`: ACR admin username (or use managed identity)
- `ACR_PASSWORD`: ACR admin password (or use managed identity)
- `ABUSEIPDB_API_KEY`: (Optional) Your AbuseIPDB API key

### For frontend-appservice.yml:
- `NEXT_PUBLIC_API_BASE_URL`: Your backend API URL

---

## Quick Setup Script (Option 2 - Service Principal)

Run this script to quickly set up authentication:

```bash
#!/bin/bash
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)

echo "Creating Service Principal..."
SP_OUTPUT=$(az ad sp create-for-rbac \
  --name "github-actions-$(date +%s)" \
  --role "Contributor" \
  --scopes "/subscriptions/$SUBSCRIPTION_ID" \
  --sdk-auth)

echo ""
echo "=========================================="
echo "Add this to GitHub Secrets as AZURE_CREDENTIALS:"
echo "=========================================="
echo "$SP_OUTPUT"
echo ""
echo "Also add these secrets:"
echo "AZURE_CLIENT_ID: $(echo $SP_OUTPUT | jq -r '.clientId')"
echo "AZURE_TENANT_ID: $TENANT_ID"
echo "AZURE_SUBSCRIPTION_ID: $SUBSCRIPTION_ID"
```

---

## Troubleshooting

### Error: "Not all values are present"
- Make sure all required secrets are set in GitHub
- Check that secret names match exactly (case-sensitive)

### Error: "Insufficient permissions"
- Ensure the service principal has Contributor role
- For ACR, ensure AcrPush role is assigned

### Error: "Invalid credentials"
- Regenerate service principal credentials
- Check that the subscription is active

