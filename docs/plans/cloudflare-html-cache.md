# Cache public pages at Cloudflare

## Goal and done

As the We All Code admin, I want Cloudflare to serve the public pages to logged-out visitors from its cache for up to 60 seconds, so that a traffic spike (a newsletter, a news story, registration day) doesn't take down the e2-micro VM, and logged-in users, forms and admin pages still behave exactly as they do today.

Why: the load test on 2026-11-25 against prod (oha, mixing `/`, `/programs/`, `/team/` and `/join-us/`) peaked at about 12 req/s. At 5 concurrent users p95 was 1.7 s. At 10 concurrent users p95 was 7.5 s with 1.8% timeouts, and throughput fell to 3.3 req/s. Every page shows `cf-cache-status: DYNAMIC`, so every request reaches the VM. Raw results are in `/tmp/wac-loadtest/step*.json` (may be gone after a reboot).

Acceptance criteria:

1. AC1: logged-out GETs of the allowlisted public pages (see Task A) return `Cache-Control: public, max-age=0, s-maxage=60`, and on the second request through Cloudflare `cf-cache-status: HIT` with `age` ≤ 60.
2. AC2: every other response (logged-in pages, any response that sets a cookie, redirects, 404s, `/join-us/`, `/account/*`, `/admin/*`, `/dj-admin/*`, `/classes/<pk>/password/`, `/unsubscribe/*`) carries `Cache-Control` containing `private`, and through Cloudflare is never `HIT`.
3. AC3: a request with a `sessionid` cookie (logged in) or a `messages` cookie (a flash message is waiting) is never served from cache (`cf-cache-status` is `BYPASS` or `DYNAMIC`), even on allowlisted paths.
4. AC4: `staging.weallcode.org` and `gcp.weallcode.org` are never cached.
5. AC5: repeating the 2026-11-25 load test on `/` at concurrency 10, 20 and 40 gives p95 under 1 s and 0% errors, and the site still answers normally afterwards.
6. AC6: `terraform plan` shows no changes after the apply.
7. AC7: CI passes, and the existing pages still work: log in with Google, the contact form on `/join-us/`, class detail, the admin.

Out of scope: purging on deploy (a 60-second TTL makes it unnecessary; manual purge is documented in Task C), caching for logged-in users, Django's own cache framework, bumping the VM size.

## Read first

Code:

