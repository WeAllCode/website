# Edge cache: close the query-string gap

Follow-up to `docs/plans/cloudflare-html-cache.md`. That plan is complete: PRs WeAllCode/website#1628 and WeAllCode/website#1631 merged on 2026-11-25, and its after-load-test p95 was 61 ms at 40 concurrent users. This plan covers only the gaps still left, and drops the ones that aren't real risks (see "Gaps checked and dropped").

## Goal and done

As the We All Code admin, I want a newsletter or social-media spike to be served from Cloudflare's cache even when every visitor's link carries a different query string (`?utm_…`, `?fbclid=…`, `?gclid=…`, Mailchimp's per-recipient `?mc_eid=…`), so that the e2-micro VM doesn't see one uncached request per click.

Why: the cache key includes the query string, and Free can't set "Ignore query string" in a cache rule (Enterprise, and Pay-as-you-go, only). Checked on prod on 2026-11-26 at 17:26Z: `/?utm_source=aN` returned MISS, then HIT; `/?utm_source=bN` returned MISS. A blast with unique per-recipient parameters is therefore fully uncached, which is the same failure as the 2026-11-25 baseline (p95 7.5 s at 10 concurrent users). The same hole lets anyone bust the cache with `?x=<random>`.

Fix: a Free URL-rewrite Transform Rule removes the query string on the allowlisted public paths for logged-out requests, before the cache lookup. None of those views read `request.GET`, so they render the same page either way. Analytics still sees the campaign parameters, because GA4 reads them from the browser URL, which doesn't change.

Acceptance criteria:

1. AC1: on the apex and `www.`, two logged-out GETs with **different** query strings (`?utm_source=a<r>`, then `?utm_source=b<r>`) give MISS (or EXPIRED), then HIT. Check this on `/`, `/programs/summer-camps/` and one `/mentors/<pk>/`.
2. AC2: the rewrite doesn't touch any other request. `/join-us/?x=1`, `/account/login/?next=/account/`, `/classes/?x=1`, any request with a `sessionid` or `messages` cookie, and `staging.` and `gcp.` all reach the origin with their query strings intact. Proof: logging in through `/account/login/?next=/account/` lands on `/account/`, and `/join-us/?x=1` is still `BYPASS`. Don't use the login page's hidden `next` input as proof: it already renders `value=""` today (`accounts/templates/account/login.html:32`, an existing quirk that's out of scope).
3. AC3: `<link rel="canonical">` on public pages never includes a query string. Proof: `GET /?utm_source=x` renders `href="https://www.weallcode.org/"`.
4. AC4: repeating the load test with a unique query string on every request (`/?n=<counter>`) at concurrency 10 and 40 gives p95 under 1 s and 0% errors.
5. AC5: `terraform plan` shows "No changes" after the apply, and CI passes.

Known gap, accepted: a campaign link without its trailing slash (`/programs/summer-camps?utm_source=…`) gets Django's `APPEND_SLASH` 301 from the origin every time (`private`, `BYPASS`; checked on prod 2026-11-26). The redirect is cheap because it runs before the view, and it lands on the cached URL. Write campaign links with the trailing slash. If a spike still shows these 301s, an edge Redirect Rule is the follow-up.

Out of scope: purge on deploy, the `csrftoken` cookie, `/dojo/` (all dropped below), and caching more views.

## Gaps checked and dropped

