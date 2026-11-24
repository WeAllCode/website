locals {
  deploy_bucket_name         = "wac-deploy-${var.project_id}"
  backup_bucket_name         = "wac-backups-${var.project_id}"
  transfer_bucket_name       = "wac-transfer-${var.project_id}"
  staging_media_bucket_name  = "wac-staging-media-${var.project_id}"
  prod_media_cors_origins    = ["https://${var.domain}", "https://www.${var.domain}", "https://gcp.${var.domain}"]
  staging_media_cors_origins = ["https://staging.${var.domain}"]
}

# --- Prod media + static (public) ---------------------------------------------

resource "google_storage_bucket" "media" {
  name                        = var.media_bucket_name
  location                    = local.bucket_location
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "inherited"

  cors {
    origin          = local.prod_media_cors_origins
    method          = ["GET"]
    response_header = ["Content-Type"]
    max_age_seconds = 3600
  }

  depends_on = [google_project_service.apis]
}

resource "google_storage_bucket_iam_member" "media_public" {
  bucket = google_storage_bucket.media.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"

  depends_on = [google_org_policy_policy.allow_all_member_domains]
}

resource "google_storage_bucket_iam_member" "media_vm_admin" {
  bucket = google_storage_bucket.media.name
  role   = "roles/storage.objectAdmin"
  member = google_service_account.vm.member
}

# --- Staging media + static (public) ------------------------------------------

resource "google_storage_bucket" "staging_media" {
  name                        = local.staging_media_bucket_name
  location                    = local.bucket_location
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "inherited"

  cors {
    origin          = local.staging_media_cors_origins
    method          = ["GET"]
    response_header = ["Content-Type"]
    max_age_seconds = 3600
  }

  depends_on = [google_project_service.apis]
}

resource "google_storage_bucket_iam_member" "staging_media_public" {
  bucket = google_storage_bucket.staging_media.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"

  depends_on = [google_org_policy_policy.allow_all_member_domains]
}

# Only the staging SA writes staging media (R10).
resource "google_storage_bucket_iam_member" "staging_media_staging_admin" {
  bucket = google_storage_bucket.staging_media.name
  role   = "roles/storage.objectAdmin"
  member = google_service_account.staging.member
}

# --- Deploy bucket (private, versioned): releases, pointers, bootstrap.tgz ----

resource "google_storage_bucket" "deploy" {
  name                        = local.deploy_bucket_name
  location                    = local.bucket_location
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      num_newer_versions = 5
      with_state         = "ARCHIVED"
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_storage_bucket_iam_member" "deploy_vm_viewer" {
  bucket = google_storage_bucket.deploy.name
  role   = "roles/storage.objectViewer"
  member = google_service_account.vm.member
}

# R5: ship every infra/vm/ file to the VM. provision.sh downloads
# gs://<deploy-bucket>/bootstrap.tgz with the metadata token and installs it.
# Real env files (env.prod, env.staging, ...) are excluded; *.example stay.
data "archive_file" "bootstrap" {
  type        = "tar.gz"
  source_dir  = "${path.module}/../vm"
  output_path = "${path.module}/.build/bootstrap.tgz"
  excludes = concat(
    [for f in fileset("${path.module}/../vm", "**/env.*") : f if !endswith(f, ".example")],
    [for f in fileset("${path.module}/../vm", "**/.DS_Store") : f],
  )
}

# The provider hashes `source` at plan time and re-uploads when it changes.
# (source_md5hash wants base64 MD5; archive_file only exports hex, so it is not set.)
resource "google_storage_bucket_object" "bootstrap" {
  bucket        = google_storage_bucket.deploy.name
  name          = "bootstrap.tgz"
  source        = data.archive_file.bootstrap.output_path
  content_type  = "application/gzip"
  cache_control = "no-store"
}

# --- Backup bucket (private): VM can write and read, never delete (R6) --------

resource "google_storage_bucket" "backups" {
  name                        = local.backup_bucket_name
  location                    = local.bucket_location
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_storage_bucket_iam_member" "backups_vm_creator" {
  bucket = google_storage_bucket.backups.name
  role   = "roles/storage.objectCreator"
  member = google_service_account.vm.member
}

resource "google_storage_bucket_iam_member" "backups_vm_viewer" {
  bucket = google_storage_bucket.backups.name
  role   = "roles/storage.objectViewer"
  member = google_service_account.vm.member
}

# --- Transfer bucket (private, not versioned): one-off DB dumps (R12) ---------

resource "google_storage_bucket" "transfer" {
  name                        = local.transfer_bucket_name
  location                    = local.bucket_location
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  # No soft delete: `gcloud storage rm` must really remove a prod dump.
  soft_delete_policy {
    retention_duration_seconds = 0
  }

  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_storage_bucket_iam_member" "transfer_vm_viewer" {
  bucket = google_storage_bucket.transfer.name
  role   = "roles/storage.objectViewer"
  member = google_service_account.vm.member
}