- `coderdojochi/settings.py:118-129`: `MIDDLEWARE`. The new middleware goes directly after `SecurityMiddleware` (before `SessionMiddleware`). Response middleware runs bottom-up, so the new one must sit above `SessionMiddleware`, `CsrfViewMiddleware` and `MessageMiddleware` to see the cookies they add on the way out.
- `coderdojochi/settings.py:59-68`: cookie settings. No overrides of `SESSION_COOKIE_NAME`, `CSRF_COOKIE_NAME` or `MESSAGE_STORAGE`, so the cookie names are the defaults `sessionid`, `csrftoken` and `messages` (FallbackStorage, cookie first).
- `weallcode/urls.py:22-53`: the public marketing pages and their URL names (`weallcode-home`, `weallcode-our-story`, `weallcode-programs`, `weallcode-programs-summer-camps`, `weallcode-team`, `weallcode-join-us`, `weallcode-associate-board`, `weallcode-privacy`, `weallcode-credits`).
- `coderdojochi/urls.py:168-191`: `/classes/` (redirect), `session-detail` (`/classes/<pk>/`), and the password page. `SessionDetailView` (`coderdojochi/views/sessions.py:145-166`) redirects to the password page when a class has a password and the session lacks it. Keep `session-detail` out of the allowlist for now; see Pitfalls.
- `coderdojochi/urls.py:236-246`: `mentors` (`/mentors/`) and `mentor-detail` (`/mentors/<pk>/`), both public. `mentor_detail.html:28` has an `is_staff` branch, which is safe because staff are logged in (they have `sessionid`).
- `weallcode/templates/weallcode/_header.html:22-26, 44-48`: the only part of the shared layout that differs for logged-in users ("Log In" or "Account"). There is no name, logout form or csrf token in the header or footer.
- `weallcode/templates/weallcode/_base.html:54-60`: renders `messages`. `weallcode/views/join_us.py:14-24`: the contact form POSTs to `/join-us/`, sets `messages.success` and redirects to the same URL. This is why `/join-us/` is excluded and the `messages` cookie bypasses the cache.
- `weallcode/views/home.py:22-25` and `weallcode/views/programs.py:21-22, 36, 89`: content changes for logged-in mentors. That is safe because logged-in requests bypass the cache.
- `infra/terraform/dns.tf:9-20`: the pattern for zone-level Cloudflare resources (`zone_id = var.cloudflare_zone_id`). `infra/terraform/versions.tf:9-12`: provider `cloudflare/cloudflare ~> 5.29`. `infra/terraform/providers.tf:10-11`: the token comes from `CLOUDFLARE_API_TOKEN`.
- `accounts/tests.py`: an existing Django test-client test to copy the style from. `.github/workflows/ci.yml:32-38`: CI runs `DJANGO_SETTINGS_MODULE=coderdojochi.test_settings uv run python manage.py test coderdojochi.tests accounts weallcode`.
- `docs/plans/heroku-to-gcp-e2micro.md`: Progress section. It covers how Terraform is run (the GCS backend `wac-tfstate-wac-website-7bda80`, `CLOUDSDK_ACTIVE_CONFIG_NAME=wac`, `GOOGLE_OAUTH_ACCESS_TOKEN=$(gcloud auth print-access-token --account ali@weallcode.org)`, `CLOUDFLARE_API_TOKEN` from `op://homelab/Cloudflare weallcode Terraform/credential`, with the sandbox disabled), how to release (`infra/vm/release.sh --target staging|prod`), and the staging basic-auth user (`staging`).

Docs (Cloudflare, checked 2026-11-25):

- https://developers.cloudflare.com/cache/how-to/edge-browser-cache-ttl/: Free plan minimum edge TTL is **2 hours** when you override the origin. That is why this plan uses "respect origin" with `s-maxage=60`. The docs don't say whether Free clamps an origin `s-maxage` below 2 hours. Checkpoint 2 step 1 tests this before anything else.
- https://developers.cloudflare.com/cache/concepts/cache-behavior/: with "eligible for cache" and respect-origin, a response with `Set-Cookie` is passed through and **not cached**. With an override TTL, Cloudflare strips the `Set-Cookie` and caches. Never use override here.
- https://developers.cloudflare.com/cache/concepts/default-cache-behavior/: HTML isn't cached without a rule. With a rule, a response that has no `Cache-Control` gets Cloudflare's default TTLs (200: 120 min, 301/302: 20 min, 404: 3 min). That is why the middleware stamps `private` on everything it doesn't mark public.
- https://developers.cloudflare.com/cache/troubleshooting/investigating-uncached-responses/: `private` and `no-store` from origin aren't cached under respect-origin.
- https://developers.cloudflare.com/ruleset-engine/rules-language/fields/reference/http.cookie/: `http.cookie contains "..."` works on Free. `http.request.cookies[...]` and the `matches` operator need Pro or higher, so don't use them.
- https://developers.cloudflare.com/cache/how-to/cache-rules/terraform-example/ and https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/ruleset: the HCL shape. One entry-point ruleset per phase per zone. Import ID `zones/<zone_id>/<ruleset_id>`.
- https://developers.cloudflare.com/api/resources/cache/methods/purge/: `POST /zones/{zone_id}/purge_cache` with `{"purge_everything":true}`, token permission "Cache Purge". Free allows 5 purge-everything calls per minute.

## Tasks

