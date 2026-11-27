resource "google_service_account" "vm" {
  account_id   = "wac-web"
  display_name = "wac-web VM (prod; root deploys both targets)"

  depends_on = [google_project_service.apis]
}

# R10: staging's own identity. Staging authenticates with a JSON key for this
# SA (secret wac-staging-sa-key), never with the VM's metadata token.
resource "google_service_account" "staging" {
  account_id   = "wac-staging-vm"
  display_name = "wac staging app on the wac-web VM"

  depends_on = [google_project_service.apis]
}

locals {
  vm_metadata = merge(
    {
      startup-script             = file("${path.module}/../vm/provision.sh")
      serial-port-logging-enable = "TRUE"
      serial-port-enable         = var.serial_console ? "TRUE" : "FALSE"
      enable-oslogin             = "TRUE"

      wac-media-bucket         = google_storage_bucket.media.name
      wac-staging-media-bucket = google_storage_bucket.staging_media.name
      wac-deploy-bucket        = google_storage_bucket.deploy.name
      wac-backup-bucket        = google_storage_bucket.backups.name
      wac-transfer-bucket      = google_storage_bucket.transfer.name
      wac-origin-cert          = cloudflare_origin_ca_certificate.origin.certificate
      wac-origin-key           = tls_private_key.origin.private_key_pem
      wac-staging-basic-auth   = var.staging_basic_auth_hash
    },
    # R25: temporary local password for the serial console, only while it's on.
    var.serial_console && var.serial_console_password_hash != "" ? {
      wac-serial-password-hash = var.serial_console_password_hash
    } : {},
  )
}

# Imported from the live boot disk (`terraform import google_compute_disk.web
# projects/<project_id>/zones/us-central1-a/disks/wac-web`). Postgres lives on it:
# it must never be replaced. The instance can be recreated around it (README).
resource "google_compute_disk" "web" {
  name  = "wac-web"
  zone  = local.zone
  type  = "pd-standard"
  size  = 30
  image = "debian-cloud/debian-12"

  lifecycle {
    prevent_destroy = true
    ignore_changes  = [image, snapshot]
  }
}

resource "google_compute_instance" "web" {
  name                      = "wac-web"
  machine_type              = "e2-micro"
  zone                      = local.zone
  allow_stopping_for_update = true
  tags                      = ["wac-web"]

  # The disk outlives the instance, so a recreate keeps Postgres.
  boot_disk {
    source      = google_compute_disk.web.self_link
    auto_delete = false
  }

  network_interface {
    subnetwork = google_compute_subnetwork.wac.id
    # Always dual-stack: nic0's internal IPv4 is what IAP TCP forwarding (SSH)
    # needs. There is still no external IPv4 unless var.enable_ipv4.
    stack_type = "IPV4_IPV6"

    ipv6_access_config {
      network_tier = "PREMIUM"
    }

    dynamic "access_config" {
      for_each = var.enable_ipv4 ? [1] : []
      content {}
    }
  }

  shielded_instance_config {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }

  service_account {
    email  = google_service_account.vm.email
    scopes = ["cloud-platform"]
  }

  metadata = local.vm_metadata

  # R9: Postgres lives on the boot disk (google_compute_disk.web, auto_delete =
  # false), so a replace no longer wipes it, but don't let Terraform do it: use
  # the README's stop/snapshot/delete --keep-disks=boot/state rm swap, after
  # backup-db.sh and asking Ali.
  #
  # deploy-nonce-<target> is written by infra/vm/release.sh (gcloud add-metadata) on every
  # release to trigger wac-deploy-watch; it is not Terraform's, so it must not show as drift.
  lifecycle {
    prevent_destroy = true
    ignore_changes = [
      metadata["deploy-nonce-prod"],
      metadata["deploy-nonce-staging"],
    ]
  }

  # provision.sh fetches bootstrap.tgz and reads secrets on first boot.
  depends_on = [
    google_storage_bucket_object.bootstrap,
    google_storage_bucket_iam_member.deploy_vm_viewer,
    google_secret_manager_secret_iam_member.vm_env,
    google_secret_manager_secret_iam_member.vm_staging_sa_key,
  ]
}
