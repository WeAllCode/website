# Custom-mode network: the auto-mode default network can't host IPv6 subnets.
resource "google_compute_network" "wac" {
  name                    = "wac"
  auto_create_subnetworks = false

  depends_on = [google_project_service.apis]
}

resource "google_compute_subnetwork" "wac" {
  name                     = "wac-${local.region}"
  network                  = google_compute_network.wac.id
  region                   = local.region
  ip_cidr_range            = "10.10.0.0/24"
  stack_type               = "IPV4_IPV6"
  ipv6_access_type         = "EXTERNAL"
  private_ip_google_access = true
}

data "cloudflare_ip_ranges" "cf" {}

# HTTPS from Cloudflare only. No SSH and nothing on port 80; admin access is
# the serial console (var.serial_console).
resource "google_compute_firewall" "https_cloudflare_ipv6" {
  name          = "wac-https-cloudflare-ipv6"
  network       = google_compute_network.wac.id
  direction     = "INGRESS"
  source_ranges = data.cloudflare_ip_ranges.cf.ipv6_cidrs
  target_tags   = ["wac-web"]

  allow {
    protocol = "tcp"
    ports    = ["443"]
  }
}

resource "google_compute_firewall" "https_cloudflare_ipv4" {
  count = var.enable_ipv4 ? 1 : 0

  name          = "wac-https-cloudflare-ipv4"
  network       = google_compute_network.wac.id
  direction     = "INGRESS"
  source_ranges = data.cloudflare_ip_ranges.cf.ipv4_cidrs
  target_tags   = ["wac-web"]

  allow {
    protocol = "tcp"
    ports    = ["443"]
  }
}
