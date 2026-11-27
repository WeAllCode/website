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
    "iap.googleapis.com",
  ])
}

# iap: SSH via IAP TCP forwarding to nic0's internal IPv4 (the VM is dual-stack).
resource "google_project_service" "apis" {
  for_each = local.apis

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}
