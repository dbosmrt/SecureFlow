# Infrastructure (Terraform) Directory

This directory contains the Infrastructure as Code (IaC) required to deploy SecureFlow on Google Cloud.

## Resources Provisioned

- **`main.tf`**: Configures the Google Cloud provider and defines the Cloud Run service that hosts the FastAPI application and dashboard. It handles injecting secrets from Secret Manager into the container's environment variables.
- **`pubsub.tf`**: Provisions the Pub/Sub topic and the pull subscription with a 10-minute acknowledgment deadline to accommodate long-running agent tasks.
- **`bigquery.tf`**: Creates the `secureflow` dataset and the three structured tables (`findings`, `audit_log`, `approval_queue`) with their exact schemas.
- **`secret_manager.tf`**: Defines the placeholders for the GitLab Token and Webhook Secret.
- **`iam.tf`**: Creates a dedicated `secureflow` Service Account and binds the necessary roles (Pub/Sub Publisher/Subscriber, BigQuery Data Editor, Vertex AI User, and Secret Accessor).
- **`variables.tf`**: Parameterizes the Terraform deployment (e.g., `project_id`, `region`).
