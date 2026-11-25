# Cache logged-out HTML at the edge. The rule only makes responses eligible:
# with respect_origin, Cloudflare caches just what the origin marks
# `public, s-maxage=N` (coderdojochi/middleware.py, allowlisted views, no
# cookies). Everything else is `private` and passes through. The cookie and
# path exclusions below are belt-and-braces. Never use override_origin: it
# strips Set-Cookie and caches for at least 2 hours on Free.
resource "cloudflare_ruleset" "cache" {
  zone_id = var.cloudflare_zone_id
  name    = "Cache settings"
  kind    = "zone"
  phase   = "http_request_cache_settings"

  rules = [
    {
      ref         = "cache_public_html"
      description = "Cache logged-out public pages per origin Cache-Control"
      action      = "set_cache_settings"
      expression  = "(http.host in {\"${var.domain}\" \"www.${var.domain}\"}) and not (http.cookie contains \"sessionid=\") and not (http.cookie contains \"messages=\") and not starts_with(http.request.uri.path, \"/admin/\") and not starts_with(http.request.uri.path, \"/dj-admin/\") and not starts_with(http.request.uri.path, \"/account/\")"
      action_parameters = {
        cache = true
        edge_ttl = {
          mode = "respect_origin"
        }
        browser_ttl = {
          mode = "respect_origin"
        }
      }
    },
  ]
}