### Task A: cache-header middleware (Checkpoint 1)

Owns: new `coderdojochi/middleware.py`, and `coderdojochi/settings.py` (only the `MIDDLEWARE` list and one new setting).

1. In `coderdojochi/settings.py`, add `PUBLIC_CACHE_SECONDS = env.int("PUBLIC_CACHE_SECONDS", default=60)` next to the other env-driven settings. settings.py reads everything through django-environ's `env`. Setting it to `0` turns public caching off, which is the kill switch: every response gets `private`. The middleware must read `settings.PUBLIC_CACHE_SECONDS` on every request, never at import time, or `override_settings` in the tests won't take effect.
2. Create `coderdojochi/middleware.py` with a function-style middleware `public_cache_headers(get_response)`. After `response = get_response(request)`:
   - If the response already has a `Cache-Control` header, leave it alone. This keeps `never_cache` views as they are, including allauth's `LoginView`, which is `never_cache` and so already `private`.
   - Mark the response public with `django.utils.cache.patch_cache_control(response, public=True, max_age=0, s_maxage=settings.PUBLIC_CACHE_SECONDS)` only when **all** of these hold:
     - `PUBLIC_CACHE_SECONDS > 0`
     - `request.method in ("GET", "HEAD")`
     - `response.status_code == 200`
     - `request.resolver_match` is not None and `request.resolver_match.view_name` is in `PUBLIC_CACHE_VIEW_NAMES`
     - `not request.user.is_authenticated` (use `getattr(request, "user", None)`; treat a missing user as not cacheable)
     - `not response.cookies`, meaning the response sets no cookie
     - `"sessionid"` and `"messages"` are not in `request.COOKIES`. Use `settings.SESSION_COOKIE_NAME`, and `"messages"` for the messages cookie.
   - Otherwise, call `patch_cache_control(response, private=True)`.
3. `PUBLIC_CACHE_VIEW_NAMES` is a module-level frozenset: `weallcode-home`, `weallcode-our-story`, `weallcode-programs`, `weallcode-programs-summer-camps`, `weallcode-team`, `weallcode-associate-board`, `weallcode-privacy`, `weallcode-credits`, `mentors`, `mentor-detail`. Not `weallcode-join-us` (form and csrf cookie) and not `session-detail` (see Pitfalls). Confirm each name with `reverse()` in the test (Task B).
4. In `MIDDLEWARE`, insert `"coderdojochi.middleware.public_cache_headers"` directly after `"django.middleware.security.SecurityMiddleware"`.

Copy: Django's own `django/views/decorators/cache.py` (`never_cache`) for how `patch_cache_control` is used.

Pitfalls:
- The middleware must sit above `SessionMiddleware`, `CsrfViewMiddleware` and `MessageMiddleware` in the list, or `response.cookies` won't yet hold the cookies they set.
- `request.user` is lazy and set by `AuthenticationMiddleware`, but it's read after `get_response`, so it's already present.
- `session-detail` is left out: a password-protected class redirects anonymous visitors (a 302, which gets `private` here), but after a visitor enters the password, the session cookie bypasses the cache anyway. It's still left out until someone checks that `public/session_detail.html` has no per-request content. Add it in a later change.
- Don't touch `Vary`. Django already sends `Vary: Cookie`. The docs don't clearly say whether Cloudflare's default ignores it, so the Checkpoint 2 spike confirms that a `HIT` happens despite it. If it never hits, record it in Progress and stop for Ali.

Proof: Task B's tests.

### Task B: tests (Checkpoint 1, in parallel with Task A)

Owns: new `coderdojochi/tests/test_cache_headers.py`.

It can be written in parallel with Task A because it tests the behavior spec above, not the code. Use `django.test.TestCase` and the test client, with `DJANGO_SETTINGS_MODULE=coderdojochi.test_settings`.

