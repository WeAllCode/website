# Block vulnerability-scanner probes at the edge (docs/plans/scanner-defense.md,
# Task C). The rules apply to all hosts (apex, www., gcp., staging.) on purpose:
# none of them serves PHP, dotfiles or other stacks. This uses 4 of the 5 custom
# rules on Free and leaves 1 spare. Free has no regex and lower() isn't
# confirmed for Free: `in` and starts_with/ends_with are case-sensitive, so names
# are written as scanners send them; Caddy's backstop catches other casings. Paths are already
# normalized by the URL sanitize phase. Kill switch: `enabled = false` on a rule,
# then apply (see README "WAF and rate limit").
resource "cloudflare_ruleset" "waf_custom" {
  zone_id = var.cloudflare_zone_id
  name    = "Custom rules"
  kind    = "zone"
  phase   = "http_request_firewall_custom"

  rules = [
    {
      ref         = "block_probe_extensions"
      description = "Block probe file extensions (php, env, backups, configs, keys, ...)"
      action      = "block"
      enabled     = true
      expression  = "(http.request.uri.path.extension in {\"env\" \"php\" \"php3\" \"php5\" \"phtml\" \"asp\" \"aspx\" \"asax\" \"asa\" \"axd\" \"jsp\" \"cgi\" \"sql\" \"bak\" \"backup\" \"old\" \"orig\" \"save\" \"swp\" \"tmp\" \"zip\" \"tar\" \"gz\" \"tgz\" \"rar\" \"7z\" \"log\" \"ini\" \"cnf\" \"conf\" \"config\" \"cfg\" \"pem\" \"key\" \"enc\" \"kv\" \"yml\" \"yaml\" \"toml\" \"properties\" \"gradle\" \"db\" \"sqlite\" \"tfstate\" \"tfvars\" \"hcl\" \"ovpn\" \"py\" \"rb\" \"lock\" \"inc\" \"json\" \"js\" \"map\" \"xml\" \"txt\" \"md\"}) and not (http.request.uri.path in {\"/robots.txt\" \"/sitemap.xml\"}) and not starts_with(http.request.uri.path, \"/.well-known/\")"
    },
    {
      ref         = "block_dotfiles"
      description = "Block dotfiles and dot-directories (.env, .git, .aws, ...) except /.well-known/"
      action      = "block"
      enabled     = true
      expression  = "(http.request.uri.path contains \"/.\") and not starts_with(http.request.uri.path, \"/.well-known/\")"
    },
    {
      ref         = "block_other_stacks"
      description = "Block paths of stacks we don't run (WordPress, phpMyAdmin, Spring, Laravel, Vite, ...)"
      action      = "block"
      enabled     = true
      expression  = "starts_with(http.request.uri.path, \"/wp-\") or (http.request.uri.path contains \"/wp-\") or starts_with(http.request.uri.path, \"/wordpress\") or starts_with(http.request.uri.path, \"/xmlrpc\") or starts_with(http.request.uri.path, \"/phpmyadmin\") or starts_with(http.request.uri.path, \"/pma/\") or (http.request.uri.path contains \"/actuator\") or starts_with(http.request.uri.path, \"/cgi-bin\") or starts_with(http.request.uri.path, \"/vendor/\") or starts_with(http.request.uri.path, \"/telescope\") or (http.request.uri.path contains \"/_profiler\") or starts_with(http.request.uri.path, \"/_ignition\") or starts_with(http.request.uri.path, \"/@fs/\") or starts_with(http.request.uri.path, \"/phpinfo\")"
    },
    {
      ref         = "block_probe_names"
      description = "Block editor backups (~) and exact probe names (Dockerfile, id_rsa, /metrics, /graphql, ...)"
      action      = "block"
      enabled     = true
      expression  = "ends_with(http.request.uri.path, \"~\") or (http.request.uri.path in {\"/Dockerfile\" \"/Makefile\" \"/Jenkinsfile\" \"/Procfile\" \"/Gemfile\" \"/Vagrantfile\" \"/Rakefile\" \"/Capfile\" \"/Gulpfile\" \"/brewfile\" \"/Pipfile\" \"/id_rsa\" \"/id_dsa\" \"/id_ecdsa\" \"/env\" \"/direnv\" \"/credentials\" \"/error_log\" \"/kubeconfig\" \"/OAI_CONFIG_LIST\" \"/passwd-s3fs\" \"/metrics\" \"/health\" \"/healthz\" \"/status\" \"/_status\" \"/info\" \"/_info\" \"/version\" \"/_version\" \"/oauth/token\" \"/v2/_catalog\" \"/api/config\" \"/api/v1/config\" \"/api/health\" \"/server-status\" \"/server-info\" \"/graphql\" \"/graphiql\" \"/horizon\" \"/_debugbar\"})"
    },
  ]
}

# One IP may send 60 requests per 10 s per Cloudflare data center (cf.colo.id is
# required by the API), then is blocked for 10 s (Free allows period 10 s and
# timeout 10 s). Cached hits count too. Free allows only path fields in the expression
# (no host, no response fields). /anymail/ is exempt so Resend's webhook bursts
# are never dropped. Before a load test, set `enabled = false` and apply first.
resource "cloudflare_ruleset" "ratelimit" {
  zone_id = var.cloudflare_zone_id
  name    = "Rate limit"
  kind    = "zone"
  phase   = "http_ratelimit"

  rules = [
    {
      ref         = "per_ip_60_per_10s"
      description = "Block an IP over 60 requests per 10 s per colo, except /anymail/ webhooks"
      action      = "block"
      enabled     = true
      expression  = "not starts_with(http.request.uri.path, \"/anymail/\")"
      ratelimit = {
        characteristics     = ["cf.colo.id", "ip.src"]
        period              = 10
        requests_per_period = 60
        mitigation_timeout  = 10
      }
    },
  ]
}
