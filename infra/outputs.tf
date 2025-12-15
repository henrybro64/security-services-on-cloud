output "frontend_url" {
  description = "Public URL of the frontend Container App"
  value       = "https://${azurerm_container_app.frontend.latest_revision_fqdn}"
}

output "backend_url" {
  description = "Public URL of the backend Container App"
  value       = "https://${azurerm_container_app.backend.latest_revision_fqdn}"
}

output "acr_login_server" {
  description = "ACR login server"
  value       = azurerm_container_registry.acr.login_server
}

# AKS outputs (not used)
# output "aks_kube_config" {
#   value     = azurerm_kubernetes_cluster.aks.kube_config_raw
#   sensitive = true
# }
#
# output "api_public_ip" {
#   value       = azurerm_public_ip.api.ip_address
#   description = "Static public IP for the security-service API LoadBalancer (AKS)"
# }
#
# output "api_fqdn" {
#   value       = azurerm_public_ip.api.fqdn
#   description = "DNS name for the security-service API (AKS LoadBalancer)"
# }
