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

resource "google_compute_instance" "web" {
  name                      = "wac-web"
  machine_type              = "e2-micro"
  zone                      = local.zone
  allow_stopping_for_update = true
  tags                      = ["wac-web"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      size  = 30
      type  = "pd-standard"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.wac.id
    # IPV6_ONLY is not checked by `terraform validate`; a typo only shows at plan/apply.
    stack_type = var.enable_ipv4 ? "IPV4_IPV6" : "IPV6_ONLY"

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

  # R9: Postgres lives on the boot disk, so a replace wipes the database.
  # Before any plan that replaces this VM: run backup-db.sh, verify the dump
  # restores into a scratch DB, then ask Ali before removing this guard.
  lifecycle {
    prevent_destroy = true
  }

  # provision.sh fetches bootstrap.tgz and reads secrets on first boot.
  depends_on = [
    google_storage_bucket_object.bootstrap,
    google_storage_bucket_iam_member.deploy_vm_viewer,
    google_secret_manager_secret_iam_member.vm_env,
    google_secret_manager_secret_iam_member.vm_staging_sa_key,
  ]
}
