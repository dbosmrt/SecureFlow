# ============================================================
#  SecureFlow — IAM Configuration
#  Service account + least-privilege role bindings.
# ============================================================

# --- Service Account ---
resource "google_service_account" "secureflow_sa" {
  account_id   = "secureflow"
  display_name = "SecureFlow Service Account"
  description  = "Used by Cloud Run and Cloud Build for SecureFlow operations"
}

# --- Pub/Sub roles ---
resource "google_project_iam_member" "pubsub_publisher" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.secureflow_sa.email}"
}

resource "google_project_iam_member" "pubsub_subscriber" {
  project = var.project_id
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:${google_service_account.secureflow_sa.email}"
}

# --- BigQuery role ---
resource "google_project_iam_member" "bigquery_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.secureflow_sa.email}"
}

# --- Vertex AI role (for Gemini API via Vertex) ---
resource "google_project_iam_member" "vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.secureflow_sa.email}"
}

# --- Secret Manager access (per-secret, least privilege) ---
resource "google_secret_manager_secret_iam_member" "gitlab_token_accessor" {
  secret_id = google_secret_manager_secret.gitlab_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.secureflow_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "gitlab_webhook_accessor" {
  secret_id = google_secret_manager_secret.gitlab_webhook_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.secureflow_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "google_api_key_accessor" {
  secret_id = google_secret_manager_secret.google_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.secureflow_sa.email}"
}
