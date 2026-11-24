# Cloudflare Origin CA certificate for the VM's Caddy (Cloudflare does public TLS).
# The private key is in state (private bucket) and in instance metadata
# (wac-origin-key): accepted risk, see infra/vm/README.md.

resource "tls_private_key" "origin" {
  algorithm   = "ECDSA"
  ecdsa_curve = "P256"
}

resource "tls_cert_request" "origin" {
  private_key_pem = tls_private_key.origin.private_key_pem
  dns_names = [
    var.domain,
    "www.${var.domain}",
    "gcp.${var.domain}",
    "staging.${var.domain}",
  ]

  subject {
    common_name  = var.domain
    organization = "We All Code"
  }
}

# Cloudflare returns hostnames sorted; sort() here so the list diff doesn't force replacement.
resource "cloudflare_origin_ca_certificate" "origin" {
  csr                = tls_cert_request.origin.cert_request_pem
  hostnames          = sort(tls_cert_request.origin.dns_names)
  request_type       = "origin-ecc"
  requested_validity = 5475
}
