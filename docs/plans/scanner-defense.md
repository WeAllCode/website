# Block vulnerability-scanner bursts

## Goal and done

As the We All Code admin, I want scanners that probe for secrets and backups (`/.env`, `/.git/config`, `/backup.zip`, `/wp-login.php` …) to be stopped at Cloudflare, or answered with a tiny 404 by Caddy, before they reach Django. A single client should also be held below what the e2-micro can serve. The result: a burst can't slow the site or fill Sentry Logs, and real users, sign-in, webhooks and monitors work exactly as today.

Why (investigated 2026-11-25 in Sentry Logs, we-all-code-p5 / production, and in Cloudflare Security → Analytics):

- **The burst Ali saw.** It was 666 GETs in 14 s (03:42:15–03:42:29 UTC), about 47 req/s. Each request wrote two log lines (the gunicorn access line and the `django.request` "Not Found:" warning), which is why Sentry showed ~1.3K. It hit 333 unique paths, each twice, and every one was a 404 of 74 KB (the full Django 404 page). There were no 200s.
  - The scanner's user agent was exactly `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36`, with no `Chrome/` token.
  - Its only 200s, in a later run, were `/robots.txt` and `/sitemap.xml`.
- **What it was after: credentials.**
  - `.env` variants (~85)
  - cloud and AI-tool credential files: `.aws`, `.config/gcloud`, `.azure`, `.claude`, `.cursor`, `.codex`, `.huggingface`
  - `.git/*`
  - CI and IaC files (`terraform.tfstate`, workflows)
  - SQL dumps and site archives (`weallcode.org.zip`, `backup.tar` …)
  - It tried 545 unique paths across all its runs. The fixture for this plan, [scanner-probe-paths-2026-11-25.txt](scanner-probe-paths-2026-11-25.txt), holds 543 of them: the two `/.well-known/` paths are left out because `/.well-known/` is never blocked.
- **Source.**
  - Gunicorn sits on a unix socket, so the access log has `-` where the IP should be.
  - Cloudflare's 24 h top source IPs show 35.233.37.230 (Google Cloud) with 1.34K requests. That matches the scanner's ~1,312 requests, but it was not confirmed with a filter.
  - A second credential scan was running at 17:53 UTC from 35.240.20.93, also Google Cloud.
  - Scanners rotate cloud IPs, so this plan uses **no IP or ASN rules**. Never block Google Cloud's ASN: the Sentry uptime checker and other legitimate services run there.
- **It recurs.**
  - The same user agent came back at 07:54–07:55 (646 requests), 10:32 and 13:34.
  - Other scanners in the same ~18 h:
    - a WordPress webshell sweep at 00:48 (364 requests)
    - empty-UA PHP shell probes at 04:29, 04:57 and 10:38
    - a curl "reconx" scan at 13:34
    - a `.git/config` / `.env` scan at 15:15 (129 requests)
- **Totals.** Since logs began, 2,653 of 5,108 origin requests (52%) were 404s, and 99.96% of those were the 74 KB page.
  - Pattern counts: `.php` 851, `.env` 444, `wp-`/`xmlrpc` 277, archives and dumps 139, `.git` 106, actuator/phpinfo 59.
  - SQLi and path-traversal strings: 0.
  - POST floods: none. There were 11 POSTs in total: 9 to `/join-us/` (200, spread over the day) and 2 to `/xmlrpc.php`.
- **It did not slow the site.**
  - Origin transaction p95 was 40 ms during the 03:42 burst and 38 ms during 07:54, against a 187–219 ms baseline. The 404 render is cheap: 18–40 ms.
  - Sentry uptime checks at 03:40 and 03:45, and at 07:50 and 07:55, all passed (266–520 ms).
  - The 11 "Worker was sent SIGTERM" events don't line up with the bursts.
  - The real risk is a scanner or flood hitting *uncached real pages* at 47 req/s: the VM serves about 12 req/s uncached (load test, `docs/plans/cloudflare-html-cache.md`). That is why the per-IP rate limit is the availability control, and the path blocks are mainly there to remove noise and probes.
