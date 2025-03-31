variable "project_id" {
  type        = string
}

variable "region" {
  description = "GCP region (e.g., europe-west1)"
  type        = string
}

variable "zone" {
  description = "GCP zone (e.g., europe-west1-b)"
  type        = string
}

variable "bucket_name" {
  description = "Name of the Cloud Storage bucket for Velib data"
  type        = string
}


variable "composer_name"{
  description = "Name of the composer env"
  type = string
}


variable "dataset_name"{
  description = "Name of the Big Query dataset"
  type = string
}