| Gap from the brief | Why it's not a real risk | Evidence |
|---|---|---|
| Purge on deploy (`release.sh`, `deploy-pull.sh`) | HTML is stale for at most 60 s. Static files are hashed (`ManifestFilesMixin`), and `collectstatic --noinput` runs without `--clear`, so old hashed files stay in GCS and a stale page still loads its old CSS and JS. A purge would also need a Cloudflare token on the VM, which is more risk than it removes. A manual purge is documented in `infra/terraform/README.md` "Edge cache". | `coderdojochi/storage_backends.py:11`, `infra/vm/deploy-pull.sh:250`, `coderdojochi/settings.py:277-283` |
| Bypass on the `csrftoken` cookie | This cookie doesn't mean the visitor is logged in; that needs `sessionid`, which already bypasses the cache. A cached anonymous page served to someone holding `csrftoken` is correct. If a template on an allowlisted page ever renders `{% csrf_token %}`, Django sets the cookie on the response, and the middleware's `response.cookies` guard marks it `private`, so it can't be cached by mistake. No allowlisted template renders a token today. | `coderdojochi/middleware.py:53-55`, `test_guard_response_cookie`; `git grep -l csrf_token -- '*.html'` lists no allowlisted template |
| Bypass on `/dojo/` | The route doesn't exist; it's commented out. It returns 404, and the middleware makes every 404 `private`. | `coderdojochi/urls.py:278-279` |
| Bypass on POSTs | Cloudflare never caches POSTs, and the middleware only marks GET and HEAD `public`. | `coderdojochi/middleware.py:37` |
| Django messages on cached pages | A waiting flash puts a `messages` cookie on the request, or a `sessionid` when it falls back to the session; both bypass the cache at the edge and at the origin. Verified on prod in the earlier plan's AC7. | `infra/terraform/cache.tf:18`, `cloudflare-html-cache.md` Progress, Checkpoint 3 |
| Staging basic auth | The cache rule matches only the apex and `www.`; staging was `DYNAMIC` in the earlier plan's AC4. | `infra/terraform/cache.tf:18` |
| `Cache-Control` and `Vary` | Already in place: `public, max-age=0, s-maxage=60` on allowlisted pages and `private` on everything else. `Vary: Cookie` doesn't prevent HITs. | earlier plan, Checkpoint 2 spike |
| Free clamping a short `s-maxage` up to 2 h | Disproven by the earlier spike. | earlier plan, Checkpoint 2 |

## Read first

- `docs/plans/cloudflare-html-cache.md`, in full: how the cache works, how Terraform is run (GCS backend, `CLOUDSDK_ACTIVE_CONFIG_NAME=wac`, `GOOGLE_OAUTH_ACCESS_TOKEN=$(gcloud auth print-access-token --account ali@weallcode.org)`, `CLOUDFLARE_API_TOKEN` from `op://homelab/Cloudflare weallcode Terraform/credential`, with the sandbox disabled), the spike method, and the load-test command. Never use the ali.karbassi@bebraven.org account.
- `coderdojochi/middleware.py:15-28`: `PUBLIC_CACHE_VIEW_NAMES`. The rewrite's path list must match these views exactly.
- `weallcode/urls.py:22-53` and `coderdojochi/urls.py:236-258`: the paths for those names. They are `/`, `/our-story/`, `/programs/`, `/programs/summer-camps/`, `/team/`, `/join-us/associate-board/` (nested under `join-us/`), `/privacy/`, `/credits/`, `/mentors/` and `/mentors/<pk>/`. Task B's test checks this list against `reverse()`. `/mentors/<pk>/approve-avatar/` and `/mentors/<pk>/reject-avatar/` are staff actions and are excluded from the rewrite.
- `infra/terraform/cache.tf`: the ruleset style to copy. Its expression is the host and cookie clauses to reuse.
- `infra/terraform/waf.tf:47-73` and README "WAF and rate limit", line 116: the rate limit (60 requests per 10 s per IP) has to be disabled for a load test, then re-enabled. Both are live changes that need Ali's OK.
- `infra/terraform/README.md:88-101`: the "Edge cache" section to extend.
- `weallcode/templates/weallcode/_base.html:13`: the canonical link uses `request.get_full_path`, which includes the query string.
- `coderdojochi/tests/test_cache_headers.py`: the test style and `@override_settings(SECURE_SSL_REDIRECT=False)`.
- Cloudflare docs: https://developers.cloudflare.com/rules/transform/url-rewrite/ (static query rewrite) and https://developers.cloudflare.com/cache/how-to/cache-rules/settings/ (the Cache Key query options are Enterprise-only). Neither page says that an empty static value removes the query string, or that the cache key uses the rewritten URL. The Checkpoint 2 spike tests both before anything else.

## Tasks

### Task A: query-strip Transform Rule (Checkpoint 1)

Owns: new `infra/terraform/transform.tf`, and `infra/terraform/README.md` (the "Edge cache" section only).

