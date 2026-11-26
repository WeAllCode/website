# Plan: IAP SSH to wac-web

## Goal and done

As Ali (or the lead), I want `CLOUDSDK_ACTIVE_CONFIG_NAME=wac gcloud compute ssh wac-web --zone us-central1-a --tunnel-through-iap` to open a shell, so I can run the VM without the serial-console steps.

Acceptance criteria:

1. The command above gets a shell as Ali's OS Login user, with `sudo`.
2. Prod (`https://www.weallcode.org`) and staging serve as before. Postgres (`wac`, `wac_staging`), `/var/lib/wac` and `/etc/wac` survive unchanged, because the boot disk is reused.
3. SSH is reachable only from IAP's range `35.235.240.0/20`. Nothing new is open to the internet.
4. Everything is in Terraform. `terraform plan` shows no changes after the apply.

## Root cause (diagnosed 2026-11-26, read-only)

`4047 Failed to lookup instance` is IAP reporting that it has no IPv4 target. `wac-web` is `IPV6_ONLY` (`nic0` has no internal IPv4), and IAP TCP forwarding only connects to a NIC's internal IPv4. This is by design since the GCP move (#1613), so it has never worked on this VM. `infra/terraform/apis.tf:14` already says so.

Evidence:

- `gcloud compute instances describe`: `nic0.stackType = IPV6_ONLY`, no `networkIP`, no `accessConfigs`, only `external-ipv6`. The subnet `wac-us-central1` is `IPV4_IPV6` with `10.10.0.0/24`, so an internal IPv4 is available.
- Firewall on network `wac`: only `wac-https-cloudflare-ipv6` (tcp:443). No rule for `35.235.240.0/20` tcp:22. (`default-allow-ssh` is on the unused `default` network.)
- Enabled APIs: `compute` and `oslogin`; `iap.googleapis.com` is not enabled.
- IAM: `ali@weallcode.org` has `roles/owner`, which should include `iap.tunnelInstances.accessViaIAP` and `compute.instances.osAdminLogin`; T0 verifies this. Metadata has `enable-oslogin = TRUE`. No IAM change is expected.
- Terraform state `gs://wac-tfstate-wac-website-7bda80/prod/default.tfstate` (serial 22) matches live for the firewall, APIs and NIC, so there is no drift. A full `terraform plan` was not run because there is no `terraform.tfvars` on this machine (it needs the Cloudflare token and the filled-in vars).
- Side effect: `gcloud compute ssh --troubleshoot` auto-answered "yes" and **enabled `networkmanagement.googleapis.com`** on the project, then failed because the change had not propagated. That API is not in Terraform. Ask Ali whether to disable it (`gcloud services disable networkmanagement.googleapis.com`).

## Decision Ali must make first

A NIC's stack type can't change in place, so adding an internal IPv4 needs a new instance (`infra/terraform/README.md:80`).

| Option | Cost | Meets the goal |
|---|---|---|
| **C. New instance on the existing boot disk (recommended)** | A few minutes of downtime. No DB restore. $0/month (internal IPv4 only). | Yes |
| A. New VM on a fresh disk, then restore the dump | Restore risk: an empty-DB deploy goes live, staging is empty, `/etc/wac` flags are lost | Yes |
| B. Keep using the serial console (`infra/vm/README.md:171-179`) | Nothing | No; update the docs only |

The rest of this plan is option C. Don't start until Ali approves and picks a window.

## Read first

- `infra/terraform/vm.tf:39-69`: the instance, `boot_disk` (debian-12, 30 GB, `pd-standard`), and `network_interface` at 56-69. `vm.tf:90-91` is `prevent_destroy`.
- `infra/terraform/network.tf:21-49`: the firewall rules to copy for the IAP rule.
- `infra/terraform/apis.tf`: the API list. The line-14 comment becomes wrong.
- `infra/terraform/variables.tf:27-31`: `enable_ipv4`.
- `infra/terraform/dns.tf:3-4`: DNS follows the VM's external IPv6. The new instance gets a new address, and the same apply updates the Cloudflare AAAA records.
- `infra/terraform/README.md:9-18` (credentials), `:80` (replacement notes), `:86`; `infra/vm/README.md:139-144` (the restore TOC filter, for the fallback only) and `:171-179` (admin access docs).
- Changing `infra/vm/README.md` also changes `bootstrap.tgz` (`google_storage_bucket_object.bootstrap`). Apply only from merged `main`, because the archive is built from the local checkout.
- Docs: https://cloud.google.com/iap/docs/using-tcp-forwarding ("Create a firewall rule", "Tunneling SSH connections"), and `google_compute_instance.boot_disk.source` / `google_compute_disk` in the Terraform Google provider docs.

