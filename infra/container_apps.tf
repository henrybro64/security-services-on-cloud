# Backend Container App
resource "azurerm_container_app" "backend" {
  name                         = "${var.project_name}-backend"
  resource_group_name          = azurerm_resource_group.rg.name
  container_app_environment_id = azurerm_container_app_environment.cae.id
  revision_mode                = "Single"

  identity {
    type = "SystemAssigned"
  }

  # Registry auth configured by GitHub Actions when deploying real images

  secret {
    name  = "redis-password"
    value = azurerm_redis_cache.redis.primary_access_key
  }

  template {
    min_replicas = 1
    max_replicas = 3

    container {
      name   = "backend"
      image  = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"  # Placeholder, updated by GitHub Actions
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
        name  = "REDIS_SSL"
        value = "true"
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

  # Let GitHub Actions manage image updates
  lifecycle {
    ignore_changes = [
      template[0].container[0].image,
      registry
    ]
  }

  depends_on = [
    azurerm_container_registry.acr,
    azurerm_redis_cache.redis
  ]
}

# ACR pull permission for backend
resource "azurerm_role_assignment" "backend_acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_container_app.backend.identity[0].principal_id
}

# Frontend Container App
resource "azurerm_container_app" "frontend" {
  name                         = "${var.project_name}-frontend"
  resource_group_name          = azurerm_resource_group.rg.name
  container_app_environment_id = azurerm_container_app_environment.cae.id
  revision_mode                = "Single"

  identity {
    type = "SystemAssigned"
  }

  # Registry auth configured by GitHub Actions when deploying real images

  template {
    min_replicas = 1
    max_replicas = 3

    container {
      name   = "frontend"
      image  = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"  # Placeholder, updated by GitHub Actions
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "NEXT_PUBLIC_API_BASE_URL"
        # Use stable app FQDN (not revision-specific) for backend API
        value = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 3000   # Next.js default port

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  # Let GitHub Actions manage image updates
  lifecycle {
    ignore_changes = [
      template[0].container[0].image,
      registry
    ]
  }

  depends_on = [
    azurerm_container_registry.acr,
    azurerm_container_app.backend
  ]
}

# ACR pull permission for frontend
resource "azurerm_role_assignment" "frontend_acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_container_app.frontend.identity[0].principal_id
}
