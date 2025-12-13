# Quick Setup: Fix GitHub Actions Azure Authentication

## The Problem
GitHub Actions can't authenticate to Azure because the required secrets are missing.

## Quick Fix (5 minutes)

### Step 1: Run the setup script

```bash
cd /Users/henrybro/workspace/security-services-on-cloud
./.github/setup-azure-auth.sh
```

This will create a Service Principal and show you the values to add to GitHub.

### Step 2: Add GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add these three secrets:

   **Secret 1:**
   - Name: `AZURE_CLIENT_ID`
   - Value: (from the script output)

   **Secret 2:**
   - Name: `AZURE_TENANT_ID`
   - Value: `0cc06911-81b8-4857-a1ce-f070b7e6c712`

   **Secret 3:**
   - Name: `AZURE_SUBSCRIPTION_ID`
   - Value: `55f22fc6-910b-48e6-bbbf-dea69b35b455`

### Step 3: Additional Secrets (if needed)

For the backend workflow, you may also need:

- `ACR_USERNAME`: Your ACR admin username (or leave empty if using managed identity)
- `ACR_PASSWORD`: Your ACR admin password (or leave empty if using managed identity)
- `ABUSEIPDB_API_KEY`: (Optional) Your AbuseIPDB API key

For the frontend workflow:

- `NEXT_PUBLIC_API_BASE_URL`: Your backend API URL (e.g., `https://securityproj-backend.xxx.azurecontainerapps.io`)

### Step 4: Test

Push a change to trigger the workflow, or manually run it from the Actions tab.

---

## Alternative: Manual Setup

If the script doesn't work, run these commands manually:

```bash
# Get your subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)

# Create service principal
az ad sp create-for-rbac \
  --name "github-actions-$(date +%s)" \
  --role "Contributor" \
  --scopes "/subscriptions/$SUBSCRIPTION_ID" \
  --sdk-auth
```

Copy the output and add it to GitHub Secrets as shown above.

---

## Verify Secrets Are Set

After adding secrets, you can verify by:
1. Going to Settings → Secrets and variables → Actions
2. You should see: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`

---

## Troubleshooting

**Error: "Not all values are present"**
- Double-check that all three secrets are added
- Make sure secret names match exactly (case-sensitive)
- Try re-running the workflow

**Error: "Insufficient permissions"**
- The service principal needs Contributor role (the script sets this)
- For ACR access, ensure AcrPush role is assigned