**Decorate the class with `@override_settings(SECURE_SSL_REDIRECT=False)`.** test_settings leaves it True, so otherwise every request is a 301 from SecurityMiddleware. Copy this from `coderdojochi/tests/test_calendar_view.py:16`. Copy the user setup from `accounts/tests.py`, or make a user with `get_user_model().objects.create_user(...)` and `self.client.force_login(user)`.

Each guard in the middleware needs a test that fails without it, so test each condition alone. Use `django.test.RequestFactory` plus a direct call of the middleware with a stub `get_response`, alongside the client tests:
- authenticated user with **no** cookies → `private`. This tests the `is_authenticated` guard.
- anonymous with a `sessionid` cookie → `private`. This tests the request-cookie guard.
- anonymous, and the stub response sets a cookie → `private`. This tests the `response.cookies` guard.

Tests:

1. `test_allowlist_names_resolve`: every name in `PUBLIC_CACHE_VIEW_NAMES` except `mentor-detail` reverses without error. `mentor-detail` takes `pk=1`.
2. `test_anonymous_home_is_public`: `GET /` → 200, `Cache-Control` contains `public`, `s-maxage=60` and `max-age=0`.
3. `test_logged_in_home_is_private`: logged in, `GET /` → `private` and no `public`.
4. `test_join_us_is_private`: `GET /join-us/` → `private`. The page sets the `csrftoken` cookie and isn't allowlisted.
5. `test_login_page_not_public`: `GET /account/login/` → `Cache-Control` does not contain `public`.
6. `test_404_is_private`: `GET /no-such-page-xyz/` → 404 and `private`.
7. `test_messages_cookie_is_private`: set `self.client.cookies["messages"] = "x"`, `GET /` → `private`.
8. `test_kill_switch`: with `override_settings(PUBLIC_CACHE_SECONDS=0)`, `GET /` → `private`.
9. `test_redirect_is_private`: `GET /get-involved/` (302) → `private`.
10. `test_guard_authenticated_no_cookie`, `test_guard_request_sessionid`, `test_guard_response_cookie`: the three RequestFactory tests above. Use `resolve("/")` to set `request.resolver_match` on the factory request.
11. Note: a fake `messages=x` cookie fails to decode, so Django deletes it in the response. Test 7 therefore proves the behaviour, but not the `"messages" in request.COOKIES` line by itself. That's accepted.

Pitfalls:
- The home page queries classes. `test_settings` uses in-memory sqlite, so an empty DB is fine; check that `/` renders 200 there before writing the asserts.
- `/join-us/` renders reCAPTCHA. If it fails under test settings, use `/account/signup/` as the "sets csrftoken" case and say so in the report.
- Assert on parsed directives, not on exact string order: split `Cache-Control` on `,` and strip.

Proof: `DJANGO_SETTINGS_MODULE=coderdojochi.test_settings uv run python manage.py test coderdojochi.tests.test_cache_headers` passes. Also `uv run ruff check .` and `uv run ruff format --check .`, if ruff is configured in `pyproject.toml`; use whatever lint CI runs.

### Task C: Cloudflare cache rule (Checkpoint 2)

Owns: new `infra/terraform/cache.tf`, and `infra/terraform/README.md` (one short section).

It waits for Checkpoint 1 to be live on prod. Without the origin headers, the rule would cache pages with Cloudflare's 2-hour default.

