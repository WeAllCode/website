locals {
  vm_ipv6 = google_compute_instance.web.network_interface[0].ipv6_access_config[0].external_ipv6
  vm_ipv4 = var.enable_ipv4 ? google_compute_instance.web.network_interface[0].access_config[0].nat_ip : null
}

# Full strict mode zone-wide: the VM listens only on 443 with an Origin CA cert,
# and Heroku's origin has valid ACM certs. Checkpoint 0 recorded the old mode.
resource "cloudflare_zone_setting" "ssl" {
  zone_id    = var.cloudflare_zone_id
  setting_id = "ssl"
  value      = "strict"
}

# --- Always on ---------------------------------------------------------------

resource "cloudflare_dns_record" "gcp_aaaa" {
  zone_id = var.cloudflare_zone_id
  name    = "gcp.${var.domain}"
  type    = "AAAA"
  content = local.vm_ipv6
  proxied = true
  ttl     = 1
}

resource "cloudflare_dns_record" "staging_aaaa" {
  zone_id = var.cloudflare_zone_id
  name    = "staging.${var.domain}"
  type    = "AAAA"
  content = local.vm_ipv6
  proxied = true
  ttl     = 1
}

# --- Only after cutover ------------------------------------------------------
# Delete the Heroku-era apex/www records by hand first (Task H step 4), or
# creating these fails on the duplicate name.

resource "cloudflare_dns_record" "apex_aaaa" {
  count = var.cutover ? 1 : 0

  zone_id = var.cloudflare_zone_id
  name    = var.domain
  type    = "AAAA"
  content = local.vm_ipv6
  proxied = true
  ttl     = 1
}

resource "cloudflare_dns_record" "apex_a" {
  count = var.cutover && var.enable_ipv4 ? 1 : 0

  zone_id = var.cloudflare_zone_id
  name    = var.domain
  type    = "A"
  content = local.vm_ipv4
  proxied = true
  ttl     = 1
}

resource "cloudflare_dns_record" "www_cname" {
  count = var.cutover ? 1 : 0

  zone_id = var.cloudflare_zone_id
  name    = "www.${var.domain}"
  type    = "CNAME"
  content = var.domain
  proxied = true
  ttl     = 1
}
