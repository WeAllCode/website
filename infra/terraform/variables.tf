variable "project_id" {
  description = "We All Code GCP project ID (e.g. wac-website-xxxx)."
  type        = string
}

variable "billing_account_id" {
  description = "Billing account ID (XXXXXX-XXXXXX-XXXXXX) for the budget alert."
  type        = string
}

variable "cloudflare_zone_id" {
  description = "Cloudflare zone ID for var.domain."
  type        = string
}

variable "domain" {
  description = "Apex domain."
  type        = string
  default     = "weallcode.org"
}

variable "media_bucket_name" {
  description = "Public prod media/static bucket name (e.g. wac-media-<project_id>)."
  type        = string
}

variable "enable_ipv4" {
  description = "Fallback: give the VM an external IPv4 (~$3.65/month). Changing it replaces the VM (stack type is immutable); see README."
  type        = bool
  default     = false
}

variable "serial_console" {
  description = "Turn on the interactive serial console (serial-port-enable) for admin access."
  type        = bool
  default     = false
}

variable "serial_console_password_hash" {
  description = "Temporary crypt(5) password hash for a local serial-console login (R25). Passed as metadata wac-serial-password-hash only while serial_console is true. Clear it after Task F."
  type        = string
  default     = ""
  sensitive   = true
}

variable "cutover" {
  description = "false: only gcp.<domain> (and staging.<domain>) point at the VM. true: apex and www do too."
  type        = bool
  default     = false
}

variable "project_owners" {
  description = "Members granted roles/owner on the project."
  type        = list(string)
  # daniel.m.conrad@gmail.com is NOT here: a gmail.com Owner can only be added
  # by a console invite he accepts by email (R2). Ali invites him by hand; after
  # he accepts, the lead adds "user:daniel.m.conrad@gmail.com" to this list in
  # terraform.tfvars and runs `terraform import` for that binding (Task F).
  default = [
    "user:ali@weallcode.org",
    "user:hello@weallcode.org",
  ]
}

variable "allow_all_member_domains" {
  description = "R3: add a project-level org policy override (allow_all) for iam.allowedPolicyMemberDomains. Set true only if 0b found the constraint enforced."
  type        = bool
  default     = false
}

variable "staging_basic_auth_hash" {
  description = "bcrypt hash from `caddy hash-password` for staging basic auth. Passed as metadata wac-staging-basic-auth. The password itself lives only in 1Password."
  type        = string
  sensitive   = true
}

variable "resend_dns_records" {
  description = "Resend domain DNS records from the Resend API (Checkpoint 0b). name may be relative (send, resend._domainkey) or a full FQDN."
  type = list(object({
    type     = string
    name     = string
    content  = string
    priority = optional(number)
  }))
  default = []
}
