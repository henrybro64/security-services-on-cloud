# Deployment

Deploy everything with Terraform, then GitHub Actions handles image builds and updates.

## First Time Setup

1. Deploy infrastructure:
   ```bash
   cd infra
   export ARM_SUBSCRIPTION_ID=your-subscription-id
   terraform apply -var-file=terraform.tfvars
   ```
   
   Creates: Resource Group, ACR, Redis, Container Apps Environment, and Container Apps (with placeholder images).

2. Push code to trigger GitHub Actions:
   - Backend workflow builds and pushes image to ACR, then updates the Container App
   - Frontend workflow does the same

3. Get URLs:
   ```bash
   terraform output frontend_url
   terraform output backend_url
   ```

## Updates

- Code changes: Push to GitHub, workflows handle the rest
- Infrastructure changes: Run `terraform apply`

## Cleanup

```bash
cd infra
terraform destroy -var-file=terraform.tfvars
```

## How It Works

Terraform creates Container Apps with placeholder images. The `lifecycle { ignore_changes = [template[0].container[0].image] }` block means Terraform won't revert image changes made by GitHub Actions.

GitHub Actions builds images, pushes to ACR, configures registry auth, and updates the Container App with the new image.

## Troubleshooting

**Container App revision fails initially?** Normal - wait for GitHub Actions to build the image.

**Images not updating?** Check GitHub Actions is running and verify images in ACR: `az acr repository show-tags --name <acr> --repository <image>`
