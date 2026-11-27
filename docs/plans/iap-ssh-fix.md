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
- External research confirms it. The same error on the same setup (`IPV6_ONLY` with an `EXTERNAL` IPv6, code 4047) has a Google answer: "Directly accessing an IPv6-only VM using IAP TCP forwarding is not currently possible, if the VM uses an external (GUA)" (https://discuss.google.dev/t/failed-to-lookup-instance-when-using-iap-ssh-on-ipv6-only-vm/190749, June 2025). IAP's IPv6 range `2600:2d00:1:7::/64` only works for **internal** (ULA) IPv6 subnets (Google codelab: https://codelabs.developers.google.com/codelabs/private-nat64). `nic0` can't be internal IPv6, because Cloudflare needs its external IPv6. The docs say "IAP proxies connect to the primary internal IPv4 address of `nic0`" (https://docs.cloud.google.com/iap/docs/using-tcp-forwarding).
- Stack type can't change in place. Google's docs say "You can't change the stack type of an IPv6-only instance"; in-place changes are only IPv4-only ↔ dual-stack (https://docs.cloud.google.com/compute/docs/ip-addresses/configure-ipv6-address). So the instance has to be recreated. Pinned provider: `hashicorp/google` 8.12.0.
- Side effect: `gcloud compute ssh --troubleshoot` auto-answered "yes" and **enabled `networkmanagement.googleapis.com`** on the project, then failed because the change had not propagated. That API is not in Terraform. It was disabled again on 2026-11-26, at Ali's request.

## Decision Ali must make first

A NIC's stack type can't change in place, so adding an internal IPv4 needs a new instance (`infra/terraform/README.md:80`).

| Option | Cost | Meets the goal |
|---|---|---|
| **C. New instance on the existing boot disk (recommended)** | A few minutes of downtime. No DB restore. $0/month (internal IPv4 only). | Yes |
| A. New VM on a fresh disk, then restore the dump | Restore risk: an empty-DB deploy goes live, staging is empty, `/etc/wac` flags are lost | Yes |
| B. Keep using the serial console (`infra/vm/README.md:171-179`) | Nothing | No; update the docs only |

### Cost check (Cloud Billing Catalog API, 2026-11-26)

Option C stays $0/month. The only one-off cost is the optional snapshot.

| Item | Price | Effect |
|---|---|---|
| Internal IPv4 on `nic0` | No SKU, free | $0 |
| IAP TCP forwarding | No IAP billing service or SKU, free | $0 |
| Firewall rule, IAP API | Free | $0 |
| External IPv6 (new address) | No IPv6 SKU, free | $0 |
| e2-micro + 30 GB `pd-standard` | Free tier, unchanged (same single disk, same VM count) | $0 |
| External IPv4 | Not added (`enable_ipv4` stays `false`) | $0 |
| Safety snapshot (step 3.4) | "Storage PD Snapshot" $0.05/GiB-month, prorated, billed on used compressed data, not in the free tier | A few cents if it's deleted within days; ~$0.25–0.40/month if kept (est. 5–8 GiB used) |
| `networkmanagement.googleapis.com` (enabled by accident) | Enabling it is free; only connectivity tests bill | Disabled 2026-11-26 |

To keep it at $0, delete the snapshot after the Proof passes (step 3.9). Brief IAP SSH sessions use negligible egress, well inside the 1 GB free tier.

The rest of this plan is option C. Don't start until Ali approves and picks a window.

## Read first

- `infra/terraform/vm.tf:41-105`: the instance. `boot_disk` is at 48-54 (debian-12, 30 GB, `pd-standard`), `network_interface` at 56-69, and the `lifecycle` block with `prevent_destroy` at 90-91.
- CI (`.github/workflows/ci.yml:150-157`) only runs `fmt` and `validate`. Nothing applies on merge.
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

- `vm.tf`: add `google_compute_disk.web` (name from T0, zone, `type = "pd-standard"`, `size = 30`, `image = "debian-cloud/debian-12"`, `lifecycle { prevent_destroy = true, ignore_changes = [image, snapshot] }`). Change `boot_disk` to `source = google_compute_disk.web.self_link` with `auto_delete = false`, and **remove `initialize_params`**, which conflicts with `source`. Set `stack_type = "IPV4_IPV6"` always, and keep `access_config` gated on `var.enable_ipv4`. Keep `prevent_destroy` on the instance.
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
2. Check the actual diff yourself, run the proof, commit, and open a PR. **Before Ali merges**, do the tfvars gate:
   1. Build `terraform.tfvars` from `terraform.tfvars.example` with Ali. Set the credentials (`infra/terraform/README.md:9-18`), then `terraform init -backend-config="bucket=wac-tfstate-wac-website-7bda80"` (check the backend prefix `prod` in `versions.tf`).
   2. On pre-T1 `main`, run a full `terraform plan`. It **must show "No changes"**. If it doesn't, fix tfvars (`cutover`, `staging_basic_auth_hash`, `resend_dns_records`, …) until it does. This keeps a wrong var from deleting apex DNS or changing the new VM's metadata.
   3. Ali merges T1.
3. Maintenance window, on a `main` checkout that includes the merge. Ali approves each step, because this is prod.
   1. Pre-swap evidence: download the newest nightly `db/wac-*.dump` from `gs://wac-backups-wac-website-7bda80` to the scratchpad, write down its name, and count users with `pg_restore --data-only -t coderdojochi_cdcuser -f - <dump> | awk '/^COPY/{f=1;next} /^\\\./{f=0} f' | wc -l`. This needs no VM access or serial console.
   2. While prod is still up, run `terraform import google_compute_disk.web projects/wac-website-7bda80/zones/us-central1-a/disks/<disk>`, then `terraform plan -target=google_compute_disk.web`. It **must show "No changes"**. If it doesn't, fix the disk block in a follow-up PR and stop here. Nothing is down yet.
   3. `gcloud compute instances stop wac-web --zone us-central1-a`. Prod is down from here.
   4. Snapshot the stopped disk, so the copy is consistent: `gcloud compute disks snapshot <disk> --zone us-central1-a --storage-location us-central1 --snapshot-names wac-web-pre-iap-<date>`.
   5. `gcloud compute instances delete wac-web --zone us-central1-a --keep-disks=boot` (`--keep-disks` makes a separate `set-disk-auto-delete` unnecessary), then `gcloud compute disks describe <disk> --zone us-central1-a` to confirm the disk still exists, then `terraform state rm google_compute_instance.web`.
   6. `terraform plan`. Expect: create `google_compute_instance.web`, create `wac-ssh-iap` and `iap.googleapis.com`, update the Cloudflare AAAA records and `bootstrap`. **No change to `google_compute_disk.web`.** If you see anything else, stop and ask. Once Ali approves, `terraform apply`. DNS and the instance are created in the same apply, so downtime runs from step 3.3 until the boot in 3.7.
   7. Wait for the boot (`gcloud compute instances get-serial-port-output wac-web --zone us-central1-a` until `wac-provision: done`). `provision.sh` is idempotent and keeps the existing DB, `/var/lib/wac/infra-vm` and `/etc/wac`.
   8. `terraform plan` shows no changes.
   9. After the Proof passes and a day of normal running, run `gcloud compute snapshots delete wac-web-pre-iap-<date>` (back to $0).
4. Write the results and evidence into Progress.

Rollback (the original disk survives step 3.5):

- If the new instance fails: locally set `stack_type = "IPV6_ONLY"` (keep the disk resource and `boot_disk.source`), then `terraform apply`. That recreates the old network setup on the same disk, with metadata from Terraform.
- If the disk itself is damaged: `gcloud compute disks create wac-web-restore --source-snapshot wac-web-pre-iap-<date> --zone us-central1-a --type pd-standard`, then point `google_compute_disk.web` at it (`state rm` plus import) and apply.
- If both are lost: build a fresh VM and restore the dump with the TOC filter at `infra/vm/README.md:139-144`, then run `sudo wac-refresh-staging-db` and re-create `/etc/wac/reminders-enabled` if it was there.

## Proof

| Criterion | Test | One-line break that must fail it |
|---|---|---|
| 1 | `CLOUDSDK_ACTIVE_CONFIG_NAME=wac gcloud compute ssh wac-web --zone us-central1-a --tunnel-through-iap -- 'sudo -n true && hostname'` prints `wac-web` | Set `iap_ssh = false` in tfvars: the plan must show `wac-ssh-iap` being destroyed. Optionally, with Ali's OK, apply it and check that the ssh command times out, then apply `iap_ssh = true` and check that it works again |
| 2 | `curl -sI https://www.weallcode.org` returns 200; staging returns 401 without auth; over SSH, `sudo -u wac psql -d wac -tAc 'select count(*) from coderdojochi_cdcuser'` is **≥** the count from step 3.1 | n/a |
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

### Re-review (fresh sub-agent, 2026-11-26)

- It confirmed that the IAP/IPv6 design works, and that `provision.sh` is safe on a reused disk with a new NIC: nftables already blocks staging's IPv4 metadata access, Postgres has `listen_addresses = ''`, Caddy on 10.x is firewalled, and the watcher tolerates missing nonces. It also confirmed the disk config plans cleanly (`ignore_changes` covers the image URL, and `guest_os_features`, `licenses` and `architecture` are Optional+Computed).
- Blocker: the disk diff was first seen after prod was down. **Fixed:** step 3.2 runs the import plus `plan -target=google_compute_disk.web` while prod is up.
- Major: tfvars rebuilt from scratch could delete apex DNS or change metadata. **Fixed:** the step 2 gate requires a full plan on pre-T1 `main` to show "No changes" before the merge.
- Major: the snapshot was taken while the VM was running. **Fixed:** step 3.4 snapshots after the stop.
- Major: Proof 2 used `auth_user`, but the user table is `coderdojochi_cdcuser`, and the pre-swap count needed the serial console. **Fixed:** step 3.1 counts users from the nightly dump locally, and Proof 2 queries `coderdojochi_cdcuser`.
- Minor: T1 didn't remove `initialize_params`. **Fixed.**
- Minor: `vm.tf` refs were off. **Fixed** (41-105, 48-54).
- Minor: rollback went through the snapshot first. **Fixed:** the first option reuses the original disk.
- Minor: `instances stop` had no `--zone`. **Fixed.**
- Minor: the auto-delete step was redundant. **Removed**, because `--keep-disks=boot` covers it; there is now a check that the disk exists.
- Minor: Proof 1's break test was plan-only. **Fixed:** an optional live check of the timeout was added.
- Done 2026-11-26: `networkmanagement.googleapis.com` was disabled at Ali's request.

## Progress

Run 2026-11-26 (CST) by the lead session, with Ali's OK at each gated step.

- T0: `testIamPermissions` (REST; this gcloud has no `projects test-iam-permissions`) returned all three permissions. Boot disk `wac-web`: `pd-standard`, 30 GB, `debian-12-bookworm-v20261117`, `autoDelete=true`, tag `wac-web`.
- T1: a sub-agent wrote it, and the lead reviewed the diff. `fmt -check` and `validate` pass. It merged as WeAllCode/website#1662 (`76c83666`), with CI green.
- Gate (step 2): `terraform.tfvars` was derived from state serial 24 and kept in the scratchpad, never committed. The Cloudflare token is `op://homelab/Cloudflare weallcode Terraform/credential`.
  - The first full plan on pre-T1 `main` (`7e29406d`) wasn't "No changes". It showed 2 in-place updates from `infra/vm` changes on `main` that had never been applied (#1642, #1643, #1657): the `startup-script` metadata and `bootstrap.tgz`. There were no DNS, IAM or other diffs, so the tfvars were correct.
  - Ali chose to apply them separately first: an in-place metadata update with no reboot. After that, the plan showed "No changes".
- 3.1: the newest dump is `db/wac-20261126T093005.dump`, with 3639 `coderdojochi_cdcuser` rows.
- 3.2: the disk was imported, and `plan -target=google_compute_disk.web` showed "No changes".
- 3.3–3.4: the VM was stopped at 21:59 CST, when prod went down. Snapshot `wac-web-pre-iap-20261126` is READY (1.84 GB stored).
- 3.5: `instances delete --keep-disks=boot` ran, and disk `wac-web` stayed READY with no users. `state rm google_compute_instance.web` ran.
- 3.6: the plan was 3 to add (instance, `wac-ssh-iap`, `iap.googleapis.com`) and 5 to change (3 AAAA records, `bootstrap`, and the budget). The budget change came only from `data.google_project.this` being deferred, and the project number was the same. There was no change to the disk. It was applied at 22:08 CST, with 3 added and 4 changed. The new IPv6 is `2600:1900:4000:9c5b:0:1::`.
- 3.7: `wac-provision: done 2026-11-27T04:09:24Z`, with uv 0.13.9. Downtime was about 10 min (21:59–22:09 CST).
- 3.8: `terraform plan -detailed-exitcode` exited 0 ("No changes").
- Proof 1: IAP SSH ran `sudo -n true && hostname` and printed `wac-web`. Break test: the plan with `-var iap_ssh=false` destroys only `google_compute_firewall.ssh_iap[0]`. The live timeout check was not run.
- Proof 2: www returns `HTTP/2 200`, and staging returns 401. `coderdojochi_cdcuser` has 3640 rows, at least the dump's 3639.
- Proof 3: network `wac` has only `wac-https-cloudflare-ipv6` (tcp:443) and `wac-ssh-iap` (`35.235.240.0/20` tcp:22). The `default-*` rules are on the unused `default` network.
- Proof 4: "No changes". `fmt -check` and `validate` pass.
- Timers: `wac-deploy@prod`/`@staging` ran OK after boot (04:11 and 04:12 UTC). `wac-backup` and `wac-reminders` are scheduled.
- Pending: 3.9, deleting the snapshot after a day of normal running, with Ali's OK.

