# Resend sending-domain records (R19). Checkpoint 0b creates the Resend domain
# and copies the returned records into terraform.tfvars (resend_dns_records).
# DNS-only (never proxied). The Google Workspace MX/SPF at the apex stay out
# of Terraform.

locals {
  resend_records = {
    for r in var.resend_dns_records :
    "${upper(r.type)}:${r.name}:${substr(sha1(r.content), 0, 8)}" => merge(r, {
      fqdn = (r.name == var.domain || endswith(r.name, ".${var.domain}")) ? r.name : "${r.name}.${var.domain}"
    })
  }
}

resource "cloudflare_dns_record" "resend" {
  for_each = local.resend_records

  zone_id  = var.cloudflare_zone_id
  name     = each.value.fqdn
  type     = upper(each.value.type)
  content  = each.value.content
  priority = each.value.priority
  proxied  = false
  ttl      = 1
}
