#  SecureFlow — Secret Manager Configuration
#  All sensitive values stored as managed secrets.

resource "google_secret_manager_secret" "gitlab_token" {
  secret_id = "gitlab_token"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "gitlab_webhook_secret" {
  secret_id = "gitlab_webhook_secret"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "google_api_key" {
  secret_id = "google_api_key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}
