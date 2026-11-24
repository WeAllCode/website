# $1 budget: alerts at any spend (1%), 50% and 100%, emailed to billing admins.
resource "google_billing_budget" "project" {
  billing_account = var.billing_account_id
  display_name    = "wac-website $1"

  budget_filter {
    projects = ["projects/${data.google_project.this.number}"]
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = "1"
    }
  }

  threshold_rules {
    threshold_percent = 0.01
  }
  threshold_rules {
    threshold_percent = 0.5
  }
  threshold_rules {
    threshold_percent = 1.0
  }

  # No all_updates_rule: without one, threshold emails go to billing admins
  # (the provider requires a Pub/Sub topic or channel if the block is present).

  depends_on = [google_project_service.apis]
}
