output "frontend_url" {
  description = "Public URL of the frontend Container App"
  value       = "https://${azurerm_container_app.frontend.ingress[0].fqdn}"
}

output "backend_url" {
  description = "Public URL of the backend Container App"
  value       = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
}

output "acr_login_server" {
  description = "ACR login server"
  value       = azurerm_container_registry.acr.login_server
}
