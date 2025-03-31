# Basic Info 
terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "6.8.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Create the Google Cloud Storage Bucket
# TBD: need to add archive logic
resource "google_storage_bucket" "velib_bucket" {
  name     = var.bucket_name
  location = var.region
  force_destroy = true
}

# Create the Google Big Query Dataset
resource "google_bigquery_dataset" "velib_dataset" {
  dataset_id                  = var.dataset_name
  location                    = var.region
}


# Create the Google Cloud Composer
/*
resource "google_composer_environment" "velib_composer" {
  name   = var.composer_name
  region = var.region
  config {
    software_config {
      image_version = "composer-3-airflow-2"
      env_variables = {
        # Use project instead of project_id, as it is a reserved word in Google Composer
        project     = var.project_id
        bucket_name = var.bucket_name
        region      = var.region
        dataset_name = var.dataset_name
      }
    }
  }
}

output "dag_bucket" {
  value       = google_composer_environment.velib_composer.config[0].dag_gcs_prefix
  description = "The Cloud Storage prefix for DAGs (e.g., gs://<bucket>/dags/)"
}
*/