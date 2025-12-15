# Public IP (not needed for Container Apps)
# resource "azurerm_public_ip" "api" {
#   name                = "${var.project_name}-api-pip"
#   location            = azurerm_resource_group.rg.location
#   resource_group_name = azurerm_resource_group.rg.name
#
#   allocation_method = "Static"
#   sku               = "Standard"
#
#   # Must be unique per region; adjust if needed
#   # Example: securityservice-api, henrysec-api, etc.
#   domain_name_label = "${var.project_name}-api"
# }
#
#
# output "api_public_ip" {
#   value       = azurerm_public_ip.api.ip_address
#   description = "Static public IP for the security-service API LoadBalancer"
# }
#
# output "api_fqdn" {
#   value       = azurerm_public_ip.api.fqdn
#   description = "DNS name for the security-service API (e.g. myproj-api.eastus.cloudapp.azure.com)"
# }
