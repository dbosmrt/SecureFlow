# ============================================================
#  SecureFlow — Terraform Variables
#  All configurable parameters for the GCP infrastructure.
# ============================================================

variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "The default GCP region for all resources"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment (development, staging, production)"
  type        = string
  default     = "production"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "cloud_run_min_instances" {
  description = "Minimum number of Cloud Run instances (0 = scale to zero)"
  type        = number
  default     = 0
}

variable "cloud_run_max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 3
}

variable "gemini_model" {
  description = "Gemini model to use for agents"
  type        = string
  default     = "gemini-2.5-flash"
}