## Tasks

T0 can run in parallel with T1: T0 is gcloud reads only and T1 is file edits only.

**T0: Pre-flight checks (lead only, read-only)**

- `gcloud projects test-iam-permissions wac-website-7bda80 --permissions=iap.tunnelInstances.accessViaIAP,compute.instances.osAdminLogin,iam.serviceAccounts.actAs`. All three must come back; if any is missing, stop and ask Ali.
- Get the boot disk's name and its settings: `gcloud compute instances describe wac-web --zone us-central1-a --format='value(disks[0].source,disks[0].autoDelete)'` and `gcloud compute disks describe <name> --zone us-central1-a`.

**T1: Terraform and docs** (files: `infra/terraform/vm.tf`, `network.tf`, `apis.tf`, `variables.tf`, `README.md`, `infra/vm/README.md`)

- `vm.tf`: add `google_compute_disk.web` (name from T0, zone, `type = "pd-standard"`, `size = 30`, `image = "debian-cloud/debian-12"`, `lifecycle { prevent_destroy = true, ignore_changes = [image, snapshot] }`). Change `boot_disk` to `source = google_compute_disk.web.self_link` with `auto_delete = false`. Set `stack_type = "IPV4_IPV6"` always, and keep `access_config` gated on `var.enable_ipv4`. Keep `prevent_destroy` on the instance.
- `network.tf`: add `google_compute_firewall.ssh_iap` with name `wac-ssh-iap`, network `wac`, ingress, `source_ranges = ["35.235.240.0/20"]`, tcp:22, `target_tags = ["wac-web"]`, `count = var.iap_ssh ? 1 : 0`. Copy `https_cloudflare_ipv4` (`network.tf:36`) and update the comment at `:21`.
- `apis.tf`: add `iap.googleapis.com` and replace the line-14 comment.
- `variables.tf`: add `iap_ssh` (bool, default `true`, "Allow SSH from IAP's TCP-forwarding range"). Reword `enable_ipv4`: it now only adds an external IPv4, though changing it still recreates the instance.
- READMEs: admin access is now IAP SSH first, with the serial console as the fallback. Say that the VM has an internal IPv4 but no IPv4 egress (no NAT), and that `README.md:80`'s procedure is now the reuse-the-disk swap below.
- Proof: `terraform fmt -check && terraform validate` in `infra/terraform`.

Pitfalls:

- There is no IPv4 egress (no Cloud NAT, no external IPv4). Once the VM has an internal IPv4, a host that publishes only A records (for example GitHub) times out instead of failing fast. IPv6 stays preferred (RFC 6724), and Google APIs still work through Private Google Access. Check the deploy and backup timers after the swap.
- The disk attributes must match live exactly, or the plan shows a disk replacement. `prevent_destroy` on the disk is the guard; never lift it.
- Don't open tcp:22 to anything but `35.235.240.0/20`. Don't add IAM.

## How to run it

1. Read the whole plan. You are the lead and write no code. Give T1 to one sub-agent. Its brief names T1 and only T1's files, gives the proof command, says not to run git, and asks for the list of changed files plus the proof output. Run T0 yourself at the same time.
2. Check the actual diff yourself, run the proof, commit, and open a PR. Ali reviews and merges.
3. Maintenance window, on a `main` checkout that includes the merge. Ali approves each step, because this is prod.
   1. Safety net: run `gcloud compute disks snapshot <disk> --zone us-central1-a --snapshot-names wac-web-pre-iap-<date>`, and start a fresh `db/wac-*.dump` (`sudo systemctl start wac-backup` over the serial console, or rely on the most recent nightly dump and write down its timestamp).
   2. Build `terraform.tfvars` from `terraform.tfvars.example` with Ali. Set the credentials (`infra/terraform/README.md:9-18`), then `terraform init -backend-config="bucket=wac-tfstate-wac-website-7bda80"` (check the backend prefix `prod` in `versions.tf`).
   3. `terraform import google_compute_disk.web projects/wac-website-7bda80/zones/us-central1-a/disks/<disk>`.
   4. If T0 showed `autoDelete = true`, run `gcloud compute instances set-disk-auto-delete wac-web --zone us-central1-a --disk <disk> --no-auto-delete`. Re-check it.
   5. `gcloud compute instances stop wac-web`, then `gcloud compute instances delete wac-web --zone us-central1-a --keep-disks=boot`, then `terraform state rm google_compute_instance.web`. Prod is down from here.
   6. `terraform plan`. Expect: create `google_compute_instance.web`, create `wac-ssh-iap` and `iap.googleapis.com`, update the Cloudflare AAAA records and `bootstrap`. **No change to `google_compute_disk.web`.** If you see anything else, stop and ask. Once Ali approves, `terraform apply`.
   7. Wait for the boot (`gcloud compute instances get-serial-port-output wac-web` until `wac-provision: done`). `provision.sh` is idempotent and keeps the existing DB, `/var/lib/wac/infra-vm` and `/etc/wac`.
   8. `terraform plan` shows no changes.
