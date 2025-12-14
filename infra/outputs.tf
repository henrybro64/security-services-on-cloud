output "frontend_url" {
  description = "Public URL of the frontend App Service"
  value       = "https://${azurerm_linux_web_app.frontend.default_hostname}"
}
output "acr_login_server" {
  description = "ACR login server"
  value       = azurerm_container_registry.acr.login_server
}