1. Read-only pre-check with the Terraform token: `curl -s -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" "https://api.cloudflare.com/client/v4/zones/<zone_id>/rulesets/phases/http_request_transform/entrypoint" | jq '.success, .errors, .result.rules'`. "could not find entrypoint ruleset" means you create it. If it exists, import it (`zones/<zone_id>/<ruleset_id>`) and keep its rules. On an authentication or 403 error, stop: Ali adds "Transform Rules: Edit" to the token.
2. `transform.tf`: one `cloudflare_ruleset` "transform", with `name = "Transform rules"`, `kind = "zone"`, `phase = "http_request_transform"` and `zone_id = var.cloudflare_zone_id`. It has one rule:
   - `ref = "strip_query_public_html"`, `action = "rewrite"`
   - `action_parameters = { uri = { query = { value = "" } } }`
   - expression: `(http.host in {"${var.domain}" "www.${var.domain}"}) and http.request.method in {"GET" "HEAD"} and http.request.uri.query ne "" and not (http.cookie contains "sessionid=") and not (http.cookie contains "messages=") and (http.request.uri.path in {"/" "/our-story/" "/programs/" "/programs/summer-camps/" "/team/" "/join-us/associate-board/" "/privacy/" "/credits/" "/mentors/"} or (starts_with(http.request.uri.path, "/mentors/") and not ends_with(http.request.uri.path, "-avatar/")))`
   - Above is the logical expression. In HCL, escape every inner quote as `\"` and use `${var.domain}` interpolation, exactly as `infra/terraform/cache.tf:18` does.
   - Add a comment at the top: this list must match `PUBLIC_CACHE_VIEW_NAMES` (Task B's test checks it), and Free can't ignore query strings in the cache key.
3. README "Edge cache": one paragraph on what the rule strips and why, the kill switch (`enabled = false`, then apply), and the fact that the path list mirrors the middleware allowlist.

Pitfalls:
- `starts_with(…, "/mentors/")` would also match the avatar actions, hence the `-avatar/` exclusion. Those actions are staff-only, so logged-in, so `sessionid` already excludes them, but don't rely on that. Reviewed: `coderdojochi/views/public/mentor.py:7-34` doesn't paginate or read `request.GET`.
- If the API rejects an empty `value`, or v5 stores `""` as null and `terraform plan` keeps showing a diff, don't invent a workaround: record it in Progress and stop for Ali.
- Free has 10 Transform Rules, and this uses 1.

Proof: in a fresh worktree, first run `terraform -chdir=infra/terraform init -reconfigure -backend-config="bucket=wac-tfstate-wac-website-7bda80"`, and copy the gitignored `terraform.tfvars` from the main checkout. Then `terraform -chdir=infra/terraform fmt -check`, `validate`, and `plan` must show exactly one ruleset to add and nothing else. Report any drift instead of applying it.

### Task B: canonical without the query string (Checkpoint 1, in parallel with Task A: separate files)

Owns: `weallcode/templates/weallcode/_base.html` (line 13 only), and `weallcode/tests.py` (a module, not a package; add one test class).

1. Change `{{ request.get_full_path }}` to `{{ request.path }}` in the canonical link.
2. Test `test_canonical_drops_query`: `GET /?utm_source=x` → the response contains `<link rel="canonical" href="…/" />` and doesn't contain `utm_source`. Use `@override_settings(SECURE_SSL_REDIRECT=False)`.
3. Test `test_rewrite_paths_match_allowlist`: read `Path(settings.BASE_DIR) / "infra/terraform/transform.tf"`, not a path relative to the cwd. Take the `http.request.uri.path in {…}` set from the `strip_query_public_html` expression, unescape the `\"` quotes, and keep only strings that start with `/`, so that `"GET"`, `"sessionid="`, `"-avatar/"` and the host strings are dropped. Then assert that `{reverse(n) for n in PUBLIC_CACHE_VIEW_NAMES - {"mentor-detail"}}` equals that set, and that `reverse("mentor-detail", kwargs={"pk": 1})` starts with `/mentors/`. Write it against the expression text in Task A step 2; the lead runs it once both tasks are done.

Coordination: this touches `weallcode/templates/weallcode/_base.html`, which `docs/plans/frontend-rewrite.md` (4G, line 271) also edits. It's a one-line change on a different line, but rebase onto main before starting and check that line 13 is unchanged.

Proof: `DJANGO_SETTINGS_MODULE=coderdojochi.test_settings uv run python manage.py test weallcode` passes. Mutations: revert to `request.get_full_path` and `test_canonical_drops_query` must fail; change `/join-us/associate-board/` to `/associate-board/` in `transform.tf` and `test_rewrite_paths_match_allowlist` must fail.

## Checkpoints

**Checkpoint 1: code ready, nothing live.** Tasks A and B run in parallel.

Check: the full suite (`DJANGO_SETTINGS_MODULE=coderdojochi.test_settings uv run python manage.py test coderdojochi.tests accounts weallcode`), `uv run ruff check .`, `uv run ruff format --check .`, `terraform fmt -check`, `terraform validate`, `terraform plan` (one add), the Task B mutation, then a draft PR with CI green. Stop for Ali's OK before Checkpoint 2.

**Checkpoint 2: rule live.** This is a live Cloudflare change, so it needs Ali's OK first. Run it from the PR branch, before merging, so main never holds an unapplied or failed `transform.tf`.

1. **Spike first.** As a local, uncommitted edit of `transform.tf`, apply with the expression narrowed to `http.host eq "www.weallcode.org" and http.request.uri.path eq "/privacy/" and http.request.uri.query ne ""`. Then, with `r=$RANDOM`, curl `/privacy/?a=$r` and then `/privacy/?b=$r`. The second must be HIT, and `terraform plan` must show "No changes" (no perpetual diff from `value = ""`). If either fails (the cache key still uses the original query), **stop**: remove the rule, record it in Progress, and ask Ali. The fallbacks are a Worker, or accepting the gap.
2. Restore the full expression with the exact reverse edit (`git diff` on `transform.tf` must be empty), then apply. Run the AC1 and AC2 curls, then `terraform plan` → "No changes" (AC5).
3. Only then merge the PR and `release.sh --target prod` for Task B's canonical change, each with Ali's OK. For AC2, also log in on prod through `/account/login/?next=/account/` in Ali's browser and check that it lands on `/account/`.

**Checkpoint 3: load test.** This needs Ali's OK, because the rate limit has to come off and go back on, and both are live changes.

1. Set `enabled = false` on `per_ip_60_per_10s` and apply.
2. Run `oha -z 20s -c N -t 10s --no-tui --output-format json --rand-regex-url 'https://www.weallcode.org/[?]n=[0-9]{8}'`. The reviewer checked this with `--dump-urls`; escaping with `\.` produces junk hosts. at N = 10 and N = 40. Stop if errors are over 5% or p95 is over 5 s. Record the results in Progress (AC4).
3. Re-enable the rate limit and apply. `terraform plan` → "No changes".

## How to run it

- Read the whole plan first. Run it as the lead: you write no code. Give Tasks A and B to two sub-agents at once. Each brief names its task, its files and only those, its Proof command as the bar, and the report format (files changed, commands with pass/fail, deviations), and tells it not to run git.
- You alone run each check, commit (one commit per checkpoint), and write the results and evidence into Progress. If something comes up that isn't in the plan, write it into the plan before anyone builds it.
- Ask Ali before any `terraform apply`, any live Cloudflare change, any merge, and any `release.sh --target prod`. Never repeat secret values. Bash calls have no description and no comments.
- After each checkpoint, if your context window is half full, write which checkpoint is next into Progress and stop.

## Proof

| AC | Test or check | Change that should make it fail |
|---|---|---|
| AC1 | Spike, then the full-rule curls: different query strings → MISS, then HIT | set `enabled = false` on the rule (reason it, don't apply) |
| AC2 | `/join-us/?x=1` is `BYPASS`; logging in through `?next=/account/` lands on `/account/` | drop the `http.request.uri.path in {…}` clause (reason it; it would strip `?next=`) |
| AC3 | `test_canonical_drops_query` in `weallcode/tests.py` | revert `_base.html:13` to `request.get_full_path` |
| AC4 | oha with random `?n=` | n/a |
| AC5 | `terraform plan` "No changes"; CI green | n/a |

Mutation rule: make the one-line change, confirm the test fails, then undo it with the exact reverse edit, never by resetting files. Before each commit, check the actual files, never the sub-agent's report. Before calling it done, browse the public pages logged out and logged in, and check that normal use still works.

## Plan review (2026-11-26)

A fresh sub-agent reviewed the plan. Each finding is folded into the text above:

| # | Severity | Finding | Resolution |
|---|---|---|---|
| 1 | Blocker | The associate board is `/join-us/associate-board/`, not `/associate-board/` (`weallcode/urls.py:39-46`) | Path fixed; Task B adds `test_rewrite_paths_match_allowlist` against `reverse()` |
| 2 | Blocker | The login page's `next` hidden input already renders `value=""` on prod, so the proof would fail before any change | AC2 now proves it with the login redirect and a `BYPASS` check |
| 3 | Blocker | The oha regex with `\.` produces junk hosts | Use `https://www.weallcode.org/[?]n=[0-9]{8}` (checked with `--dump-urls`) |
| 4 | Should-fix | `starts_with("/mentors/")` also covers the staff avatar actions | Excluded with `not ends_with(…, "-avatar/")` |
| 5 | Should-fix | `weallcode/tests.py` is a module | Task B writes there |
| 6 | Should-fix | v5 may treat `value = ""` as null and drift | The spike also requires `terraform plan` to show "No changes" |
| 7 | Should-fix | AC1 tested only `/` | AC1 adds `/programs/summer-camps/` and `/mentors/<pk>/` |
| 8 | Nit | The pre-check named no command | Exact curl and jq added |
| 9 | Nit | The docs don't confirm URL rewrite on Free, or that it runs before the cache key is built | The spike runs first and stops if either is false |

Second review (fresh sub-agent, the same day):

| # | Severity | Finding | Resolution |
|---|---|---|---|
| 10 | Should-fix | A link without the trailing slash gets an origin 301 on every click, and the query string survives it | Recorded as an accepted known gap under Goal; campaign links use the trailing slash |
| 11 | Should-fix | The Task B test depended on the cwd, and a naive quote regex would capture `GET`, the cookies and `-avatar/` | Read via `settings.BASE_DIR`, unescape the quotes, keep only strings starting with `/` |
| 12 | Should-fix | Checkpoint 2 merged before the spike, so a failed spike would leave main with an unapplied `transform.tf` | Spike from the branch as an uncommitted edit; merge only after it passes |
| 13 | Nit | The plan showed the expression with bare quotes | Note added: escape as `\"`, like `cache.tf:18` |
| 14 | Nit | The fresh worktree needs `terraform init`, and the commands lacked `-chdir` | Task A Proof spells out init, tfvars and `-chdir` |

Both reviewers confirmed that all the dropped gaps hold up, that no allowlisted view reads `request.GET` or paginates, and that the expression can't leak per-user content.

## Progress

### Before (2026-11-26 17:26Z, prod)

`/?utm_source=a<r>` → MISS, repeated → HIT, `/?utm_source=b<r>` → MISS. Every distinct query string gets its own cache entry.

### Checkpoint 1 (2026-11-26)

- Branch rebased onto main (`788c94b`); `_base.html:13` was unchanged.
- Task A (sub-agent): new `infra/terraform/transform.tf` with the expression exactly as planned, plus a README "Edge cache" paragraph. Deviation: the rule has a `description`, like cache.tf.
- Task B (sub-agent): `_base.html:13` now uses `request.path`; `weallcode/tests.py` gains `EdgeQueryStripTest` (2 tests). Deviation: the canonical assert checks against `settings.META_SITE_DOMAIN`.
- Lead checks: full suite (199 tests) OK; `ruff check` and `ruff format --check` clean; `terraform fmt -check` and `validate` pass.
- Mutations, each undone with the exact reverse edit: `get_full_path` fails `test_canonical_drops_query` (sub-agent); `/associate-board/` in transform.tf fails `test_rewrite_paths_match_allowlist` (lead). 2/2 killed.
- `terraform plan` (`-lock=false`, read-only): `cloudflare_ruleset.transform` to add, plus unrelated drift (`google_compute_instance.web` and `google_storage_bucket_object.bootstrap` in place, from VM changes on main). The apply will use `-target=cloudflare_ruleset.transform`, so the VM isn't touched in this work.
- Pre-check: `GET …/phases/http_request_transform/entrypoint` → "request is not authorized". The token "weallcode Terraform" has Cache Settings Write, Zone WAF Write, Zone Settings Write, Zone Read, SSL and Certificates Write, Cache Purge, DNS Write and Analytics Read, but **no Transform Rules permission**. Blocked on Ali adding "Transform Rules: Edit".
