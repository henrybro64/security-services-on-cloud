variable "project_name" {
  description = "Name prefix for all resources"
  type        = string
  default     = "securityproj"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "japaneast"
}

variable "acr_name" {
  description = "Globally unique ACR name (lowercase, 5-50 chars)"
  type        = string
}

variable "backend_image_name" {
  description = "Backend container image name (without registry)"
  type        = string
  default     = "security-service-api"
}

variable "backend_image_tag" {
  description = "Backend image tag"
  type        = string
  default     = "latest"
}

variable "frontend_image_name" {
  description = "Frontend container image name (without registry)"
  type        = string
  default     = "security-frontend"
}

variable "frontend_image_tag" {
  description = "Frontend image tag"
  type        = string
  default     = "latest"
}
