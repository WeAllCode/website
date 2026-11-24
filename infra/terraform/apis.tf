locals {
  apis = toset([
    "compute.googleapis.com",
    "storage.googleapis.com",
    "billingbudgets.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "cloudbilling.googleapis.com",
    "orgpolicy.googleapis.com",
  ])
}

# No IAP: IAP TCP forwarding needs an internal IPv4, which an IPv6-only VM lacks.
resource "google_project_service" "apis" {
  for_each = local.apis

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}
