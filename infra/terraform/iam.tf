# Project owners. daniel.m.conrad@gmail.com is invited by hand in the console
# (gmail.com Owners need an accepted email invite; setIamPolicy refuses them).
# After he accepts, add "user:daniel.m.conrad@gmail.com" to project_owners in
# terraform.tfvars and import the binding (R2, Task F):
#   terraform import 'google_project_iam_member.owners["user:daniel.m.conrad@gmail.com"]' \
#     "<project_id> roles/owner user:daniel.m.conrad@gmail.com"
resource "google_project_iam_member" "owners" {
  for_each = toset(var.project_owners)

  project = var.project_id
  role    = "roles/owner"
  member  = each.value

  depends_on = [google_project_service.apis]
}

# R3: orgs created on/after 2024-05-03 enforce domain-restricted sharing, which
# blocks allUsers on the media buckets and the gmail owner. Only when 0b found it
# enforced, set allow_all_member_domains = true (needs Org Policy Admin).
resource "google_org_policy_policy" "allow_all_member_domains" {
  count = var.allow_all_member_domains ? 1 : 0

  name   = "projects/${var.project_id}/policies/iam.allowedPolicyMemberDomains"
  parent = "projects/${var.project_id}"

  spec {
    rules {
      allow_all = "TRUE"
    }
  }

  depends_on = [google_project_service.apis]
}
