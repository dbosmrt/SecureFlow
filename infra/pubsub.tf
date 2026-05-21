# ============================================================
#  SecureFlow — Pub/Sub Configuration
#  Event topic + worker subscription with dead letter handling.
# ============================================================

# --- Main event topic ---
resource "google_pubsub_topic" "secureflow_events" {
  name = "secureflow-events"

  message_retention_duration = "86400s" # 24 hours

  depends_on = [google_project_service.apis]
}

# --- Dead letter topic (for failed messages) ---
resource "google_pubsub_topic" "secureflow_dead_letter" {
  name = "secureflow-dead-letter"

  depends_on = [google_project_service.apis]
}

# --- Worker subscription ---
resource "google_pubsub_subscription" "secureflow_worker" {
  name  = "secureflow-worker"
  topic = google_pubsub_topic.secureflow_events.id

  # 10 min ack deadline (Gemini processing can be slow)
  ack_deadline_seconds = 600

  # Retry policy
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  # Dead letter after 5 failed attempts
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.secureflow_dead_letter.id
    max_delivery_attempts = 5
  }

  # Keep unacked messages for 7 days
  message_retention_duration = "604800s"

  # Expire subscription after 31 days of inactivity
  expiration_policy {
    ttl = "2678400s"
  }
}

# --- Dead letter subscription (for monitoring failed events) ---
resource "google_pubsub_subscription" "secureflow_dead_letter_sub" {
  name  = "secureflow-dead-letter-sub"
  topic = google_pubsub_topic.secureflow_dead_letter.id

  ack_deadline_seconds = 60
}