1. Before writing HCL, check that no cache-settings ruleset exists. Use a read-only call with the Terraform token: `curl -s -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" "https://api.cloudflare.com/client/v4/zones/<zone_id>/rulesets" | jq '.result[] | select(.phase=="http_request_cache_settings")'`. If one exists, import it (`terraform import cloudflare_ruleset.cache 'zones/<zone_id>/<ruleset_id>'`) and keep its rules, and record that in Progress. Also check that the token can edit rulesets. If `terraform plan` or the API returns 403, stop: Ali adds "Zone → Cache Rules: Edit" (and "Cache Purge") to the token named in 1Password `op://homelab/Cloudflare weallcode Terraform/credential`.
2. `cache.tf`: one `cloudflare_ruleset` "cache" with `name = "Cache settings"` (required in v5), `kind = "zone"`, `phase = "http_request_cache_settings"` and `zone_id = var.cloudflare_zone_id`. In v5, `rules = [ { ... } ]` is a list attribute, not block syntax. Escape the expression's inner quotes as `\"` in HCL. It has one rule:
   - `ref = "cache_public_html"`, `action = "set_cache_settings"`.
   - expression: `(http.host in {"${var.domain}" "www.${var.domain}"}) and not (http.cookie contains "sessionid=") and not (http.cookie contains "messages=") and not starts_with(http.request.uri.path, "/admin/") and not starts_with(http.request.uri.path, "/dj-admin/") and not starts_with(http.request.uri.path, "/account/")`
   - `action_parameters = { cache = true, edge_ttl = { mode = "respect_origin" }, browser_ttl = { mode = "respect_origin" } }`
   - The path exclusions are belt-and-braces. The real gate is the origin header from Task A.
3. `README.md`: one section, "Edge cache", covering:
   - what is cached and for how long
   - the kill switch: set `PUBLIC_CACHE_SECONDS=0` in the prod env secret and release, or delete the rule and apply
   - a manual purge: `curl -X POST .../zones/<zone_id>/purge_cache -H "Authorization: Bearer ..." -d '{"purge_everything":true}'`

Copy: `infra/terraform/dns.tf:9-20` for the zone-resource style, and the Terraform example in the Cloudflare docs above.

Pitfalls:
- Never use `edge_ttl.mode = "override_origin"`. It strips `Set-Cookie` and caches for at least 2 hours on Free.
- `matches` and `http.request.cookies` aren't available on Free.
- `gcp.` and `staging.` are excluded by the `http.host` check (AC4).
- `terraform apply` needs Ali's OK.

Proof: `terraform fmt -check`, `terraform validate`, then `terraform plan` shows exactly one resource to add (or an in-place update, if it was imported), nothing else.

## Checkpoints

**Checkpoint 1: origin headers live.** Tasks A and B run in parallel, with separate files.

Check:
1. Tests and lint pass locally, then CI passes on the PR.
2. Run the mutation test (see Proof). Deploy the PR branch to staging (`infra/vm/release.sh --target staging --ref <branch>`).
3. Run `curl -sI -u staging:<pw> https://staging.weallcode.org/` and check that `cache-control` shows `public, max-age=0, s-maxage=60`.
4. Check that `/join-us/` and `/account/login/` aren't `public`.
5. Merge with Ali's OK, then release to prod with Ali's OK. Repeat the curl on `https://www.weallcode.org/`. It's still `DYNAMIC` at Cloudflare: no rule yet.

Delivers: correct headers everywhere, with no behavior change for users.

**Checkpoint 2: Cloudflare rule live.** Task C.

Check:
1. **Spike first.** Apply the rule with the host condition narrowed to `www.${var.domain}` and the extra condition `http.request.uri.path eq "/privacy/"`. Then run `curl -sI https://www.weallcode.org/privacy/` three times over 90 seconds. Expect MISS, then HIT with `age` < 60, then MISS or EXPIRED or REVALIDATED once `age` would pass 60.
   - If `age` climbs past 60 on a HIT, Free is clamping `s-maxage` to 2 hours. **Stop.** Delete the rule (apply without it), record it in Progress, and ask Ali. The fallback options are a Worker with the Cache API, Pro plan, or accepting a 2-hour TTL.
2. If the spike passes, widen to the full expression and apply. Then run every curl in Proof (AC1–AC4) and `terraform plan` (AC6).

Delivers: logged-out traffic to the public pages served from Cloudflare's cache.

**Checkpoint 3: load test and wrap-up.**