4. Write the results and evidence into Progress.

Rollback: if the new instance won't boot, create an instance from the snapshot with the old `IPV6_ONLY` config (`git revert` T1, then import). If the disk is lost, the last resort is a fresh VM plus a dump restore using the TOC filter at `infra/vm/README.md:139-144`, then `sudo wac-refresh-staging-db` and re-creating `/etc/wac/reminders-enabled` if it was there.

## Proof

| Criterion | Test | One-line break that must fail it |
|---|---|---|
| 1 | `CLOUDSDK_ACTIVE_CONFIG_NAME=wac gcloud compute ssh wac-web --zone us-central1-a --tunnel-through-iap -- 'sudo -n true && hostname'` prints `wac-web` | Set `iap_ssh = false` in tfvars: the plan must show the rule being destroyed (plan only; don't apply) |
| 2 | `curl -sI https://www.weallcode.org` returns 200; staging returns 401 without auth; over SSH, `sudo -u wac psql -d wac -c 'select count(*) from auth_user'` matches the pre-swap dump; `test -f /etc/wac/reminders-enabled` gives the same result as before | n/a |
| 3 | `gcloud compute firewall-rules list --filter=network~wac` shows only the 443 rule(s) plus `wac-ssh-iap` with `35.235.240.0/20` | n/a |
| 4 | `terraform plan` reports "No changes" | n/a |

Also run `terraform fmt -check` and `terraform validate`. Check the real files, not the sub-agent's report. Before calling it done, log in through IAP and run `systemctl list-timers 'wac-*'` and `journalctl -u 'wac-deploy@*' -n 50` to confirm that deploys, backups and reminders still run.

## Review

Fresh sub-agent, 2026-11-26. Findings and how the plan handles them:

- Blocker (option A): on a fresh disk, boot-time deploys run `migrate` on an empty DB and go live while the AAAA record already points at the new VM. **Fixed:** the plan now uses option C (reuse the boot disk), so no restore is needed.
- Blocker (option A): `pg_restore --clean` fails on `pg_stat_statements`. **Fixed:** there is no restore in option C. The fallback uses the TOC filter (`infra/vm/README.md:139-144`).
- Major: there was no rollback. **Fixed:** a disk snapshot plus a dump before the swap, and a Rollback paragraph.
- Major: it was unverified whether `stack_type` is ForceNew. If it were in-place, `allow_stopping_for_update` would stop prod mid-apply. **Fixed:** the plan deletes the instance itself and runs `state rm` before `plan`, so the plan can only show a create.
- Major: the fresh-disk path would lose `/etc/wac/reminders-enabled` and leave `wac_staging` empty. **Fixed:** the disk is reused. Both steps are listed in the fallback.
- Major: there was no rehearsal. **Accepted with a guard:** step 6's plan must show no disk change, and the snapshot covers a mistake. A scratch-project dry run is optional if Ali wants one.
- Minor: owner permissions were unchecked. **Fixed:** T0 runs `test-iam-permissions`.
- Minor: there was no step for getting the dump onto the VM. **N/A** under option C.
- Minor: line refs were off. **Fixed** (`vm.tf:56-69`, `network.tf:21-49`, `infra/vm/README.md:171-179`).
- Minor: the plan also updates `bootstrap.tgz`. **Fixed:** it is in step 6's expected list, and the apply runs from merged `main`.
- Minor: confirm the dump timestamp is after deploys stopped. **Covered:** step 3.1 notes the timestamp, and the disk is the real copy anyway.

## Progress

