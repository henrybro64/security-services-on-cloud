output "frontend_fqdn" {
  description = "Public URL of the frontend"
  value       = azurerm_container_app.frontend.latest_revision_fqdn
}

output "backend_fqdn" {
  description = "Public URL of the backend API"
  value       = azurerm_container_app.backend.latest_revision_fqdn
}

output "acr_login_server" {
  description = "ACR login server"
  value       = azurerm_container_registry.acr.login_server
}