- **Data window.** Sentry Logs started at the cutover, 2026-11-24 23:58 UTC (#1623), so "the last 7 days" is really about 18 hours.
- **Sentry quota is fine.**
  - In 2 days: 8,926 log items and 29.6 MB, which is about 0.45 GB a month against the Developer plan's 5 GB.
  - 17 error events.
  - No "Page not found!" issues, because `weallcode/urls.py:71` `handler404` is dead code (see Pitfalls).
- **Cloudflare as it is now.**
  - The zone is on Free.
  - Rulesets: the Cloudflare-managed ones (normalization, the Free Managed Ruleset, DDoS L7) plus our `Cache settings`. There is no custom-rules or rate-limit entry point visible.
  - security_level is `medium` and browser_check is `on`.
  - 50 requests in 24 h were already mitigated by Cloudflare.
  - The Terraform token returns `request is not authorized` for the `http_request_firewall_custom`, `http_ratelimit` and `http_request_firewall_managed` phases, and has no analytics permission.

Acceptance criteria:

1. AC1: every path in the fixture file (543), requested through Cloudflare, returns either `403` from Cloudflare or Caddy's short `404` (body `Not Found`, under 100 bytes). Thresholds:
   - None returns `200`.
   - At most 2% (10 paths) reach Django's 74 KB 404. The known tail is `/api/v1/namespaces/default/secrets` and `/api/graphql`.
   - At least 90% are `403` at the edge.
2. AC2: none of these return `403` or `429`. Each gets its status from today:
   - `/`, `/programs/`, `/team/`, `/mentors/`, `/privacy/`, `/join-us/`, `/classes/476/`
   - `/account/login/`, `/account/google/login/`, `/account/google/login/callback/`, `/dj-admin/`
   - `/anymail/resend/tracking/` (Resend webhook; GET is 4xx-not-403 today, record the exact code first)
   - `/robots.txt` and `/sitemap.xml` (200)
   - `/.well-known/security.txt` (Django 404)
   - The Sentry uptime monitor and UptimeRobot stay green for 24 h afterwards.
3. AC3: from one IP, more than 60 requests within 10 s get `429`. About 20 s later the same IP gets `200` again.
4. AC4: a real broken link (`/careers/`) still renders the full Django 404 page.
5. AC5: in the 24 h after rollout, Sentry Logs shows no fixture path reaching Django, and Cloudflare Security → Events shows the blocks.
6. AC6: gunicorn access lines in Sentry Logs start with the client IP (from `CF-Connecting-IP`), not `-`.
7. AC7: `terraform plan` shows "No changes", and CI passes.

Out of scope:
- Bot Fight Mode. It can't be skipped by WAF rules on Free, so it can't exempt `/anymail/` webhooks or monitors. Leave it off. See Decisions.
- IP and ASN blocks.
- A lighter Django 404 template. Caddy and the edge keep probes out of Django, so the remaining 404s are real and should keep the full page.
- Sentry `before_send_log` filtering: the quota is at ~9% of the limit. Revisit if Sentry Logs usage passes 50%.
- Deleting the dead `handler404` (a follow-up).

## Decisions (made 2026-11-25)

- Rate limit: **60 requests per 10 s per IP** (Ali). This is below the VM's ~120 uncached requests per 10 s. It catches the 03:42 burst (~470/10 s) and the 07:54 one (~67/10 s), and leaves room for a classroom behind one NAT. Prod static and media are served from `storage.googleapis.com`, so a page view is about one request to weallcode.org. **Ali's own load tests from one IP will trip it**: set the rule's `enabled = false` and apply before a load test.
- Bot Fight Mode stays off. Per the Cloudflare docs, it "cannot bypass or skip Bot Fight Mode using WAF custom rules", it may challenge API traffic, and it covers the whole domain.
- The Free Managed Ruleset is deployed by default on Free. Don't add a Terraform resource for `http_request_firewall_managed`.
- Blocks return Cloudflare's default 403 page. Custom block responses need Pro.

## Read first

Code:

- `infra/terraform/cache.tf:1-30`: the existing `cloudflare_ruleset` to copy (v5 `rules = [ { … } ]` list syntax, `name` required, `zone_id = var.cloudflare_zone_id`, `${var.domain}`).
- `infra/terraform/variables.tf:11-20`: `cloudflare_zone_id` and `domain`. `infra/terraform/versions.tf`: provider `cloudflare/cloudflare ~> 5.29`.
- `infra/terraform/README.md:77-102`: "Switches" and "Edge cache". Add a "WAF and rate limit" section in the same style.
- `infra/vm/Caddyfile:1-45`:
  - `(wac_common)` and `(wac_proxy)` are the snippet pattern.
  - There are two site blocks: prod plus `gcp.`, and staging. Staging's `basic_auth` runs before `respond`, so probes there get 401 anyway.
- `infra/vm/deploy-pull.sh:212-232`: **infra files (Caddyfile, systemd units) install only on `--target prod` releases.** A staging release never changes Caddy or the units. So the Caddy change is proven locally (Task A's script), then in prod.
- `infra/vm/provision.sh:105-146`: how the Caddyfile is validated (`caddy validate` from `/etc/caddy`) and installed, and how units are installed and restarted. Check how unit changes trigger a restart before changing `wac-web.service`.
- Monitors:
  - The Sentry uptime monitor 11059890 runs `GET https://www.weallcode.org/` every 5 min (`docs/plans/heroku-to-gcp-e2micro.md` H6b).
  - UptimeRobot sends `HEAD /` (seen in the access logs as `"HEAD / HTTP/1.1" 200 … UptimeRobot/2.0`). Its config isn't in the repo, so confirm in the UptimeRobot dashboard that it checks only `/`, and record that in Progress.
  - Both are in the must-pass list.
- `infra/vm/wac-web.service:16` and `infra/vm/wac-staging.service:22`: the gunicorn `ExecStart` with `--access-logfile -`.
- `coderdojochi/settings.py:340-359`: `sentry_sdk.init` with `enable_logs=True`, `send_default_pii=True`. The gunicorn access log reaches Sentry Logs because of `--preload`.
- `coderdojochi/urls.py:32-37, 297-310`: root URLconf. `account/` includes `accounts.urls` then `allauth.urls` (Google login is `/account/google/login/` and `/account/google/login/callback/`). `robots.txt` is at line 300, `anymail/` at 310. `weallcode/urls.py:54`: `sitemap.xml`. These two are the **only** routes with a file extension.
- `coderdojochi/settings.py:255-285`: in prod, `STATIC_URL` and `MEDIA_URL` are on `storage.googleapis.com`, so weallcode.org serves no `/static/` or `/media/`.
- `.github/workflows/ci.yml:144-165`: the `infra` job runs `terraform fmt -check -recursive`, `terraform validate` and `shellcheck infra/vm/*.sh infra/vm/wac-manage`. Nothing validates the Caddyfile in CI, so Task A adds a script that shellcheck covers.
- `docs/plans/heroku-to-gcp-e2micro.md` Progress: how to run Terraform:
  - GCS backend `wac-tfstate-wac-website-7bda80`
  - `CLOUDSDK_ACTIVE_CONFIG_NAME=wac`
  - `GOOGLE_OAUTH_ACCESS_TOKEN=$(gcloud auth print-access-token --account ali@weallcode.org)`
  - `CLOUDFLARE_API_TOKEN` from `op://homelab/Cloudflare weallcode Terraform/credential`
  - run with the sandbox disabled
  - `terraform.tfvars` is gitignored: copy it from `../cf-html-cache-run-5e71d0/infra/terraform/`.

  It also covers `infra/vm/release.sh --target staging|prod`.
- `docs/plans/cloudflare-html-cache.md` Progress, Checkpoint 2: how the cache-rule spike was run and recorded. Copy that style.

Docs (checked 2026-11-25):

- https://developers.cloudflare.com/waf/custom-rules/ (Availability): Free has 5 custom rules. Every action except Log is available. No regex.
- https://developers.cloudflare.com/ruleset-engine/rules-language/operators/: `matches` needs Business or Enterprise, so don't use it. `contains`, `in {}` and `wildcard` have no plan restriction.
- https://developers.cloudflare.com/ruleset-engine/rules-language/fields/reference/http.request.uri.path.extension/: lowercased text after the last dot. `/foo.tar.gz` → `gz`, `/.mp3` → `""`. **So dotfiles like `/.env` are not caught by extension**; rule 2 handles them. The docs don't say whether the field is available on Free: Checkpoint 2 step 2 proves it.
- https://developers.cloudflare.com/ruleset-engine/rules-language/expressions/: max 4,096 characters per expression.
- https://developers.cloudflare.com/waf/rate-limiting-rules/ (Availability) and https://developers.cloudflare.com/waf/rate-limiting-rules/parameters/: Free has 1 rule, IP characteristic, period 10 s and mitigation timeout 10 s.
  - No counting expression, so you can't count only 404s.
  - The rule expression may use **only path and verified-bot fields**, not host.
  - Characteristics must include `cf.colo.id` in API and Terraform: `["cf.colo.id", "ip.src"]`. Counters are per data center.
- https://developers.cloudflare.com/bots/get-started/bot-fight-mode/ (Considerations): can't be skipped by custom rules; may challenge API traffic.
- https://developers.cloudflare.com/waf/get-started/: the Free Managed Ruleset is deployed by default.
- https://developers.cloudflare.com/terraform/additional-configurations/waf-custom-rules/, https://developers.cloudflare.com/terraform/additional-configurations/rate-limiting-rules/ and https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/ruleset: HCL shape. Import ID `zones/<zone_id>/<ruleset_id>`.
- https://developers.cloudflare.com/fundamentals/api/reference/permissions/: token permissions "Zone WAF: Edit" (custom and rate-limit rules) and "Analytics: Read".
- https://caddyserver.com/docs/caddyfile/matchers (`path_regexp`, RE2: **no lookahead**), https://caddyserver.com/docs/caddyfile/directives (`respond` is ordered before `reverse_proxy`), https://caddyserver.com/docs/caddyfile/concepts#snippets (named matchers inside a snippet work when the snippet is imported into a site block).
- https://docs.gunicorn.org/en/stable/settings.html#access-log-format: `%({header}i)s` logs a request header. The default format is `%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"`.
- https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html (Specifiers): a literal `%` in a unit file must be written `%%`.

## Tasks

### Task A: Caddy probe block (Checkpoint 1)

Owns: `infra/vm/Caddyfile`, new `infra/vm/test-caddy-probes.sh`, new `docs/plans/scanner-must-pass-paths.txt`.

1. In `Caddyfile`, add a snippet between marker comments `# BEGIN wac_probes` and `# END wac_probes`:
   ```
   (wac_probes) {
   	@probe {
   		path_regexp probe (?i)(/\.|~$|\.(env|php\d?|phtml|asp|aspx|asax|asa|axd|jsp|cgi|sql|bak|backup|old|orig|save|swp|tmp|zip|tar|gz|tgz|rar|7z|log|ini|cnf|conf|config|cfg|pem|key|enc|kv|ya?ml|toml|properties|gradle|db|sqlite|tfstate|tfvars|hcl|ovpn|py|rb|lock|inc|json|js|map|xml|txt|md)$|^/(wp-|wordpress|xmlrpc|phpmyadmin|pma/|cgi-bin|vendor/|telescope|_ignition|_debugbar|@fs/|phpinfo|server-status|server-info|graphi?ql|horizon)|/actuator|/_profiler|/wp-|^/(dockerfile|makefile|jenkinsfile|procfile|gemfile|vagrantfile|rakefile|capfile|gulpfile|brewfile|pipfile|id_[rd]sa|id_ecdsa|env|direnv|credentials|error_log|kubeconfig|oai_config_list|passwd-s3fs|metrics|healthz?|_?status|_?info|_?version|oauth/token|v2/_catalog|api/(v1/)?config|api/health)/?$)
   		not path /.well-known/* /robots.txt /sitemap.xml
   	}
   	header @probe Cache-Control "private"
   	respond @probe "Not Found" 404
   }
   ```
   Add `import wac_probes` in both site blocks, after `import wac_common`, so prod, `gcp.` and staging all get it. Add a comment saying why: the Cloudflare rules are the first line, and this catches what their no-regex expressions can't, plus anything that reaches the origin if a rule is disabled. The `Cache-Control: private` keeps the cache-plan invariant that only the Django middleware marks anything public.
2. `docs/plans/scanner-must-pass-paths.txt`: one path per line, each with its expected status. Use the AC2 list plus `/careers/` (404, the full page), `/our-story/` and `/programs/summer-camps/`. Before writing each expected status, record it from prod today with `curl -s -o /dev/null -w '%{http_code}'`.
3. `infra/vm/test-caddy-probes.sh` (bash, `set -euo pipefail`, must pass shellcheck):
   - Extract the snippet between the markers from `infra/vm/Caddyfile` (awk or sed inside the script is fine).
   - Write a temporary Caddyfile with that snippet and a test site. Caddyfile has no `;` separator, so put each directive on its own line:
     ```
     {
     	admin off
     }
     (snippet here)
     http://127.0.0.1:{port} {
     	import wac_probes
     	respond "app" 200
     }
     ```
     Run `caddy run` in the background with a trap that kills it.
   - Skip `#` lines and blank lines in both path files. Use `curl -g`, because the fixture has `/*.sql`.
   - For every fixture path, expect status 404 with body `Not Found`, and count the misses (paths answered `app`).
   - For every must-pass path, expect body `app`.
   - Print `blocked N/543, fell through M` and list both the fall-throughs and the must-pass failures.
   - Exit non-zero if any must-pass path is blocked or if fewer than 98% of fixture paths are blocked.
   - Review simulation (Python `re`, 2026-11-25): 541/543 blocked. The two misses are `/api/v1/namespaces/default/secrets` and `/api/graphql`. No real route matched.
4. Check that no real route is caught. List every URL pattern with `uv run python -c` over `django.urls.get_resolver()` (prefixes from `coderdojochi.urls`) and test each literal prefix against the regex. The only expected hits are none. `/robots.txt` and `/sitemap.xml` are excluded by `not path`.

Pitfalls:
- RE2 has no lookahead, which is why `.well-known` is excluded with `not path`, not in the regex.
- `(?i)` is needed: probes use `/.git/HEAD`, `/Dockerfile`, `/OAI_CONFIG_LIST` and `appsettings.Production.json`, and the exact-name list is written in lowercase.
- The exact-name group (`/metrics`, `/health`, `/status`, `/version` …) is safe only because no Django route uses those names, and both monitors check `/` (see the Monitors note in Read first). Step 4 proves the first part.
- `respond` sorts before `reverse_proxy`, so the probe never reaches gunicorn.
- Don't add `/static/` or `/media/` exceptions. Prod serves neither from this host.
- Matching `.js`, `.json`, `.xml`, `.txt` and `.md` is safe only because no Django route has those extensions except `robots.txt` and `sitemap.xml`. Step 4 proves it.
- `caddy validate` of the real Caddyfile needs `/etc/caddy/origin.pem` and the staging auth import, so it can't run locally. That's why the test uses an extracted snippet. Prod validation happens in `provision.sh` on release.

Proof: `bash infra/vm/test-caddy-probes.sh` passes (Caddy is at `/opt/homebrew/bin/caddy`). `shellcheck infra/vm/*.sh` passes.

### Task B: client IP in the gunicorn access log (Checkpoint 1, in parallel with Task A)

Owns: `infra/vm/wac-web.service`, `infra/vm/wac-staging.service`.

1. Add `--access-logformat` to both `ExecStart` lines. Use the gunicorn default with `%(h)s` replaced by the Cloudflare client IP header. In a systemd unit every `%` is doubled:
   ```
   --access-logformat '%%({cf-connecting-ip}i)s %%(l)s %%(u)s %%(t)s "%%(r)s" %%(s)s %%(b)s "%%(f)s" "%%(a)s"'
   ```
2. Check that systemd parses it with `systemd-analyze verify`. macOS has no systemd, so run it in a Linux container: `docker run --rm -v "$PWD/infra/vm:/u:ro" debian:12 bash -c 'apt-get -qq update >/dev/null && apt-get -qq install -y systemd >/dev/null && systemd-analyze verify /u/wac-web.service'` (missing-path warnings are fine; specifier or quoting errors are not).
3. Read `provision.sh` to see whether a changed unit triggers `daemon-reload` and a restart of `wac-web`. If it doesn't, write the manual step into Checkpoint 1 before the prod release.

Pitfalls:
- A single `%` is a systemd specifier: `%(h)` would fail or expand wrongly.
- Only the access-log format changes. Sentry already receives the user IP via `send_default_pii=True`, so this adds no new kind of data.
- Staging units only install on prod releases (deploy-pull.sh:212-232). Both files change together.
- `deploy-pull.sh` runs `daemon-reload` and restarts only the target's service. So `wac-staging` keeps the old log format until its next staging deploy. That's fine, because AC6 is prod-only.

Proof: `systemd-analyze verify` shows no specifier errors for either unit. After the prod release, AC6 holds.

### Task C: Cloudflare WAF custom rules and rate limit (Checkpoint 2)

Owns: new `infra/terraform/waf.tf`, and `infra/terraform/README.md` (one new section, "WAF and rate limit").

It waits for Checkpoint 0 (the token) and Checkpoint 1 (the origin backstop is live, so a rule that is too narrow still ends in a small 404).

1. `waf.tf`, resource `cloudflare_ruleset` "waf_custom": `name = "Custom rules"`, `kind = "zone"`, `phase = "http_request_firewall_custom"`. Three rules, all `action = "block"`, each with a `ref` and a `description`:
   - `ref = "block_probe_extensions"`: `(http.request.uri.path.extension in {"env" "php" "php3" "php5" "phtml" "asp" "aspx" "asax" "asa" "axd" "jsp" "cgi" "sql" "bak" "backup" "old" "orig" "save" "swp" "tmp" "zip" "tar" "gz" "tgz" "rar" "7z" "log" "ini" "cnf" "conf" "config" "cfg" "pem" "key" "enc" "kv" "yml" "yaml" "toml" "properties" "gradle" "db" "sqlite" "tfstate" "tfvars" "hcl" "ovpn" "py" "rb" "lock" "inc" "json" "js" "map" "xml" "txt" "md"}) and not (http.request.uri.path in {"/robots.txt" "/sitemap.xml"}) and not starts_with(http.request.uri.path, "/.well-known/")`
   - `ref = "block_dotfiles"`: `(http.request.uri.path contains "/.") and not starts_with(http.request.uri.path, "/.well-known/")`
   - `ref = "block_other_stacks"`: `starts_with(http.request.uri.path, "/wp-") or (http.request.uri.path contains "/wp-") or starts_with(http.request.uri.path, "/wordpress") or starts_with(http.request.uri.path, "/xmlrpc") or starts_with(http.request.uri.path, "/phpmyadmin") or starts_with(http.request.uri.path, "/pma/") or (http.request.uri.path contains "/actuator") or starts_with(http.request.uri.path, "/cgi-bin") or starts_with(http.request.uri.path, "/vendor/") or starts_with(http.request.uri.path, "/telescope") or (http.request.uri.path contains "/_profiler") or starts_with(http.request.uri.path, "/_ignition") or starts_with(http.request.uri.path, "/@fs/") or starts_with(http.request.uri.path, "/phpinfo")`
   - `ref = "block_probe_names"`: `ends_with(http.request.uri.path, "~") or (http.request.uri.path in {"/Dockerfile" "/Makefile" "/Jenkinsfile" "/Procfile" "/Gemfile" "/Vagrantfile" "/Rakefile" "/Capfile" "/Gulpfile" "/brewfile" "/Pipfile" "/id_rsa" "/id_dsa" "/id_ecdsa" "/env" "/direnv" "/credentials" "/error_log" "/kubeconfig" "/OAI_CONFIG_LIST" "/passwd-s3fs" "/metrics" "/health" "/healthz" "/status" "/_status" "/info" "/_info" "/version" "/_version" "/oauth/token" "/v2/_catalog" "/api/config" "/api/v1/config" "/api/health" "/server-status" "/server-info" "/graphql" "/graphiql" "/horizon" "/_debugbar"})`. `in` is case-sensitive, so the names are written as the scanners send them; Caddy catches other casings.
   - The rules apply to all hosts (`www.`, apex, `gcp.`, `staging.`) on purpose. This uses 4 of the 5 Free custom rules and leaves 1 spare. Write that in a comment.
   - Simulated against the fixture before the review added rule 4 and the extra extensions: 90.5% blocked. Task D's run in Checkpoint 2 gives the real number.
2. Same file, resource `cloudflare_ruleset` "ratelimit": `name = "Rate limit"`, `kind = "zone"`, `phase = "http_ratelimit"`. One rule:
   - `ref = "per_ip_60_per_10s"`, `action = "block"`
   - `expression = "not starts_with(http.request.uri.path, \"/anymail/\")"` (path fields only on Free; webhooks are exempt)
   - `ratelimit = { characteristics = ["cf.colo.id", "ip.src"], period = 10, requests_per_period = 60, mitigation_timeout = 10 }`
3. `README.md` "WAF and rate limit":
   - what each rule blocks
   - the 60/10 s limit and why
   - the kill switch: `enabled = false` on a rule, then apply. Or delete it in the dashboard, but then `terraform plan` shows drift; re-apply or re-import.
   - how to load test: disable the rate-limit rule first
   - where blocks show: Security → Events
   - Bot Fight Mode is off on purpose
   - never add IP or ASN blocks for cloud ranges

Copy: `infra/terraform/cache.tf` for the HCL shape and the escaped quotes.

Pitfalls:
- **One entry-point ruleset per phase per zone.** Checkpoint 0 checks the entry points. If either phase already has one, `terraform import` it and keep its rules.
- Don't use `matches`, `lower()` or the dashboard's regex builder. Regex isn't on Free, and `lower()` isn't confirmed for Free. Paths are already normalized by the sanitize phase.
- Rate-limit `characteristics` must include `cf.colo.id`, or the API rejects the rule.
- Never put host or response fields in the rate-limit expression (not allowed on Free).
- `terraform apply` needs Ali's OK.

Proof: `terraform fmt -check -recursive infra/terraform`, `terraform -chdir=infra/terraform validate`, then `terraform plan` shows exactly 2 to add (or in-place updates if imported) and nothing else. If there is unrelated drift, stop and ask Ali.

### Task D: edge check script (Checkpoint 2, in parallel with Task C)

Owns: new `infra/vm/check-edge-blocks.sh`.

A bash script (it must pass shellcheck) that takes a base URL, for example `https://www.weallcode.org`, and:
- requests every fixture path at about 4 req/s (`sleep 0.25`, safely under the 60/10 s limit), and tallies `403`, Caddy `404` (body `Not Found`), the Django 404 (body over 10 KB), `200` and other codes
- requests every must-pass path and compares the result to the expected status
- exits non-zero if any fixture path returns `200`, if more than 2% reach the Django 404, if fewer than the `--min-edge` percentage are `403` (default 90; Checkpoint 1 passes `--min-edge 0`), or if any must-pass path differs

Use `curl -g -s -o "$tmp" -w '%{http_code} %{size_download}'` and a normal browser user agent. Skip `#` and blank lines. Read the paths only from the two plan files.

Proof: `shellcheck infra/vm/check-edge-blocks.sh` passes. Run it against prod with `--min-edge 0` before Task C's apply: about 99% are Caddy `404` (after Checkpoint 1), at most 2% are Django 404, and the must-pass list passes. That is the baseline.

## Checkpoints

**Checkpoint 0: token (Ali).**

1. Ali adds "Zone → Zone WAF: Edit" and "Zone → Analytics: Read" to the token "weallcode Terraform" (My Profile → API Tokens → Edit; the `cf` CLI can't edit tokens, see the cache plan's Progress).
2. Runner, read-only: for each of `http_request_firewall_custom` and `http_ratelimit`, `GET /zones/<zone_id>/rulesets/phases/<phase>/entrypoint`. Expect "could not find entrypoint ruleset". Otherwise record the ruleset id and rules in Progress; Task C imports them.
3. Runner: with Analytics Read, query GraphQL `httpRequestsAdaptiveGroups` for 2026-11-25 03:42–03:43, `edgeResponseStatus: 404`, grouped by `clientIP`, `clientCountryName` and `userAgent` (`clientAsn` is not on Free). Record the scanner's IP in Progress, closing the open question in Why. Use the Terraform token with curl, never the dashboard session. Do this first, because GraphQL retention on Free is short. If the window is past retention, record "unavailable" and move on.

**Checkpoint 1: origin backstop live.** Tasks A and B run in parallel, with separate files.

Check:
1. `bash infra/vm/test-caddy-probes.sh` passes, and `shellcheck infra/vm/*.sh` passes. Run the mutation (see Proof).
2. Units verify (Task B).
3. Open the PR. CI passes.
4. With Ali's OK, merge, then `release.sh --target prod` (also with Ali's OK). Infra files install only on prod releases; the release runs `caddy validate` before installing.
5. On prod:
   - `curl -s https://www.weallcode.org/.env` → `404 Not Found`, 9 bytes.
   - `/careers/` → the full Django 404.
   - `bash infra/vm/check-edge-blocks.sh --min-edge 0 https://www.weallcode.org` passes: the must-pass list is unchanged, about 99% of the fixture is Caddy 404, and at most 2% is Django 404.
   - A fresh access line in Sentry Logs starts with an IP (AC6).

Delivers: probes no longer reach Django. The investigation data now has client IPs.

**Checkpoint 2: Cloudflare rules live.** Tasks C and D run in parallel, with separate files.

Check:
1. `fmt -check`, `validate` and `plan` (Task C Proof).
2. **Spike first.** With Ali's OK, apply only `cloudflare_ruleset.waf_custom` (`-target`), with each rule's expression ANDed with `(http.request.uri.path in {"/.env.spike" "/spike.php" "/wp-spike"})`, so only those three paths can match. Then:
   - `curl -sI https://www.weallcode.org/spike.php` → 403. This proves `http.request.uri.path.extension` works on Free.
   - `/.env.spike` → 403, and `/wp-spike` → 403.
   - `/` → 200.
   - If the extension field is rejected at apply or doesn't match, rewrite rule 1 as `ends_with(http.request.uri.path, ".php") or …` chunks under 4,096 characters. Write that into the plan first.
3. Restore the full expressions and apply `waf_custom` (Ali's OK). Run `bash infra/vm/check-edge-blocks.sh https://www.weallcode.org` (AC1, AC2). If any must-pass path is 403, set that rule's `enabled = false`, apply, and record it.
4. Apply `cloudflare_ruleset.ratelimit` (Ali's OK). AC3: `seq 200 | xargs -P20 -I{} curl -s -o /dev/null -w '%{http_code}\n' 'https://www.weallcode.org/privacy/?rl={}' | sort | uniq -c` shows some `429`s. The parallel run makes sure more than 60 land within 10 s; the query string avoids nothing (rate limits count cached hits too) but makes the requests distinct in logs. `sleep 20`, then one request → 200. Run it from Ali's machine only, and tell other running sessions first (it blocks that IP for 10 s).
5. `terraform plan` → "No changes" (AC7).

Delivers: probes stopped at the edge, and one IP held under the VM's capacity.

**Checkpoint 3: watch for 24 h, then wrap up.**

Check:
1. 24 h after Checkpoint 2:
   - Sentry Logs: count `Not Found:` lines and 404 access lines, and compare them with the 2,653 in the ~18 h before (AC5).
   - List any fixture-like path that still reached Django.
   - Cloudflare Security → Events: blocked counts per rule.
   - Sentry uptime monitor 11059890 and UptimeRobot: no failures (AC2).
2. Check that the 9 or so daily `/join-us/` POSTs still arrive (form submissions in Sentry Logs, or the staff inbox, per Ali).
3. Record the numbers in Progress.

## How to run it

- Read the whole plan before you start. Run it as the lead: you write no code.
- At the start of each checkpoint, give every task that can run in parallel to its own sub-agent, all at once. Each brief names:
  - its task and its files, and only those
  - the bar to meet: the task's Proof command
  - the report format: files changed, commands run with pass/fail, and anything that deviated from the plan
  - that it must not run git
- You alone run the checkpoint's check, commit (one commit per checkpoint), and write the result and evidence into Progress.
- If something comes up that isn't in the plan, write it into the plan before anyone builds it.
- Ask Ali before:
  - merging
  - any `release.sh --target prod`
  - any `terraform apply`, spike included
  - running the rate-limit test
- Never block by IP or ASN. Never enable Bot Fight Mode.
- Never repeat secret values in chat or files. Bash tool calls have no description and no comments. Ali's interactive shells are fish. Use only the ali@weallcode.org Google account.
- After each checkpoint, if your context window is half full, write which checkpoint is next into Progress and stop; a fresh session continues from this plan.

## Proof

| AC | Test or check | Change that should make it fail |
|---|---|---|
| AC1 | `test-caddy-probes.sh` (origin, ≥98% blocked); `check-edge-blocks.sh` on prod (edge, ≥90% `403`, none `200`, ≤2% Django 404) | delete the `/\.|` alternative from `path_regexp`: the `.git`/`.aws`/`.env` paths fall through and the script drops below 98% |
| AC2 | must-pass section of both scripts; uptime monitors green for 24 h | append `|^/account` inside the `path_regexp` group: `test-caddy-probes.sh` must fail on `/account/login/` |
| AC3 | the 80-request loop in Checkpoint 2 step 4 | n/a (live check) |
| AC4 | `/careers/` in the must-pass list expects 404 with body over 10 KB | n/a, covered by the AC2 mutation |
| AC5 | Sentry Logs and Security Events counts in Checkpoint 3 | n/a |
| AC6 | the first field of a new access line in Sentry Logs is an IP | n/a (live check) |
| AC7 | `terraform plan` "No changes"; CI green | n/a |

Mutation rule: when a test is written, make its one-line change, confirm the test fails, then undo the change with the exact reverse edit, never by resetting files.

Whole-build checks: `terraform fmt -check -recursive infra/terraform`, `terraform -chdir=infra/terraform validate`, `shellcheck infra/vm/*.sh infra/vm/wac-manage`, `bash infra/vm/test-caddy-probes.sh`, `DJANGO_SETTINGS_MODULE=coderdojochi.test_settings uv run python manage.py test coderdojochi.tests accounts weallcode` (nothing in Django changes, so this should pass unchanged), CI on the PR, and the live checks above.

Before each commit, check the actual files, never the sub-agent's report. Anything that doesn't match goes back to its sub-agent or is fixed, never accepted on trust. Before you call it done, use the site through its real entry point the way a user would: logged out, then logged in with Google, the admin, and the `/join-us/` page (render only, no submit unless Ali OKs it). Check that normal use still works.

## Pitfalls (whole plan)

- `weallcode/urls.py:71` `handler404 = "weallcode.views.page_not_found_view"` is dead code. Django only reads `handler404` from `ROOT_URLCONF` (`coderdojochi.urls`). The view calls `capture_message("Page not found!", level="error")`, so **never wire it into the root URLconf**: every probe would become a Sentry error event and use up the error quota. Removing it is a follow-up.
- Cloudflare's 24 h top IP (99.190.111.100, ~37K requests) was the cache-plan load test, not an attacker.
- The cache rule (`cache.tf`) makes every path on `www` and the apex eligible for caching under respect-origin. Caddy's probe 404 sends `Cache-Control: private`, so it isn't cached. WAF blocks happen before the cache anyway.

## Plan review (2026-11-25)

A fresh sub-agent reviewed the plan. It ran the Caddy snippet in a real local Caddy 2.11.9 and simulated the Cloudflare rules against the fixture. Each finding is folded into the text above:

| # | Severity | Finding | Resolution |
|---|---|---|---|
| 1 | Blocker | The first regex blocked only 498/545 (91%), under the 95% gate. 46 paths (extensionless names, `~` backups, `.config`/`.asax`/`.enc`/`.kv`, `/metrics`, `/health`, `/api/actuator/env` …) passed both layers | Regex widened: `~$`, more extensions, unanchored `/actuator` and `/_profiler`, an exact-name group. It now simulates at 541/543. Edge rule 4 `block_probe_names` added. Gates are now Caddy ≥98%, edge ≥90% `403`, Django ≤2% |
| 2 | Blocker | `/.well-known/security.txt` was in both AC2 and the fixture, and edge rule 1 would 403 it (`txt`) | Rule 1 excludes `/.well-known/`. Both `/.well-known/` paths were removed from the fixture (now 543) |
| 3 | Should-fix | The one-line test Caddyfile with `;` is invalid | Task A step 3 has a multi-line test Caddyfile with `admin off` |
| 4 | Should-fix | The monitor target URLs weren't recorded | Monitors note in Read first (Sentry `GET /`, UptimeRobot `HEAD /`; confirm UptimeRobot in its dashboard) |
| 5 | Should-fix | The `(?i)`/`/Dockerfile` pitfall wording was wrong | Fixed together with #1 |
| 6 | Nit | `wac-staging` only picks up the unit change on a staging deploy | Noted in Task B pitfalls |
| 7 | Nit | The Checkpoint 1 baseline said "all Caddy 404" | Now ~99% Caddy 404, ≤2% Django, `--min-edge 0` |
| 8 | Nit | A sequential 80-curl loop may not hit 60 requests in 10 s | `xargs -P10` |
| 9 | Nit | The scripts didn't skip `#` lines or use `curl -g` | Added to Tasks A and D and to the fixture header |
| 10 | Nit | GraphQL retention on Free is short | Checkpoint 0 step 3 runs first and accepts "unavailable" |

The reviewer confirmed these are safe as planned:
- The snippet adapts and validates. It returns 404 with a 9-byte `Not Found` and `Cache-Control: private`.
- None of the 323 real Django routes (from `get_resolver()`, allauth Google included) match the Caddy regex or the Cloudflare rules.
- Google sign-in, `/anymail/` (exempt from the rate limit) and `/dj-admin/` are not blocked.
- Staging's `basic_auth` runs before `respond`.
- Infra files install only on prod releases, and are validated before they're installed.
- The gunicorn `%%` escaping and the lowercase header name are correct.
- The v5 HCL shape and the `cf.colo.id` characteristic are correct.
- CI already shellchecks new `infra/vm/*.sh` files.

## Progress

- **Checkpoint 0 done (2026-11-25, planning session).** Ali added WAF Edit and Analytics Read to the token.
  - Step 2: both `http_request_firewall_custom` and `http_ratelimit` return "could not find entrypoint ruleset". Nothing to import; Task C creates both.
  - Step 3: GraphQL works with the token. `clientAsn` is not available on Free ("does not have access to the field"), so query `clientIP`, `clientCountryName`, `userAgent` instead. Result for 03:42–03:43 UTC, 404s: 657 requests from `35.233.37.230` (Google Cloud, Belgium region), UA `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36…`. Scanner IP confirmed. Open question in Why is closed; still no IP rule (cloud IPs rotate).
- **Plan changes (2026-11-25, execution session).**
  - Task D moves to Checkpoint 1: CP1 step 5 runs `check-edge-blocks.sh`. It starts once Task A has fixed the format of `scanner-must-pass-paths.txt`.
  - One code PR, so the order is: build A, B, C and D on one branch → CP1 local checks and the Task C fmt/validate/plan → spike apply from the branch (Ali's OK; it only matches the three fake paths, so it needs no origin backstop; if the extension field fails, rule 1 is rewritten in the same PR) → merge (Ali's OK) → `release.sh --target prod` (Ali's OK) → CP1 live checks → full `waf_custom` apply (Ali's OK) → `ratelimit` apply (Ali's OK) → rate-limit test (Ali's OK) → `plan` "No changes". Progress updates after the merge go in a small docs-only PR.
- **Checkpoint 1 local checks pass (2026-11-25).** Steps 1–2 done; steps 3–5 (PR, merge, prod release, live checks) pending.
  - Task A: `bash infra/vm/test-caddy-probes.sh` → `blocked 541/543, fell through 2` (`/api/v1/namespaces/default/secrets`, `/api/graphql`), must-pass 18/18 reach the app. Mutation (a), delete `/\.|`, re-run by the lead → `blocked 436/543`, FAIL; reversed, PASS. Mutation (b), `|^/account` → `/account/login/` and both Google login paths blocked, FAIL; reversed, PASS. Route check over `get_resolver()`: 193 unique literal prefixes, 0 hits.
  - Must-pass statuses recorded from prod: 200 for `/`, `/programs/`, `/team/`, `/mentors/`, `/privacy/`, `/join-us/`, `/classes/476/`, `/our-story/`, `/programs/summer-camps/`, `/account/login/`, `/account/google/login/`, `/robots.txt`, `/sitemap.xml`; `/account/google/login/callback/` 401; `/dj-admin/` 302; `/anymail/resend/tracking/` 405; `/.well-known/security.txt` and `/careers/` 404 (~74.9 KB Django page).
  - Task B: `systemd-analyze verify` (systemd 252, Debian 12 via Apple `container`, no Docker on this Mac) passes for both units; only "not executable" warnings for paths missing in the container. Debug output shows `%%` expands to one `%` and the format stays one argument. Correction to the Task B pitfall: on systemd 252 a single `%(` is passed through unchanged, not rejected; `%%` is still the correct form. A prod release installs the units, runs `daemon-reload` and restarts `wac-web` (`deploy-pull.sh:216-220,243-244`, `provision.sh:125-126,158,195-199`); no manual step.
  - Task D: `check-edge-blocks.sh --must-pass-only https://www.weallcode.org` → 18/18 PASS. Added `--must-pass-only`. Local stub runs confirm the `--min-edge` gate.
  - `shellcheck infra/vm/*.sh infra/vm/wac-manage` passes.
  - Task C (code only, not applied): fmt and validate pass. `terraform plan` → 2 to add (`waf_custom`, `ratelimit`) and 1 in-place update, `google_storage_bucket_object.bootstrap`. That update is caused by this change: `bootstrap.tgz` archives every `infra/vm/` file (Caddyfile, units, new scripts). It is only read on a VM's first boot.
- **PR opened:** https://github.com/WeAllCode/website/pull/1635.
- **Checkpoint 2 step 2, spike, done (2026-11-25, Ali's OK).** `terraform apply -target=cloudflare_ruleset.waf_custom` with every expression ANDed with `(http.request.uri.path in {"/.env.spike" "/spike.php" "/wp-spike"})` → 1 added, ruleset id `5891032e2d2948f581ed08455bd38710`. `/spike.php` 403, `/.env.spike` 403, `/wp-spike` 403, `/` 200, `/privacy/` 200. **`http.request.uri.path.extension` works on Free**; rule 1 stays as written. The spike-only rules stay live (they match nothing real) until the full apply in step 3. `waf.tf` in git keeps the full expressions.
- **Checkpoint 1 done (2026-11-25).** CI green on #1635 (django-postgres, infra, pre-commit, tests). Merged as `298fa88` (Ali's OK). `release.sh --target prod 298fa88` (Ali's OK; prod was on `51ccada`, so only #1635 shipped) → live in ~2 min.
  - `curl https://www.weallcode.org/.env` → `404`, body `Not Found`, 9 bytes, `cache-control: private`, `cf-cache-status: BYPASS`.
  - `/careers/` → 404, 74,884 bytes (AC4).
  - `check-edge-blocks.sh --min-edge 0 https://www.weallcode.org` → PASS: 403 0, Caddy 404 541 (99.6%), Django 404 2 (0.4%: `/api/graphql`, `/api/v1/namespaces/default/secrets`), 200 0; must-pass 18/18.
  - AC6: Sentry Logs (we-all-code-p5, production) access lines start with the client IP from 23:14:29 UTC (`99.190.111.100 - - […] "GET /careers/ …"`, UptimeRobot `157.90.155.240`, SentryUptimeBot `34.85.249.57`); lines before the restart start with `-`. Checked in Chrome: the Sentry MCP connector is bound to a different org.
- **Checkpoint 2 step 3 done (2026-11-25, Ali's OK).** `terraform apply -target=cloudflare_ruleset.waf_custom` → 1 changed (spike → full expressions). `check-edge-blocks.sh https://www.weallcode.org` → PASS: 403 541 (99.6%), Caddy 404 0, Django 404 2 (0.4%), 200 0; must-pass 18/18 (AC1, AC2). Other hosts: apex `/` 200 and `/.env` 403; staging `/` 401 (basic auth) and `/.env` 403. No rule needed disabling.
- **Checkpoint 2 done (2026-11-25).**
  - Step 4: `terraform apply -target=cloudflare_ruleset.ratelimit` (Ali's OK) → 1 added, ruleset id `eaf45c24d1e0439f9fa926536095e666`. `/` still 200.
  - AC3 (Ali's OK, linked sessions warned first): the planned 80 requests with `xargs -P10` got 80×200. From Ali's Mac, requests split between the ORD and CMH data centers (`cf-ray`), and counters are per data center (`cf.colo.id`), so each saw about 40. Rerun with `seq 200 | xargs -P20` (Ali's OK) → 129×200, 71×429; 20 s later → 200. **AC3 passes.** Lesson for future tests: send at least 2.5× the limit, because one client can hit more than one data center.
  - Step 5: the `bootstrap.tgz` re-upload (an `infra/vm/` change from #1635) applied with Ali's OK; `terraform plan` → "No changes" (AC7).
- **Real-entry-point check (2026-11-25 23:35 UTC).** In Chrome, `/` loads with every request 200: 20 `storage.googleapis.com` assets plus Cloudflare's same-origin `/cdn-cgi/…/email-decode.min.js` and `rocket-loader.min.js` (both 200, so custom rules don't hit `/cdn-cgi/`). `/join-us/` renders (not submitted). Ali's existing session: `/account/login/` → `/account/` "My Account", and `/dj-admin/login/` → "Site administration". No 403 or 429. A fresh Google sign-in was not run because the session was already logged in; `/account/google/login/` returns 200 in the must-pass list.
- Next: Checkpoint 3, the 24 h watch, due after 2026-11-26 23:31 UTC (rate limit applied ~23:2x UTC on 2026-11-25): Sentry Logs 404 counts vs the 2,653 baseline, fixture paths reaching Django, Security → Events per rule, uptime monitors, `/join-us/` POSTs. Also open: confirm in the UptimeRobot dashboard that it only checks `/` (logs show `GET /` from UptimeRobot/2.0).
