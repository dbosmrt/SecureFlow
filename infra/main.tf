# SecureFlow — Main Terraform Configuration
#  Cloud Run v2 service + Artifact Registry + API enablement

terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

#  Enable required GCP APIs

resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "pubsub.googleapis.com",
    "bigquery.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "aiplatform.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

#  Artifact Registry (replaces deprecated GCR)

resource "google_artifact_registry_repository" "secureflow" {
  location      = var.region
  repository_id = "secureflow"
  description   = "SecureFlow container images"
  format        = "DOCKER"

  depends_on = [google_project_service.apis]
}

#  Cloud Run v2 Service

resource "google_cloud_run_v2_service" "secureflow_api" {
  name     = "secureflow-api"
  location = var.region

  template {
    scaling {
      min_instance_count = var.cloud_run_min_instances
      max_instance_count = var.cloud_run_max_instances
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/secureflow/api:latest"

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }

      # Application config
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      env {
        name  = "GCP_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GEMINI_MODEL"
        value = var.gemini_model
      }

      # Secrets from Secret Manager
      env {
        name = "GITLAB_TOKEN"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gitlab_token.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "GITLAB_WEBHOOK_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gitlab_webhook_secret.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "GOOGLE_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.google_api_key.secret_id
            version = "latest"
          }
        }
      }

      # Liveness and startup probes
      startup_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 5
        period_seconds        = 5
        failure_threshold     = 3
      }

      liveness_probe {
        http_get {
          path = "/health"
        }
        period_seconds = 30
      }
    }

    service_account = google_service_account.secureflow_sa.email
  }

  depends_on = [
    google_project_service.apis,
    google_artifact_registry_repository.secureflow,
  ]
}

#  Output the Cloud Run URL

output "service_url" {
  description = "The URL of the deployed SecureFlow API"
  value       = google_cloud_run_v2_service.secureflow_api.uri
}

output "service_account_email" {
  description = "The service account email used by SecureFlow"
  value       = google_service_account.secureflow_sa.email
}
