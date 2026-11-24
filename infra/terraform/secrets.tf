# Terraform creates the secrets only, never versions, so no secret values land
# in state. Versions are added with `gcloud secrets versions add` (README).

resource "google_secret_manager_secret" "env" {
  for_each = toset(["wac-env-prod", "wac-env-staging"])

  secret_id = each.value

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

# JSON key for the wac-staging-vm SA (R10). Created by hand with gcloud and
# added as a version; never created in Terraform (it would land in state).
resource "google_secret_manager_secret" "staging_sa_key" {
  secret_id = "wac-staging-sa-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

# Root on the VM deploys both targets with the prod VM SA, so it reads every
# secret: both env files and the staging SA key.
resource "google_secret_manager_secret_iam_member" "vm_env" {
  for_each = google_secret_manager_secret.env

  secret_id = each.value.id
  role      = "roles/secretmanager.secretAccessor"
  member    = google_service_account.vm.member
}

resource "google_secret_manager_secret_iam_member" "vm_staging_sa_key" {
  secret_id = google_secret_manager_secret.staging_sa_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = google_service_account.vm.member
}

# The staging SA can read only the staging env.
resource "google_secret_manager_secret_iam_member" "staging_env" {
  secret_id = google_secret_manager_secret.env["wac-env-staging"].id
  role      = "roles/secretmanager.secretAccessor"
  member    = google_service_account.staging.member
}
