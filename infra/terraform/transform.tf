# Strip the query string from logged-out GETs to the cached public pages, before
# the cache lookup, so `?utm_…`, `?fbclid=…` and per-recipient `?mc_eid=…` links
# all share one cache entry. Free can't ignore query strings in the cache key
# (Enterprise only), so this URL rewrite does it instead. None of these views
# read request.GET. The path list must match PUBLIC_CACHE_VIEW_NAMES in
# coderdojochi/middleware.py (weallcode/tests.py test_rewrite_paths_match_allowlist
# checks it). The `-avatar/` exclusion keeps the staff avatar actions under
# /mentors/<pk>/ out.
resource "cloudflare_ruleset" "transform" {
  zone_id = var.cloudflare_zone_id
  name    = "Transform rules"
  kind    = "zone"
  phase   = "http_request_transform"

  rules = [
    {
      ref         = "strip_query_public_html"
      description = "Drop the query string on logged-out public pages before the cache"
      action      = "rewrite"
      expression  = "(http.host in {\"${var.domain}\" \"www.${var.domain}\"}) and http.request.method in {\"GET\" \"HEAD\"} and http.request.uri.query ne \"\" and not (http.cookie contains \"sessionid=\") and not (http.cookie contains \"messages=\") and (http.request.uri.path in {\"/\" \"/our-story/\" \"/programs/\" \"/programs/summer-camps/\" \"/team/\" \"/join-us/associate-board/\" \"/privacy/\" \"/credits/\" \"/mentors/\"} or (starts_with(http.request.uri.path, \"/mentors/\") and not ends_with(http.request.uri.path, \"-avatar/\")))"
      action_parameters = {
        uri = {
          query = {
            value = ""
          }
        }
      }
    },
  ]
}
