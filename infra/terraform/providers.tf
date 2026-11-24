# Credentials come from GOOGLE_OAUTH_ACCESS_TOKEN (see README), never ADC.
provider "google" {
  project               = var.project_id
  region                = local.region
  zone                  = local.zone
  billing_project       = var.project_id
  user_project_override = true
}

# Reads CLOUDFLARE_API_TOKEN from the environment.
provider "cloudflare" {}

locals {
  region = "us-central1"
  zone   = "us-central1-a"

  # Every bucket is pinned here (R16).
  bucket_location = "US-CENTRAL1"
}

data "google_project" "this" {
  project_id = var.project_id

  depends_on = [google_project_service.apis]
}