Check:
1. Repeat the load test against `https://www.weallcode.org/` only, with oha at concurrency 1, 10, 20 and 40 for 20 s each. Apply the same stop rules as on 2026-11-25: stop if errors are over 5% or p95 is over 5 s.
2. Record the table in Progress (AC5).
3. Log in with Google on prod, then submit the contact form on `/join-us/` with your own name ("test, please ignore"), and check that the success message shows. Do this only with Ali's OK, because it emails the staff inbox; otherwise check the form renders. Then check that the admin loads (AC7).

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
  - any `terraform apply`
  - anything that sends email to someone other than Ali
- Never repeat secret values in chat or files. Bash tool calls have no description and no comments. Ali's interactive shells are fish.
- After each checkpoint, if your context window is half full, write which checkpoint is next into Progress and stop; a fresh session continues from this plan.

## Proof

| AC | Test or check | Change that should make it fail |
|---|---|---|
| AC1 | `test_anonymous_home_is_public`; `curl -sI https://www.weallcode.org/` twice shows `HIT`, `age` ≤ 60 | in `middleware.py`, change `public=True` to `private=True` |
| AC2 | `test_join_us_is_private`, `test_404_is_private`, `test_redirect_is_private`, `test_login_page_not_public`, `test_guard_response_cookie`; `curl -sI https://www.weallcode.org/join-us/` twice never shows `HIT` | delete the `not response.cookies` condition (fails `test_guard_response_cookie`); separately, delete `status_code == 200` (fails `test_allowlisted_404_is_private`) |
| AC3 | `test_logged_in_home_is_private`, `test_messages_cookie_is_private`, `test_guard_authenticated_no_cookie`, `test_guard_request_sessionid`; `curl -sI -H 'Cookie: sessionid=x' https://www.weallcode.org/` twice never shows `HIT` | delete the `not request.user.is_authenticated` condition (fails `test_guard_authenticated_no_cookie`); separately, delete the `sessionid` request-cookie check (fails `test_guard_request_sessionid`) |
| AC4 | `curl -sI https://gcp.weallcode.org/` twice and `curl -sI -u staging:<pw> https://staging.weallcode.org/` twice, never `HIT` | remove the `http.host in {...}` clause from the rule (don't apply it; reason it from the expression) |
| AC5 | oha load test in Checkpoint 3 | n/a |
| AC6 | `terraform plan` exits 0 with "No changes" | n/a |
| AC7 | CI green; manual checks in Checkpoint 3 | n/a |

Kill switch: `test_kill_switch`. The change that should make it fail is deleting the `PUBLIC_CACHE_SECONDS > 0` condition.

Mutation rule: when a test is written, make its one-line change, confirm the test fails, then undo the change with the exact reverse edit, never by resetting files.

Whole-build checks: `DJANGO_SETTINGS_MODULE=coderdojochi.test_settings uv run python manage.py test coderdojochi.tests accounts weallcode`, the lint CI runs, `terraform fmt -check` and `terraform validate`, CI on the PR, and the curls above.

Before each commit, check the actual files, never the sub-agent's report. Anything that doesn't match goes back to its sub-agent or is fixed, never accepted on trust. Before you call it done, use the site through its real entry point the way a user would (logged out and logged in), and check that normal use still works.

## Plan review (2026-11-25)

A fresh sub-agent reviewed the plan. Each finding is folded into the task text above:

| # | Severity | Finding | Resolution |
|---|---|---|---|
| 1 | Blocker | test_settings keeps `SECURE_SSL_REDIRECT=True`, so every test request is a 301 | Task B: `@override_settings(SECURE_SSL_REDIRECT=False)` on the class |
| 2 | Should-fix | v5 `cloudflare_ruleset` needs `name`; `rules` is a list attribute | Task C step 2 updated |
| 3 | Should-fix | The AC3 and AC2 mutations wouldn't fail any test (the guards overlap), and the messages test can't isolate its line | Task B adds three RequestFactory guard tests; the Proof table now has one mutation per guard |
| 4 | Nit | allauth `LoginView` is `never_cache`, not its own `max-age` | Task A wording fixed |
| 5 | Nit | settings use django-environ, and the setting must be read per request | Task A step 1 fixed |
| 6 | Nit | The docs don't clearly say Vary is ignored | The spike confirms a `HIT`; stop if not |

The reviewer confirmed these are safe as planned:
- the middleware order
- the CSRF cookie (Django 5.2 always re-sends it when a token renders, so those pages go `private`)
- flash messages
- per-user content
- cookie expressions (they can only over-match, which means an extra bypass, never a leak)
- excluding staging and gcp by host
- 5xx not being cached
- never overriding the edge TTL

## Progress

### Checkpoint 1 (2026-11-25)

- Found during the mutation check: deleting `status_code == 200` did not fail `test_404_is_private`, because `/no-such-page-xyz/` has no `resolver_match` and that guard catches it first. Added `test_allowlisted_404_is_private`: `GET /mentors/999999/` (a `mentor-detail` 404, so `resolver_match` is set) → 404 and `private`. The AC2 status mutation now targets this test.
- Files: `coderdojochi/middleware.py` (new), `coderdojochi/settings.py` (`PUBLIC_CACHE_SECONDS`, middleware after `SecurityMiddleware`), `coderdojochi/tests/test_cache_headers.py` (new, 14 tests). Deviations from the plan: guards live in a helper `_is_publicly_cacheable` with one early return each (`# noqa: PLR0911`); `test_login_page_not_public` creates a Google `SocialApp` because the login template needs one; `test_guard_control_anonymous_is_public` added as the positive control for the guard tests.
- Local: full suite 93 tests OK; `ruff check .` and `ruff format --check .` clean.
- Mutations (each one-line change, then the exact reverse edit; file verified identical afterwards): `public=True`→`private=True` fails `test_anonymous_home_is_public`; delete `response.cookies` guard fails `test_guard_response_cookie`; delete status guard fails `test_allowlisted_404_is_private`; delete `is_authenticated` guard fails `test_guard_authenticated_no_cookie`; delete sessionid guard fails `test_guard_request_sessionid`; delete `seconds <= 0` guard fails `test_kill_switch`. 6/6 killed.
- PR: https://github.com/WeAllCode/website/pull/1628. Staging deploy of `b505447` (basic-auth user is `staging`; password at `op://homelab/WAC staging basic auth/password`). Staging headers: `/`, `/privacy/`, `/mentors/` → `public, max-age=0, s-maxage=60`; `/join-us/` → `private`; `/account/login/` → `max-age=0, no-cache, no-store, must-revalidate, private`; `/no-such-page-xyz/` 404 → `private`; `/get-involved/` 302 → `private`. All `cf-cache-status: DYNAMIC` (no rule yet).
- CI on the PR: tests, django-postgres, pre-commit, infra all pass.
- Checkpoint 2 pre-check (read-only): the Terraform token is active but `GET /zones/<zone_id>/rulesets` returns `10000 Authentication error`, so it lacks ruleset permissions. Needs Ali to add "Zone → Cache Rules: Edit" and "Cache Purge" before Task C.
- Checkpoint 1 closed: PR #1628 merged with Ali's OK (squash `9ce8c61`), released to prod with Ali's OK. Prod: `/`, `/privacy/`, `/mentors/` → `public, max-age=0, s-maxage=60`; `/join-us/` → `private`; `/account/login/` → `…, private`. All `DYNAMIC`.

### Checkpoint 2 (2026-11-25)

- Task C files written by a sub-agent on branch `claude/cf-html-cache-rule`: `infra/terraform/cache.tf` (expression exactly as planned, respect_origin for edge and browser TTL) and the README "Edge cache" section. `terraform fmt -check` and `terraform validate` pass.
- Token: the Terraform token "weallcode Terraform" (a user token) has Zone Settings Write, Zone Read, SSL and Certificates Write, DNS Write on the weallcode.org zone. Tried adding "Cache Settings Write" and "Cache Purge" with the `cf` CLI (v0.15.0, Ali's OAuth login): `PUT /user/tokens/<id>` returns `9109 Unauthorized`, because `cf`'s OAuth scopes don't cover API-token management. Ali has to add them in the dashboard (My Profile → API Tokens → weallcode Terraform → Edit).
- Ali added them. `GET .../rulesets/phases/http_request_cache_settings/entrypoint` → "could not find entrypoint ruleset", so there was no existing cache ruleset to import.
- Terraform setup: `terraform.tfvars` copied from the `heroku-free-hosting-migration-a21bab` worktree (gitignored); `terraform init -reconfigure -backend-config="bucket=wac-tfstate-wac-website-7bda80"`. Baseline plan: `cloudflare_ruleset.cache` to add, plus unrelated drift from #1625 (`google_compute_instance.web` metadata startup-script and `google_storage_bucket_object.bootstrap`, both in place). Ali: include the drift in the full apply so AC6 ends at "No changes".
- Before applying, checked Ali's other running session (upgrade-cp3, dependency upgrades Checkpoint 3): Python bumps only, no Terraform or Cloudflare work. Sent it an FYI about the cache (use `sessionid=x` or a query string to reach origin).
- Spike (Ali's OK): applied `-target=cloudflare_ruleset.cache` with the expression narrowed to `http.host eq "www.weallcode.org" and http.request.uri.path eq "/privacy/"` → 1 added (ruleset id `386a3a700609476fb45ed5913c03b62f`) at 17:28:38Z. `curl -sI https://www.weallcode.org/privacy/` every 10 s:

  | UTC | cf-cache-status | age |
  |---|---|---|
  | 17:28:42 | MISS | |
  | 17:28:53 | HIT | 10 |
  | 17:29:03 | HIT | 20 |
  | 17:29:13 | MISS | |
  | 17:29:24 | HIT | 10 |
  | 17:29:34 | HIT | 20 |
  | 17:29:44 | (request hung 46 s, empty) | |
  | 17:30:30 | EXPIRED | |
  | 17:30:40 | MISS | |
  | 17:30:51 | HIT | 20 |

  Result: **no clamp.** `age` never passed 20, and the object filled at 17:29:13 was `EXPIRED` 77 s later. `HIT` happens despite `Vary: Cookie`. The occasional early `MISS` is most likely a different cache node in the colo. The 46 s hang was a one-off: right afterwards `/`, `/privacy/` and a cache-busted `/` answered 200 in 0.1–0.4 s. Watch for it in the load test.
- Widened back to the full expression (sub-agent, restored verbatim; `fmt -check` passes). Full plan: `0 to add, 3 to change, 0 to destroy` (ruleset expression in place, plus the #1625 drift). Applied at 17:32:24Z per Ali's "include it".
- AC6: `terraform plan` → "No changes. Your infrastructure matches the configuration."
- AC1: `www /` MISS then HIT `age: 2`; apex `/` HIT, `age` 34–39 over 6 requests; `/programs/` and `/team/` MISS then HIT with `age` 1–6. All `public, max-age=0, s-maxage=60`.
- AC2: `/join-us/` `private`, `BYPASS` twice; `/account/login/` `…, private`, `DYNAMIC` twice.
- AC3: `www /` with `Cookie: sessionid=x` → `private`, `DYNAMIC` twice; with `Cookie: messages=x` → `private`, `DYNAMIC` twice.
- AC4: `gcp.weallcode.org/` and `staging.weallcode.org/` (basic auth) send `public, …s-maxage=60` from origin but are `DYNAMIC` twice each: the host clause excludes them.

