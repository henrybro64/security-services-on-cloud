# App Service Plan for frontend (Linux, Node)
# Using Free tier (F1) - if quota issues occur, try Consumption plan (Y1) or Basic (B1)
resource "azurerm_service_plan" "frontend_plan" {
  name                = "${var.project_name}-frontend-plan"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  os_type  = "Linux"
  sku_name = "F1" # Free tier - if this fails, change to "Y1" (Consumption) or "B1" (Basic)
}

resource "azurerm_linux_web_app" "frontend" {
  name                = "${var.project_name}-frontend-webapp"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  service_plan_id     = azurerm_service_plan.frontend_plan.id

  https_only = true

  site_config {
    minimum_tls_version = "1.2"

    application_stack {
      node_version = "20-lts"
    }
  }

  app_settings = {
    # Backend API URL from AKS LoadBalancer (using FQDN from Terraform)
    NEXT_PUBLIC_API_BASE_URL = "http://${azurerm_public_ip.api.fqdn}"
  }

  tags = {
    project = var.project_name
    role    = "frontend"
  }
}
