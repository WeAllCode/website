output "vm_ipv6" {
  description = "External IPv6 address of wac-web."
  value       = local.vm_ipv6
}

output "vm_ipv4" {
  description = "External IPv4 address of wac-web (null unless enable_ipv4)."
  value       = local.vm_ipv4
}

output "media_bucket_url" {
  description = "Public base URL of the prod media/static bucket."
  value       = "https://storage.googleapis.com/${google_storage_bucket.media.name}"
}

output "staging_media_bucket_url" {
  description = "Public base URL of the staging media/static bucket."
  value       = "https://storage.googleapis.com/${google_storage_bucket.staging_media.name}"
}

output "deploy_bucket" {
  value = google_storage_bucket.deploy.name
}

output "backup_bucket" {
  value = google_storage_bucket.backups.name
}

output "transfer_bucket" {
  value = google_storage_bucket.transfer.name
}

output "vm_service_account" {
  value = google_service_account.vm.email
}

output "staging_service_account" {
  description = "Create its key by hand and add it to secret wac-staging-sa-key (README)."
  value       = google_service_account.staging.email
}
