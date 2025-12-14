# ---------------------------
# Backend Container App (FastAPI)
# COMMENTED OUT: Backend is running in AKS, not Container Apps
# ---------------------------
# resource "azurerm_container_app" "backend" {
#   name                         = "${var.project_name}-backend"
#   resource_group_name          = azurerm_resource_group.rg.name
#   container_app_environment_id = azurerm_container_app_environment.cae.id
#   revision_mode                = "Single"
#
#   identity {
#     type = "SystemAssigned"
#   }
#
#   registry {
#     server   = azurerm_container_registry.acr.login_server
#     identity = "System"
#   }
#
#   secret {
#     name  = "redis-password"
#     value = azurerm_redis_cache.redis.primary_access_key
#   }
#
#   template {
#     min_replicas = 1
#     max_replicas = 3
#
#     container {
#       name   = "backend"
#       image  = "${azurerm_container_registry.acr.login_server}/${var.backend_image_name}:${var.backend_image_tag}"
#       cpu    = 0.5
#       memory = "1Gi"
#
#       env {
#         name  = "REDIS_HOST"
#         value = azurerm_redis_cache.redis.hostname
#       }
#
#       env {
#         name  = "REDIS_PORT"
#         value = tostring(azurerm_redis_cache.redis.ssl_port)
#       }
#
#       env {
#         name  = "REDIS_SSL"
#         value = "true"
#       }
#
#       env {
#         name        = "REDIS_PASSWORD"
#         secret_name = "redis-password"
#       }
#     }
#   }
#
#   ingress {
#     external_enabled = true
#     target_port      = 8000
#
#     traffic_weight {
#       latest_revision = true
#       percentage      = 100
#     }
#   }
# }

# ---------------------------
# Frontend Container App (Next.js/React)
# COMMENTED OUT: Using App Service instead of Container Apps
# Backend is running in AKS, so frontend points to AKS LoadBalancer
# ---------------------------
# resource "azurerm_container_app" "frontend" {
#   name                         = "${var.project_name}-frontend"
#   resource_group_name          = azurerm_resource_group.rg.name
#   container_app_environment_id = azurerm_container_app_environment.cae.id
#   revision_mode                = "Single"
#
#   identity {
#     type = "SystemAssigned"
#   }
#
#   registry {
#     server   = azurerm_container_registry.acr.login_server
#     identity = "System"
#   }
#
#   template {
#     min_replicas = 1
#     max_replicas = 3
#
#     container {
#       name   = "frontend"
#       image  = "${azurerm_container_registry.acr.login_server}/${var.frontend_image_name}:${var.frontend_image_tag}"
#       cpu    = 0.5
#       memory = "1Gi"
#
#       # Tell frontend how to reach backend (AKS LoadBalancer)
#       # Using FQDN from Terraform public IP output
#       env {
#         name  = "NEXT_PUBLIC_API_BASE_URL"
#         value = "http://${azurerm_public_ip.api.fqdn}"
#       }
#     }
#   }
#
#   ingress {
#     external_enabled = true
#     target_port      = 3000   # Next.js default port
#
#     traffic_weight {
#       latest_revision = true
#       percentage      = 100
#     }
#   }
# }

# Allow frontend container app to pull images from ACR using managed identity
# resource "azurerm_role_assignment" "frontend_acr_pull" {
#   scope                = azurerm_container_registry.acr.id
#   role_definition_name = "AcrPull"
#   principal_id         = azurerm_container_app.frontend.identity[0].principal_id
# }
