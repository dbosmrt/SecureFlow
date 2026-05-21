# ============================================================
#  SecureFlow — BigQuery Configuration
#  Dataset + 3 tables matching the Python data models exactly.
#
#  Tables:
#    findings       — Security findings from scanner agents
#    audit_log      — Every agent action for compliance
#    approval_queue — HITL pending/approved/rejected actions
# ============================================================

resource "google_bigquery_dataset" "secureflow" {
  dataset_id  = "secureflow"
  location    = var.region
  description = "SecureFlow autonomous security agent data"

  # Default table expiration: none (keep all data)
  # Access controlled via IAM, not dataset-level ACLs

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }

  depends_on = [google_project_service.apis]
}

# --- Findings table (matches models.Finding.to_dict()) ---
resource "google_bigquery_table" "findings" {
  dataset_id          = google_bigquery_dataset.secureflow.dataset_id
  table_id            = "findings"
  deletion_protection = false

  schema = <<EOF
[
  {"name": "id", "type": "STRING", "mode": "REQUIRED", "description": "UUID4 finding identifier"},
  {"name": "mr_iid", "type": "INTEGER", "mode": "NULLABLE", "description": "GitLab MR internal ID"},
  {"name": "project_id", "type": "STRING", "mode": "REQUIRED", "description": "GitLab project ID"},
  {"name": "scanner", "type": "STRING", "mode": "REQUIRED", "description": "Agent that produced this finding"},
  {"name": "severity", "type": "STRING", "mode": "REQUIRED", "description": "CRITICAL|HIGH|MEDIUM|LOW|INFO"},
  {"name": "title", "type": "STRING", "mode": "REQUIRED", "description": "Short finding title"},
  {"name": "description", "type": "STRING", "mode": "REQUIRED", "description": "Detailed explanation"},
  {"name": "file_path", "type": "STRING", "mode": "NULLABLE", "description": "File where issue was found"},
  {"name": "line_number", "type": "INTEGER", "mode": "NULLABLE", "description": "Line number in file"},
  {"name": "cve_ids", "type": "STRING", "mode": "REPEATED", "description": "Associated CVE identifiers"},
  {"name": "cvss_score", "type": "FLOAT", "mode": "NULLABLE", "description": "CVSS v3.1 base score"},
  {"name": "risk_score", "type": "INTEGER", "mode": "NULLABLE", "description": "Composite risk score 1-10"},
  {"name": "remediation", "type": "STRING", "mode": "NULLABLE", "description": "How to fix"},
  {"name": "recommended_fix", "type": "STRING", "mode": "NULLABLE", "description": "Exact code change"},
  {"name": "status", "type": "STRING", "mode": "REQUIRED", "description": "OPEN|APPROVED|FIXED|DISMISSED"},
  {"name": "created_at", "type": "TIMESTAMP", "mode": "REQUIRED", "description": "Finding creation time"},
  {"name": "resolved_at", "type": "TIMESTAMP", "mode": "NULLABLE", "description": "When resolved"}
]
EOF
}

# --- Audit log table (matches models.AuditLogEntry.to_dict()) ---
resource "google_bigquery_table" "audit_log" {
  dataset_id          = google_bigquery_dataset.secureflow.dataset_id
  table_id            = "audit_log"
  deletion_protection = false

  schema = <<EOF
[
  {"name": "id", "type": "STRING", "mode": "REQUIRED", "description": "UUID4 log entry ID"},
  {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED", "description": "When action occurred"},
  {"name": "agent", "type": "STRING", "mode": "REQUIRED", "description": "Agent that performed the action"},
  {"name": "action", "type": "STRING", "mode": "REQUIRED", "description": "What was done"},
  {"name": "tool_name", "type": "STRING", "mode": "REQUIRED", "description": "Tool that was called"},
  {"name": "tool_input", "type": "JSON", "mode": "NULLABLE", "description": "Arguments passed to tool"},
  {"name": "result", "type": "STRING", "mode": "NULLABLE", "description": "Outcome summary"},
  {"name": "approved_by", "type": "STRING", "mode": "NULLABLE", "description": "HITL approver username"}
]
EOF
}

# --- Approval queue table (matches models.ApprovalAction.to_dict()) ---
resource "google_bigquery_table" "approval_queue" {
  dataset_id          = google_bigquery_dataset.secureflow.dataset_id
  table_id            = "approval_queue"
  deletion_protection = false

  schema = <<EOF
[
  {"name": "id", "type": "STRING", "mode": "REQUIRED", "description": "UUID4 action ID"},
  {"name": "finding_id", "type": "STRING", "mode": "REQUIRED", "description": "Related finding ID"},
  {"name": "action_type", "type": "STRING", "mode": "REQUIRED", "description": "GitLab action type"},
  {"name": "action_payload", "type": "JSON", "mode": "NULLABLE", "description": "Full tool call arguments"},
  {"name": "status", "type": "STRING", "mode": "REQUIRED", "description": "PENDING|APPROVED|REJECTED|TIMEOUT_REJECTED"},
  {"name": "requested_at", "type": "TIMESTAMP", "mode": "REQUIRED", "description": "When approval was requested"},
  {"name": "decided_at", "type": "TIMESTAMP", "mode": "NULLABLE", "description": "When decision was made"},
  {"name": "decided_by", "type": "STRING", "mode": "NULLABLE", "description": "Approver username"}
]
EOF
}
