# ---------------------------
# Backend Container App (FastAPI)
# ---------------------------
resource "azurerm_container_app" "backend" {
  name                         = "${var.project_name}-backend"
  resource_group_name          = azurerm_resource_group.rg.name
  container_app_environment_id = azurerm_container_app_environment.cae.id
  revision_mode                = "Single"

  identity {
    type = "SystemAssigned"
  }

  registry {
    server   = azurerm_container_registry.acr.login_server
    identity = "System"
  }

  secret {
    name  = "redis-password"
    value = azurerm_redis_cache.redis.primary_access_key
  }

  template {
    min_replicas = 1
    max_replicas = 3

    container {
      name   = "backend"
      image  = "${azurerm_container_registry.acr.login_server}/${var.backend_image_name}:${var.backend_image_tag}"
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "REDIS_HOST"
        value = azurerm_redis_cache.redis.hostname
      }

      env {
        name  = "REDIS_PORT"
        value = tostring(azurerm_redis_cache.redis.ssl_port)
      }

      env {
        name        = "REDIS_PASSWORD"
        secret_name = "redis-password"
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8000

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }
}

# ---------------------------
# Frontend Container App (Next.js/React)
# ---------------------------
resource "azurerm_container_app" "frontend" {
  name                         = "${var.project_name}-frontend"
  resource_group_name          = azurerm_resource_group.rg.name
  container_app_environment_id = azurerm_container_app_environment.cae.id
  revision_mode                = "Single"

  identity {
    type = "SystemAssigned"
  }

  registry {
    server   = azurerm_container_registry.acr.login_server
    identity = "System"
  }

  template {
    min_replicas = 1
    max_replicas = 3

    container {
      name   = "frontend"
      image  = "${azurerm_container_registry.acr.login_server}/${var.frontend_image_name}:${var.frontend_image_tag}"
      cpu    = 0.5
      memory = "1Gi"

      # Tell frontend how to reach backend
      env {
        name  = "BACKEND_BASE_URL"
        value = azurerm_container_app.backend.latest_revision_fqdn
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 3000   # change if your frontend uses a different port

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }
}
