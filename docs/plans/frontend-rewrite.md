# Replace jQuery, Foundation, Bootstrap 3 and Font Awesome with plain modern HTML, CSS and JS

Status: **plan only, approved goal and criteria by Ali 2026-11-25.** Nothing built. Written 2026-11-25 from `main` at `933ac62` (Checkpoint 9 of the dependency-upgrade plan, on prod).

**Ali's decisions (2026-11-25 interview). These override anything below that contradicts them:**

- Look the same. This is a plumbing change, not a redesign.
- **New class names.** Don't re-implement Foundation's or Bootstrap's class names. Follow the Google Chrome `modern-web-guidance` rules (https://github.com/GoogleChrome/modern-web-guidance) for every piece of UI.
- Icons are inline SVG with no sprite for the Font Awesome or Glyphicons replacements. The existing `weallcode/_svgs.html` program-icon sprite is not an icon font and stays.
- In scope: delete dead front-end code, drop `django-bootstrap3`, drop `js-datepicker`, and fix the 3 broken Bootstrap popovers.
- Browser policy: **Baseline Widely available** with no fallbacks. Newer features (interest invokers, `popover="hint"`, anchor positioning, `hidden="until-found"`) only with feature detection that degrades gracefully. **Never a polyfill.**
- No build tooling. Plain `.css` (native nesting, `@layer`) and plain `.js` (ES modules) served through `collectstatic`. No npm, Sass or bundler in the repo.
- Dashboard: shared tokens and reset, plus its own `dashboard.css` that keeps today's Bootstrap look.
- "Look the same" is a pixel threshold: each page differs from `main` by **< 1 % of pixels** at 1280 and 390 px. Only failures go to Ali.
- One PR per checkpoint, each through CI, staging and prod with Ali's OK (same runbook as `docs/plans/dependency-upgrades-2026-11.md`).
- **Never send any email (Ali, 2026-11-25).** This holds for local runs, staging and prod, for every task, check and manual step.
  - Every local server and script runs with `EMAIL_BACKEND=anymail.backends.test.EmailBackend` and `RESEND_API_KEY=` (empty). `seed.sh` exports both. It aborts unless `manage.py shell -c "from django.conf import settings; print(settings.EMAIL_BACKEND)"` prints the test backend in both trees, and only then starts the servers.
  - No script or person submits a form that can send mail: sign-up, password reset, contact, join-us, associate board, session or meeting sign-up, announce, check-in, email change or verification. The only allowed submit is 1A's `--post-invalid` (an empty required field, so it can't validate), and only on the local server.
  - The "Announce" check only opens the popover and reads the link's `href`. It never follows it.
  - On staging and prod: read-only page loads only, and no form submits at all.
  - If a step would need an email to prove itself, it gets a Django test with the anymail test backend (`mail.outbox`) instead.

## Goal and done

**User story.** As the maintainer of weallcode.org, I want every page built on plain modern HTML, CSS and JS, with no jQuery, Foundation, Bootstrap 3, Font Awesome, what-input or js-datepicker, and looking the same as today, so the front-end is small, has no unmaintained libraries, and is easy to change.

**Acceptance criteria.**

1. No page loads jQuery, Foundation (JS or CSS), Bootstrap 3 (JS, CSS or Glyphicons), Font Awesome 4 or 5, what-input or js-datepicker. Their `coderdojochi/static/vendor/` directories and `vendor.json` entries are deleted, and so are `weallcode/css/foundation*.css`. `django-bootstrap3` is gone from `pyproject.toml`, `uv.lock` and `INSTALLED_APPS`.
2. Every page in the A/B page list (below), at 1280 × 800 and 390 × 844, differs from the same page served by `main` on the same database by **< 1 %** of pixels. Known-dynamic regions are masked.
3. These work by mouse, keyboard and touch: the mobile nav, the team page "See more" buttons, the dashboard navbar collapse at mobile width, the dashboard "Show/Hide" rows, and the 3 fixed hints (meeting "Announce", mentor background-check hint, session gender-limit hint).
4. CSS + JS + font bytes transferred per page are lower than on `main` for every page in the list.
5. There are zero new console errors and zero failed requests compared with `main`. The full test suite passes, including the new guard tests.
6. Dead front-end code is deleted (list in 1B).
7. Every task follows the `modern-web-guidance` guides named in it. `legacy-scan` on the front-end sources ends with 0 unjustified findings (baseline 6, listed in "Read first").

**Out of scope.** Redesign. HTML emails (`coderdojochi/emailtemplates/`, `accounts/templates/account/email/`), which use inline styles. The Django admin (`/dj-admin/`), which ships its own jQuery. Chart.js, the Sentry bundle and the Fontsource fonts, which stay vendored. Setting `CSRF_COOKIE_HTTPONLY = True` once `cdc.js` is gone (follow-up, see Pitfalls). The `cdc_admin` `ZeroDivisionError` (`old_views.py:289`).

## Read first

The builder must read these before starting. Line numbers are at `933ac62`.

**Bases (everything inherits from 2 of them):**
- `weallcode/templates/weallcode/_base.html:34-39` (CSS: FA5, fonts, `foundation.min.css`, `app.css`), `:46` (skip link), `:72-75` (jQuery, what-input, Foundation JS, `app.js`), `:80-89` (donation widget, GA4; keep both). Public pages, `accounts/` and every non-dashboard `coderdojochi/` page extend it: `coderdojochi/_base.html` is a one-line `{% extends "weallcode/_base.html" %}`, and `account/_base.html` extends that.
- `coderdojochi/templates/dashboard/_admin_base.html:12-19` (fonts, FA4, Bootstrap CSS), `:29` (`_topnav.html`), `:33` (`_messages_bootstrap.html`), `:42-43` (jQuery, Bootstrap JS). Extended by `dashboard/admin.html`, `meeting_check_in.html`, `session_check_in.html`, `session_check_in_mentors.html` and `session_donations.html`. `dashboard/session_stats.html` extends the Foundation base, not this one.

**JS today:**
- `weallcode/static/weallcode/js/app.js` (whole file, 17 lines) is the only jQuery code. It does `$(document).foundation()`, toggles `.mobile-nav`, handles `[data-toggler]` (only `team.html:150,192`) and `.autoreveal` (used nowhere). No template uses a Foundation JS plugin attribute (checked: no `data-reveal`, `data-dropdown`, `data-accordion` and so on). Every inline page script is already vanilla (`admin.html:22-75`, `session_check_in.html:61-115`, `session_stats.html:82-130` (Chart.js), `account/email.html:61-70`, `welcome.html:79-104`).
- Bootstrap JS is used only on dashboard pages: navbar collapse (`data-toggle="collapse" data-target="#navbar"` in all 5 dashboard templates and `_topnav.html:5`) and row collapse (`admin.html:190,268,328,368`).

**Broken today (Bootstrap popover markup on Foundation pages, where Bootstrap JS isn't loaded):**
- `coderdojochi/templates/meeting_detail.html:69`: the staff "Announce" link opens a popover holding the only link to `meeting-announce`. **Staff can't announce a meeting from this page today.**
- `accounts/templates/account/mentor/home.html:30`: background-check hover hint.
- `coderdojochi/templatetags/coderdojochi_extras.py:114-122`: gender-limitation hover hint on the session sign-up button.

**CSS today:**
- `weallcode/static/weallcode/css/foundation.min.css` (152 KB, a custom Foundation 6.5.1 build with spacing and colour utilities; no SCSS source in the repo). The unminified `foundation.css` sits next to it. Check whether it's the same build before using it as the reference: pretty-print the min file in `/tmp` and diff the selector lists. If they differ, the min file is the truth. Useful places in `foundation.css`: breakpoints `:8` (40em) and `:483` (64em), headings `:284`, `.show-for-sr` `:1391`, spacing utilities `:1231`, `.breadcrumbs` `:2942`, `.grid-container` `:4216`.
- `weallcode/static/weallcode/css/app.css` (781 lines, unlayered): brand tokens `:1-25`, `scroll-behavior` `:29`, site classes (`.text-*`, `.bg-*`, `.title`, `.subtitle`, `.program-icon`, …) and 16 media queries.
- Class usage on Foundation-base pages (counted 2026-11-25): `cell` 197, `grid-x` 92, `button` 77, `medium-6` 53, `grid-container` 50, `grid-margin-x` 34, `grid-margin-y` 31, `margin-*`/`padding-*` ~300, plus Bootstrap 3 leftovers (`list-group-item`, `well`, `col-*`, `hidden-xs`, `thumbnail`, `form-control`) that **render unstyled today**, because Bootstrap CSS isn't on those pages. To look the same, a migrated template drops any class that has no rule in `foundation.min.css` or `app.css`. Don't restyle it.
- `coderdojochi/forms.py:130-398` puts `form-control` and `btn btn-xs btn-link` into widget attrs. These are unstyled on Foundation pages too.
- Dashboard pages use Bootstrap's grid (`row`, `col-sm-*`), `navbar`, `panel`, `table-striped`, `progress`, `badge` and `glyphicon-check` (`admin.html:228,256,358`). `session_partner_password.html:29` uses `glyphicon-exclamation-sign` on a Foundation page.

**Icons in use (Font Awesome and Glyphicons, 2026-11-25):** `fa-bars` (`_header.html:12`), `fa-chevron-right` ×6, `fa-calendar` ×4, `fa-calendar-check-o` ×2, `fa-group` ×2, `fa-google` ×2 (brand, `account/login.html` and `signup.html`), `fa-check`, `fa-graduation-cap`, `fa-hands-helping`, `fa-fw` ×4 (fixed width), `glyphicon-check` ×3, `glyphicon-exclamation-sign` ×1. Find each with `git grep -n "fa-\|glyphicon" -- '*.html' '*.py'`.

**django-bootstrap3:** used only by `{% bootstrap_field %}` in `account/guardian/home.html:2,15-21` and `account/mentor/home.html:2,66`. It's at `settings.py:103` and `pyproject.toml:28`. Replace it with Django's `{{ field.as_field_group }}` (Django 5.0+) or a small `_field.html` partial that renders the same markup minus the Bootstrap classes.

**js-datepicker:** `welcome.html:8,79-104`. It's only a fallback where `<input type="date">` falls back to text, and every Baseline browser supports the date input. Delete it. The widget already sets `type="date"` (`forms.py:154,274`).

**Vendoring:** `coderdojochi/static/vendor/vendor.json` and `README.md`, and `tasks.py:195-231` (`invoke vendor`: npm tarball, sha512 check, transforms, reference check). `.pre-commit-config.yaml:1` excludes `^coderdojochi/static/vendor/`.

**Tests to copy:**
- `coderdojochi/tests/test_vendored_assets.py`: `_AssetCollector` `:53-82`, page rendering with staff, no-role and seeded orders `:98-175`, manifest `collectstatic` test `:189-204`. Its `:204` asserts `vendor/fontawesome5/css/all.min.css` and must change when FA5 is deleted.
- `coderdojochi/tests/test_security_settings.py:93-94`: comment about `cdc.js`.

**Smoke tooling (outside the repo, Ali's rule: code runs in `/tmp`):** `/tmp/wac-smoke/smoke.mjs` (public page list `:13-26`, viewports `:44-45`, `--cp9` host allowlist), `cp9-local.mjs` (runserver + `sessionid` cookies for logged-in pages), `cp9-charts.mjs`. `/tmp` can be wiped by a reboot. If the files are gone, rebuild them from the spec in "Proof".

**Dependency-upgrade plan (read for the release runbook, staging, prod and rollback):** `docs/plans/dependency-upgrades-2026-11.md` on PR https://github.com/WeAllCode/website/pull/1630 (branch `claude/dep-upgrades-cp3-9e6614`; not on `main` yet). Sections "How to run it" step 4 (runbook) and 5 (rollback), "Playwright smoke", "Pitfalls" (Cloudflare 60 s edge cache, serial console, 1 GB RAM), and "Checkpoint 9", whose allowlist still applies.

**modern-web-guidance:** run `npx -y modern-web-guidance@latest retrieve "<id>"` (set `NPM_CONFIG_CACHE=/tmp/npm-cache`). Read the guides each task names. Which guides apply:
- `css`: `@layer` order, `:where()`, no BEM, logical properties, `currentColor`.
- `css-layout` and `responsive-design`: flex vs grid, container queries.
- `navbar`: popover nav at narrow widths, `aria-current="page"`.
- `icons`: "Prefer embedding for a handful of core icons"; `aria-hidden` on decorative icons, a label on icon-only controls.
- `interest-triggered-tooltips`: hint vs toggletip, `role="tooltip"`, WCAG 1.4.13.
- `search-hidden-content`: `hidden="until-found"` for "See more".
- `html`: popover, `<details>`, focus.
- `forms`, `accessibility`, `responsive-table`, `progress`, `autofill-sign-in-form`.
- Baseline `legacy-scan` (2026-11-25, 6 findings): `autofill-sign-in-form` at `session_partner_password.html:37`; `progress` at `dashboard/admin.html:121`, `meeting_check_in.html:54`, `session_check_in_mentors.html:49`, `session_check_in.html:178` and `session_stats.html:23`.

## Design (fixed so that tasks can run in parallel)

### Cascade

Every new CSS file wraps its rules in one named layer. The first stylesheet link in each base is `layers.css`, which only declares the order:

```css
@layer legacy, reset, tokens, base, layout, components, pages, utilities;
```

During the migration (CP2 to CP4) the public base links `legacy.css`, which holds one line: `@import url("foundation.min.css") layer(legacy);`. Any layered rule beats an unlayered one, so the new CSS wins over Foundation on every page, and pages that haven't migrated keep Foundation for the classes they still use. `ManifestFilesMixin` rewrites `@import url()`, so hashing still works. `legacy.css` and Foundation are deleted in 4G.

`app.css` is **not** a legacy file. In CP2 its contents move, with their class names unchanged, into `brand.css` (`@layer components`, plus `pages` for its page-specific rules). Then `app.css` is deleted. Those names are ours, not Foundation's, so they stay.

### Files

- Public and app pages: `weallcode/static/weallcode/css/{layers,legacy,tokens,reset,base,layout,components,brand,utilities}.css`, plus one file per page that needs its own rules, `css/pages/<template-name>.css`, linked from that page's `{% block extra_style %}`.
- Dashboard: `layers.css`, `tokens.css`, `reset.css`, plus `coderdojochi/static/css/dashboard.css` (its own `base`, `layout` and `components` layers, with Bootstrap 3's look: 14 px base, Open Sans/Quicksand).
- JS: one ES module `weallcode/static/weallcode/js/site.js`, loaded with `<script type="module">`. `app.js` is deleted.
- Icons: `{% icon "<name>" %}` from a new `coderdojochi/templatetags/icons.py`. It inlines an SVG vendored from `@fortawesome/fontawesome-free` 7.x (`svgs/solid/*.svg`, `svgs/brands/google.svg`; CC BY 4.0, credited on `/credits/`) into `coderdojochi/static/vendor/fa-svgs/` through `vendor.json`. The tag adds `class="icon"`, `aria-hidden="true"` and `focusable="false"`. With `label="…"` it emits `role="img"` and `aria-label` instead. It is cached with `functools.lru_cache`, and an unknown name raises `TemplateSyntaxError` when `DEBUG` is on and renders nothing in prod. Name map: `bars`, `chevron-right`, `calendar`, `calendar-check` (was `fa-calendar-check-o`), `users` (was `fa-group`), `google`, `check`, `graduation-cap`, `handshake-angle` (was `fa-hands-helping`), `square-check` (was `glyphicon-check`), `circle-exclamation` (was `glyphicon-exclamation-sign`). `fa-fw` becomes CSS on `.icon` (`inline-size: 1.25em`).

### Class vocabulary

Rule: **no new class name may appear as a class selector in `foundation.min.css` or `vendor/bootstrap3/css/bootstrap.min.css`.** Task 2A writes the check (a `/tmp` script that lists the class selectors in our new CSS and greps the two legacy files). Run it in every checkpoint. If a page task needs a name that's missing, it reports to the lead. The lead adds the name to this table, and the core task's owner adds it in the next checkpoint (or the lead assigns a fix-up task). Page tasks never edit shared CSS.

| Today (Foundation / Bootstrap) | New | Owner |
|---|---|---|
| `grid-container` | `.wrap` | 2A `layout.css` |
| `grid-x` | `.cols` (flex row that wraps, as in Foundation XY) | 2A |
| `grid-margin-x` / `grid-margin-y` / `grid-padding-x` / `grid-padding-y` | `.cols.gutter-x` / `.gutter-y` / `.pad-x` / `.pad-y` | 2A |
| `cell` + `small-N` / `medium-N` / `large-N` | `.span-N` / `.md-span-N` / `.lg-span-N` (no class = full width, as `.cell` is) | 2A |
| `auto` / `shrink` / `medium-auto` | `.span-auto` / `.span-shrink` / `.md-span-auto` | 2A |
| `*-offset-N` | `.md-offset-N` / `.lg-offset-N` / `.offset-N` | 2A |
| `align-right` / `align-center` on `grid-x` | `.cols.end` / `.cols.center` | 2A |
| `margin-top-2`, `padding-vertical-3`, `margin-0`, `*-half` … | `.mt-2`, `.py-3`, `.m-0`, `.mt-h` … (`m`/`p` + `t`,`b`,`l`,`r`,`x`,`y` + `0`,`h`,`1`,`2`,`3`; `x`/`y` map to logical inline/block). Keep Foundation's values and `!important` | 2A `utilities.css` |
| `text-center`, `text-right`, `text-uppercase`, `font-bold`, `medium-text-left`, `large-text-center` … | `.t-center`, `.t-end`, `.t-upper`, `.t-bold`, `.md-t-start`, `.lg-t-center` … | 2A |
| `hide` | native `hidden` attribute | — |
| `show-for-sr` / `sr-only` | `.visually-hidden` | 2A |
| `show-on-focus` (skip link) | `.skip-link` | 2A |
| `show-for-medium` / `show-for-large` / `hide-for-medium` | `.md-up` / `.lg-up` / `.sm-only` | 2A |
| `width-100` / `width-50` / `width-25`, `display-inline-block`, `position-relative` | `.w-100` / `.w-50` / `.w-25`, `.inline-block`, `.relative` (check whether these are Foundation or `app.css` first; `app.css` names stay) | 2A |
| `button` + `secondary`/`tertiary`/`large`/`small`/`expanded`/`button-danger`/`disabled` | `.cta` + `.cta-secondary` / `.cta-tertiary` / `.cta-large` / `.cta-small` / `.cta-block` / `.cta-danger`; disabled = the `disabled` attribute, or `aria-disabled="true"` on links | 2B `components.css` |
| `menu` / `menu.align-right` / `vertical` | `.nav-list` / `.nav-list.end` / `.nav-list.nav-list-stack` (`stack`, `column`, `vertical` are Foundation classes) | 2B |
| `callout` + `alert`/`success`/`warning`/`primary` | `.notice` + `.notice-alert` / `-success` / `-warning` / `-info` (`role="status"`, or `alert` for errors) | 2B |
| `breadcrumbs` | `.crumbs` (a `<nav aria-label="Breadcrumb">` with `<ol>`) | 2B |
| `flex-video widescreen` | `.video` (`aspect-ratio: 16 / 9`) | 2B |
| Foundation `table`, form, label and input element styles | element rules in `base.css` (no classes) | 2A |
| `fa` / `fas` / `glyphicon` | `{% icon %}`, sized by `.icon` | 2B (`.icon` CSS), 2D (tag) |
| hints and popovers | `.hint` (popover) and `.toggletip` | 2B |
| Dashboard `navbar*`, `panel*`, `table-striped`, `table-condensed`, `badge`, `progress*`, `row`/`col-sm-*`, `pull-right`, `hidden-xs`/`hidden-sm`, `container(-fluid)`, `vert-align` | `.dash-nav`, `.dash-panel`, `.striped`, `.dense`, `.count`, native `<progress>`, `.cols` + `.sm-span-N` (dashboard breakpoint 48em = Bootstrap `sm`), `.float-end`, `.md-up`, `.wrap`/`.wrap-fluid`, `.v-middle` | 5A `dashboard.css` |

Breakpoints (literal values, because custom properties don't work in media queries): Foundation `medium` 40em, `large` 64em, `xlarge` 75em. Bootstrap `sm` 48em (768 px), `md` 62em (992 px). Check each value against the legacy CSS before using it.

### Interaction patterns

- **Mobile nav** (`navbar` guide): a `<button popovertarget="site-nav" aria-label="Menu">` with `{% icon "bars" %}`, and the nav list as `popover` at narrow widths. At ≥ 40em it shows inline (popover attribute neutralised with CSS as in the guide). Its open state looks like today's (in flow under the header). The current link gets `aria-current="page"` (`active_link` already adds a class; add the attribute next to it). No JS.
- **"See more" on `/team/`** (`search-hidden-content`): the extra members get `hidden="until-found"`, and a `<button aria-expanded="false" aria-controls="…">` reveals them. `site.js` handles `[data-reveal-target]` buttons and the `beforematch` event, so Find-in-page reveals the members too. Where `until-found` isn't supported it behaves as plain `hidden`, which is fine.
- **Dashboard row Show/Hide and navbar collapse:** the same `site.js` disclosure handler (`hidden` + `aria-expanded`) for the rows. The `navbar` popover pattern for the navbar.
- **Hints** (`interest-triggered-tooltips`):
  - Meeting "Announce" becomes a **toggletip**: `<button popovertarget>` with `aria-expanded` kept in sync, and a popover holding the confirm link. It is placed under the button with anchor positioning in `@supports (anchor-name: --a)`, and centred by default otherwise.
  - The background-check hint and the gender-limit hint are a `popover="hint"` + `interestfor` hint with `role="tooltip"` and `aria-describedby`, used only when `HTMLButtonElement.prototype.hasOwnProperty("interestForElement")` (or the guide's detection). Otherwise the hint text is not shown, which is today's behaviour. **The disabled sign-up button can't take interest**, so put the hint trigger on a wrapper, or show the gender message as inline text (the guide's "Inline content" case). If inline text changes the screenshot by ≥ 1 %, report it to Ali.

## Tasks

Each task lists: files (owned exclusively within its checkpoint) · what to change · copy from · pitfalls · proof. "Lead" means the lead does it, not a sub-agent.

### Checkpoint 1: Safety net and removals with no visual change (PR 1)

Run 1A–1E in parallel. Their files don't overlap.

**1A. A/B, interaction and bytes tool.** Files: `/tmp/wac-smoke/ab.mjs` (new), `/tmp/wac-smoke/package.json` (add `pixelmatch` and `pngjs`, latest versions at least 14 days old), `/tmp/wac-ab/seed.sh` (new).
- `seed.sh <dir>`: creates `<dir>/main` as `git worktree add --detach <dir>/main origin/main` and `uv sync` there, and `<dir>/db.sqlite3` through `DATABASE_URL=sqlite:///<dir>/db.sqlite3 manage.py migrate && loaddata fixtures/*.json`. If the fixtures don't load on sqlite, seed with `coderdojochi/factories.py` as CP9 did (record which in Progress). Then it creates 4 users (staff, guardian, mentor, no-role) and prints a `sessionid` for each, made with `SessionStore` and `cdc-admin`-style login (copy `cp9-local.mjs`). Both servers use **the same DB file** and `DEBUG=True`, with `runserver` on :8001 (main) and :8000 (branch).
- `ab.mjs --a http://127.0.0.1:8001 --b http://127.0.0.1:8000 --cp <label> --sessions <json> [--interact] [--only <path>]`. For each page in the A/B page list and each viewport (desktop 1280×800, mobile 390×844 `isMobile`), load A then B with `waitUntil: 'networkidle'`. Then `document.fonts.ready`, and disable animations (`page.emulateMedia({ reducedMotion: 'reduce' })` plus a `*{transition:none!important;animation:none!important;caret-color:transparent!important}` style). Take full-page screenshots. Mask these by painting them a solid colour before the screenshot: `iframe` (donation widget, YouTube, reCAPTCHA), `img[src*="gravatar"]`, `[data-ab-mask]`, the CSRF-token-dependent nothing (none visible). Diff with pixelmatch (`threshold: 0.1`). If the heights differ, the diff fails with the height delta. Write `out/<cp>/{a,b,diff}/<vp>-<slug>.png` and `out/<cp>/report.json` (per page: diff %, bytes by type for A and B, console errors, failed requests). Exit 1 if any page is ≥ 1 %, has B bytes ≥ A bytes, or has a console error or failed request in B that A doesn't have.
- `--interact` (B only) runs these named checks and fails on any miss:
  - `nav-open-click` / `nav-open-keyboard` (Tab to the trigger, Enter; Escape closes and focus returns) / `nav-tap` (mobile).
  - `team-see-more` (click: the hidden members become visible and `aria-expanded="true"`).
  - `dash-nav` (mobile `/admin/`), `dash-rows` (`/admin/` Show/Hide).
  - `hint-announce` (staff, meeting detail: the button opens the popover, which shows a link to `/…/announce/`; Escape closes it).
  - `hint-bgcheck` and `hint-gender`: when interest invokers are supported, hover and focus show the `role=tooltip` element; otherwise assert the trigger works and nothing throws.
  - Until a checkpoint migrates a page, its check runs against the old markup or is skipped. The report says which.
- **A/B page list.** Public: `/`, `/our-story/`, `/programs/`, `/programs/summer-camps/`, `/team/`, `/join-us/`, `/associate-board/` (check the URL), `/credits/`, `/privacy/`, `/account/login/`, `/account/signup/`, `/account/password/reset/`, a 404 path, and `/500/` (DEBUG URL, `coderdojochi/urls.py`). Guardian: `/account/`, a session detail and a session sign-up. Mentor: `/account/`, a session detail and sign-up, a meeting detail and sign-up, `/meetings/`, the mentor list and one mentor detail. No-role: `/welcome/`. Staff: `/admin/`, a session's stats, check-in, mentor check-in and donations, a meeting check-in, a meeting detail, and a student detail. Others: `unsubscribe` and `session_partner_password` if their URLs can be reached with the fixtures. Record in Progress any page that can't be reached, and why.
- Proof: run `ab.mjs` with A = B = :8001 (both main): every page 0.000 %, exit 0. Then patch the branch server's `app.css` locally (`body{font-size:17px}` in the :8000 tree only; undo with the exact reverse edit): exit 1, with the diffs reported. Paste both summaries into Progress.

**1B. Delete dead front-end code.** Files (delete each, **after proving it dead**: `git grep` for its name in `*.py`, `*.html` and `*.txt`, and for templates, check every `template_name`, `render(` and CBV default name; paste the grep into the report): `coderdojochi/static/css/cdc.css`, `coderdojochi/static/js/cdc.js`, `coderdojochi/templates/home.html`, `volunteer.html`, `sessions.html`, `contact.html`, `_messages.html` (the `coderdojochi/` one, not `weallcode/_messages.html`), `weallcode/templates/weallcode/contact.html`, `weallcode/templates/weallcode/snippets/card.html`, `coderdojochi/templates/admin/filter.html` (Django admin may load it by convention: check for a `ModelAdmin` that sets `filter` templates or for `list_filter` overrides before deleting), and the unrouted `home` and `volunteer` functions in `coderdojochi/old_views.py:49-75` (check `urls.py:279` and the rest first). Also `coderdojochi/tests/test_security_settings.py:93`: change the comment so it no longer names `cdc.js` (keep the assertion; see Pitfalls).
- Pitfalls: `coderdojochi/mentor_list.html` and `mentor_detail.html` **are live** (`MentorListView`/`MentorDetailView` default names). The `account/*` and `socialaccount/*` templates and `400`/`403`/`403_csrf`/`404.html` are loaded by convention. Don't delete them.
- Proof: the full test suite passes. `git grep -n "cdc\.js\|cdc\.css"` finds only the `settings.py:61` comment (1D's file). The A/B run is unchanged.

**1C. Drop js-datepicker.** Files: `coderdojochi/templates/welcome.html` (delete `:8` and `:79-104`; keep the `{% block extra_script %}` if anything else is in it), `coderdojochi/static/vendor/vendor.json` (remove the `js-datepicker` entry), `coderdojochi/static/vendor/README.md` (its line), and `coderdojochi/static/vendor/js-datepicker/` (delete).
- Proof: `uv run invoke vendor` reports 0 files written and leaves `git status --porcelain coderdojochi/static/vendor` empty apart from the deletions. On `/welcome/`, `#id_birthday` is `type="date"` (assert in 1E).

**1D. Drop django-bootstrap3.** Files: `accounts/templates/account/guardian/home.html`, `accounts/templates/account/mentor/home.html` (only `:2` `{% load %}` and the `{% bootstrap_field %}` lines), new `accounts/templates/account/_field.html` if needed, `coderdojochi/settings.py` (`:103` remove `"bootstrap3"`; `:61` reword the comment: CSRF cookie stays readable; revisit now that `cdc.js` is gone), `pyproject.toml:28`, `uv.lock` (`uv remove django-bootstrap3`, never a bare `uv lock --upgrade`).
- Copy: Django's `{{ field.as_field_group }}` (https://docs.djangoproject.com/en/5.2/topics/forms/#reusable-field-group-templates). Before writing, render one `bootstrap_field` in a Django shell and copy the outer wrapper, label, help-text and error markup it produces, minus the Bootstrap-only classes, so Foundation styles it the same.
- Pitfall: Python dependency change, so runbook step 0 (migration check) applies. `bootstrap3` has no models; record "no planned operations".
- Proof: A/B for guardian and mentor `/account/` < 1 %, including the form with a validation error (submit an empty required field in `ab.mjs --only /account/ --post-invalid`; add that flag in 1A or do it by hand and record it). `uv run python -c "import bootstrap3"` fails.

**1E. Guard tests.** File: new `coderdojochi/tests/test_frontend_stack.py`.
- `LegacyRatchetTest`:
  - A module constant `LEGACY_TEMPLATES` lists every template (path relative to the repo) that still contains a legacy token. Compute it at 933ac62 minus 1B's deletions.
  - Legacy-token regex: class tokens `grid-x|grid-container|cell|(small|medium|large)-\d+|(small|medium|large)-offset-\d+|margin-[a-z-]+\d|padding-[a-z-]+\d|callout|button|menu|show-for-sr|hide|col-(xs|sm|md|lg)-\d+|navbar[a-z-]*|panel[a-z-]*|glyphicon[a-z-]*|fa|fas|far|fab|fa-[a-z-]+`, plus attributes `data-toggle|data-target|data-dismiss|data-ride|data-toggler`. Match within `class="…"` values, and as `data-` attributes.
  - Test 1: no template outside `LEGACY_TEMPLATES` matches.
  - Test 2: every template in `LEGACY_TEMPLATES` still exists and still matches, so the list must shrink as pages migrate. Each later checkpoint removes its files from the set.
  - Scan `weallcode/templates`, `coderdojochi/templates` and `accounts/templates`, excluding `emailtemplates` and `account/email/`. Also scan `coderdojochi/templatetags/*.py` and `coderdojochi/forms.py` (string literals) with the same regex, and list them in the set too.
- `RemovedLibrariesTest`: renders the pages `test_vendored_assets.py` renders (copy its setUp, `:98-175`). Asserts that no asset URL matches the libraries removed so far, kept in `REMOVED = ["js-datepicker"]` (later checkpoints append), that `bootstrap3` is not in `INSTALLED_APPS`, and that `/welcome/`'s birthday input is `type="date"`.
- `DeadFilesTest`: asserts that each path deleted in 1B doesn't exist.
- Mutations (do each, confirm the failure, undo with the exact reverse edit):
  - Add `class="callout"` to a non-legacy template (e.g. `weallcode/_messages.html` if CP2 has migrated it; in CP1 use a new throwaway template, created and deleted) → Test 1 fails.
  - Add `"bootstrap3"` back to `INSTALLED_APPS` → fails.
  - Recreate an empty `cdc.js` → `DeadFilesTest` fails.
- Proof: the full suite passes.

Lead, after 1A–1E: the whole-build commands, and an A/B run of main vs the branch (all pages < 1 %; most should be 0.000 %). Run `legacy-scan` and record the count in Progress.

### Checkpoint 2: New CSS core, shared chrome, no jQuery or Foundation JS (PR 2)

2A, 2B, 2C and 2D run in parallel. 2E runs in parallel too: it uses the vocabulary above and the tag name, not the files.

**2A. Tokens, reset, base, layout, utilities.** Files: `weallcode/static/weallcode/css/{layers,legacy,tokens,reset,base,layout,utilities}.css` (new), and `/tmp/wac-smoke/classcheck.mjs` (new: the no-collision check).
- `tokens.css` (`@layer tokens`): `app.css:1-25` brand colours and fonts, with the same names. Spacing scale from Foundation's utilities. Gutters: Foundation's 20 px small and 30 px medium; read the real values in `foundation.css` around `.grid-margin-x`.
- `reset.css`: what Foundation's normalize and base actually do, as the current pages depend on it (box-sizing, margins, `img{max-inline-size:100%}`…). Copy the values, don't reinvent them.
- `base.css`: `html{scroll-behavior:smooth}` (`app.css:29`). Body, heading (with the medium-breakpoint step-ups at `foundation.css:284`), paragraph, link, list, table, form, label and input element styles, matching Foundation's computed values. Use `:focus-visible` for focus rings (no what-input).
- `layout.css` and `utilities.css`: the vocabulary table. `.cols` must reproduce Foundation XY geometry exactly: flex, negative-margin gutters or `gap` with matching width maths. Prove it with A/B, not by eye.
- Guides: `css`, `css-layout`, `responsive-design`, `accessibility` (skip link, `.visually-hidden`).
- Proof: `classcheck.mjs` exits 0. The A/B run after 2E is < 1 % on every page.

**2B. Components.** Files: `weallcode/static/weallcode/css/components.css` (new).
- `.cta*`, `.nav-list`, `.notice*`, `.crumbs`, `.video`, `.icon` (`inline-size:1em; block-size:1em; fill:currentColor; vertical-align:-0.125em`, and the `fa-fw` width rule; match FA5's metrics), `.hint`, `.toggletip`, and the mobile nav popover styles. Copy the button, callout, menu and breadcrumb values from `foundation.css`.
- Guides: `css`, `navbar`, `interest-triggered-tooltips`, `icons`, `html`.
- Pitfall: style `:popover-open` and anchor positioning only inside `@supports`. No polyfill classes.
- Proof: `classcheck.mjs` exits 0. A/B as in 2A.

**2C. app.css → brand.css.** Files: `weallcode/static/weallcode/css/brand.css` (new), `weallcode/static/weallcode/css/app.css` (delete).
- Move every rule. Rules that style site classes go in `@layer components`. Rules that target one page's structure go in `@layer pages`. Media queries stay with their rules (use nesting). Drop `:1-25` (now in `tokens.css`) and `:29` (now in `base.css`).
- Pitfall: `app.css` was unlayered, so it beat Foundation. Now it's layered above `legacy`, so it still beats Foundation. Check every `!important` in it.
- Proof: A/B < 1 %.

**2D. Icon tag and SVGs.** Files: `coderdojochi/templatetags/icons.py` (new), `coderdojochi/static/vendor/vendor.json` (add `@fortawesome/fontawesome-free` 7.x, latest at least 14 days old, with only the SVGs in the name map plus LICENSE.txt, to `vendor/fa-svgs/{solid,brands}/`), `coderdojochi/static/vendor/README.md` (one line), `coderdojochi/static/vendor/fa-svgs/**` (generated by `uv run invoke vendor`), `coderdojochi/tests/test_icons.py` (new).
- The tag reads the file through `django.contrib.staticfiles.finders.find`, strips the leading `<!-- … -->` licence comment (FA puts one in each SVG; the licence ships as LICENSE.txt and on `/credits/`), and returns `mark_safe` of the parsed SVG with the attributes from "Design". Only names in a fixed allowlist dict are accepted, never a path from the template.
- Tests: the rendered output has `aria-hidden="true"`; `label="Menu"` gives `role="img" aria-label="Menu"`; an unknown name raises under `DEBUG`. Mutation: drop `aria-hidden` from the tag → test fails.
- Pitfall: `invoke vendor`'s reference check scans CSS and JS only, so SVGs pass. `vendor/fontawesome5` stays until 4G.
- Proof: tests pass. `invoke vendor` second run: 0 written.

**2E. Shared chrome and JS.** Files:
- `weallcode/templates/weallcode/_base.html`: links in this order: `layers.css`, `legacy.css`, `tokens`, `reset`, `base`, `layout`, `components`, `brand`, `utilities`, then `{% block extra_style %}`. Keep FA5 until 4G. Remove jQuery, what-input, Foundation JS and `app.js`; add `<script type="module" src="{% static 'weallcode/js/site.js' %}">`. Skip link becomes `.skip-link`. Drop `class="no-js"` on `<head>` (it's on the wrong element and nothing reads it).
- `weallcode/templates/weallcode/_header.html`: popover nav per "Design".
- `weallcode/templates/weallcode/_footer.html`.
- `weallcode/templates/weallcode/_messages.html`: `.notice`.
- `weallcode/static/weallcode/js/site.js` (new).
- `weallcode/static/weallcode/js/app.js` (delete).
- `weallcode/templates/weallcode/team.html`: only `:150`, `:192` and the elements they toggle (`.mentor-toggle`, `.volunteer-toggle`), changed to the reveal pattern. The rest of the page is 3D's.
- Remove these templates from `LEGACY_TEMPLATES` in `test_frontend_stack.py` (only the 4 chrome partials; the lead edits that test file at the end of the checkpoint, not 2E). Append `jquery`, `what-input` and `foundation.min.js` to `REMOVED` (lead).
- Copy: the guides `navbar`, `search-hidden-content` and `accessibility`. `donsPlus.openWidget()` links stay as they are, because the widget needs them.
- Pitfall: the donation widget may expect jQuery. Check on `/` after the change that `donsPlus.openWidget()` opens it (A/B shows no console error; click it by hand once and record the result).
- Proof: `ab.mjs --interact` `nav-*` and `team-see-more` pass. A/B < 1 % on every page. `window.jQuery === undefined` on every public page (add to `ab.mjs`).

Lead, after 2A–2E: edit `test_frontend_stack.py` (ratchet set and `REMOVED`), run `classcheck.mjs`, `legacy-scan` and the whole-build commands, and the full A/B with `--interact`.

### Checkpoint 3: Public pages (PR 3)

3A–3F run in parallel, one page group each. Each task: change every Foundation class to the vocabulary, drop the classes with no effect, `fa-*` → `{% icon %}`, `hide` → `hidden`, and put page-only rules in `css/pages/<name>.css` (new, owned by that task). Then remove its templates from `LEGACY_TEMPLATES` (report the lines; the lead edits the test). If a needed class is missing from the vocabulary, report it; don't add it to shared CSS.

- **3A** `weallcode/templates/weallcode/home.html`, `css/pages/home.css`
- **3B** `our_story.html`, `css/pages/our_story.css`
- **3C** `programs.html`, `programs_summer_camps.html`, `snippets/class.html`, `css/pages/programs.css`
- **3D** `team.html` (rest of it), `snippets/team_member.html`, `css/pages/team.css`
- **3E** `join_us.html`, `associate_board.html`, `css/pages/join_us.css`
- **3F** `credits.html` (add the Font Awesome Free CC BY 4.0 credit), `privacy.html`, `snippets/hero_image.html`, `snippets/poster.html`, `snippets/posters.html`, `_svgs.html` (`class="hide"` → `hidden`; `aria-hidden="true"` on the sprite `<svg>`)
- Guides: `css-layout`, `responsive-design`, `icons`, `html`, `accessibility`, `forms` (the join-us and associate-board forms; keep the field names and reCAPTCHA as they are).
- Proof (each task): `ab.mjs --only <its paths>` < 1 % on both viewports; the ratchet test passes with its files removed.

Lead: the full A/B (every page, since shared CSS loads everywhere), `classcheck.mjs`, `legacy-scan` and the whole-build commands.

### Checkpoint 4: Account and app pages, hints fixed, Foundation and FA5 removed (PR 4)

4A–4F run in parallel. 4G runs after them (it needs every template migrated).

- **4A** `accounts/templates/account/{_base,login,signup,logout,password_change,password_reset,password_reset_done,password_reset_from_key,password_reset_from_key_done,password_set,email,email_confirm,email_confirmed,account_inactive,signup_closed,verification_sent,verified_email_required}.html`, `account/snippets/already_logged_in.html`, `accounts/templates/socialaccount/*.html` (not `email/`). `autocomplete` on password inputs per `autofill-sign-in-form`. Guides: `forms`, `autofill-sign-in-form`.
- **4B** `account/guardian/home.html`, `account/mentor/home.html`, `account/_field.html` (from 1D). Background-check hint per "Design". Guides: `forms`, `interest-triggered-tooltips`.
- **4C** `coderdojochi/templates/{guardian,mentor,public}/session_detail.html`, `{guardian,mentor}/session_sign_up.html`, `session_partner_password.html` (`glyphicon-exclamation-sign` → `{% icon "circle-exclamation" %}`; `autocomplete`, which fixes the `legacy-scan` finding), `coderdojochi/templatetags/coderdojochi_extras.py` (`:110-125`: `class='button small …'` → `cta cta-small`, gender hint per "Design"; it builds HTML with f-strings, so escape `message` and `title` with `format_html`, because today they're interpolated raw). Guides: `interest-triggered-tooltips`, `autofill-sign-in-form`.
- **4D** `meetings.html`, `meeting_detail.html` (Announce toggletip), `meeting_sign_up.html`, `student_detail.html`, `unsubscribe.html`, `welcome.html`, `coderdojochi/mentor_list.html`, `coderdojochi/mentor_detail.html`, `coderdojochi/forms.py` (drop `form-control` and `btn*` from widget attrs; `js-expand-student-form` spans: find what reads them; if nothing does, delete them). Guides: `interest-triggered-tooltips`, `html`, `forms`.
- **4E** `400.html`, `403.html`, `403_csrf.html`, `404.html`, `500.html` (keep the Sentry bundle and init as they are), `dashboard/session_stats.html` (Foundation base; its 5 `progress` findings: native `<progress>` per the `progress` guide; Chart.js code unchanged).
- **4F** `css/pages/*.css` for any 4A–4E page that needs one: each task owns `css/pages/<its first template name>.css`. Listed here so no two tasks pick the same file.
- **4G (after 4A–4F).** Files: `weallcode/templates/weallcode/_base.html` (drop the `legacy.css` and FA5 links), delete `weallcode/static/weallcode/css/{legacy.css,foundation.min.css,foundation.css}`, delete `coderdojochi/static/vendor/{jquery,what-input,foundation,fontawesome5}/`, `vendor.json` (remove the 4 entries; **keep `jquery` if the dashboard still needs it: it does until CP5**, so remove only `what-input`, `foundation-sites` and `@fortawesome/fontawesome-free@5`, and keep jQuery for `_admin_base`), `vendor/README.md`, `coderdojochi/tests/test_vendored_assets.py:204` (assert `vendor/chartjs/chart.umd.min.js` and `weallcode/css/layers.css` instead), `layers.css` (drop `legacy` from the order).
- Lead: `LEGACY_TEMPLATES` loses every Foundation-base template; `REMOVED` gains `foundation`, `fontawesome5`, `what-input`; extend `DeadFilesTest` with the deleted CSS.
- Proof: A/B < 1 % on every page, `--interact` `hint-*` pass, `legacy-scan` = only the 4 dashboard `progress` findings, `invoke vendor` 0 written, `collectstatic` manifest test passes, the whole-build commands.

### Checkpoint 5: Dashboard (PR 5)

5A–5D run in parallel. The include name `dashboard/_nav.html` and the `dashboard.css` vocabulary are fixed above.

- **5A** `coderdojochi/templates/dashboard/_admin_base.html` (links: `layers.css`, `tokens.css`, `reset.css`, `dashboard.css`, fonts; remove FA4, Bootstrap CSS/JS and jQuery; add `site.js`), `coderdojochi/templates/_topnav.html`, `coderdojochi/templates/_messages_bootstrap.html` (rename it to `dashboard/_messages.html` and update `_admin_base` to match), `coderdojochi/templates/dashboard/_nav.html` (new: the navbar each dashboard page copies today, one partial with a `{% block %}`-free include and an `active` variable), `coderdojochi/static/css/dashboard.css` (new). Copy the Bootstrap 3.4.1 values from `vendor/bootstrap3/css/bootstrap.min.css` (pretty-print it in `/tmp`). Guides: `css`, `navbar`, `responsive-table`, `progress`.
- **5B** `dashboard/admin.html`: nav → include, collapse rows → reveal pattern (`hidden` + `aria-expanded`), `glyphicon-check` → icon, `progress` → `<progress>`, `fa-calendar-check-o` → icon.
- **5C** `dashboard/session_check_in.html`, `dashboard/session_check_in_mentors.html`.
- **5D** `dashboard/meeting_check_in.html`, `dashboard/session_donations.html`.
- **5E (after 5A–5D).** Delete `coderdojochi/static/vendor/{jquery,bootstrap3,fontawesome4}/` and their `vendor.json` and README entries. The lead empties `LEGACY_TEMPLATES` and turns `LegacyRatchetTest` into a plain "no template matches" test, and `REMOVED` gains `jquery`, `bootstrap`, `font-awesome`, `glyphicons`.
- Proof: A/B < 1 % on every staff page, `--interact` `dash-*` pass, `legacy-scan` 0 findings, `git grep -n "jquery\|bootstrap\|foundation\|font-awesome\|fontawesome[45]\|what-input\|datepicker\|glyphicon" -- ':!docs' ':!*.lock'` finds nothing outside the guard tests, and the whole-build commands.

## Checkpoints

| CP | PR title | Check that proves it | Delivers |
|---|---|---|---|
| 1 | Front-end safety net; drop dead code, js-datepicker, django-bootstrap3 | `ab.mjs` main vs branch < 1 %; guard tests pass; mutations fail | A/B harness, ratchet, 2 deps gone |
| 2 | Modern CSS core and site chrome; no jQuery/Foundation JS | `ab.mjs --interact` nav and team; `classcheck`; `jQuery` undefined on public pages | Public JS stack gone; layered CSS |
| 3 | Public pages on the new CSS | Full A/B < 1 %; ratchet shrinks | Public site off Foundation classes |
| 4 | Account and app pages; hints fixed; Foundation and FA5 deleted | Full A/B; `hint-*`; manifest test; `legacy-scan` ≤ 4 | Foundation, FA5, what-input gone; Announce works |
| 5 | Dashboard on dashboard.css; Bootstrap, FA4 and jQuery deleted | A/B staff pages; `dash-*`; `legacy-scan` 0; grep clean | All acceptance criteria met |

Order: 1 → 2 → 3 → 4 → 5. Each one is released to prod before the next starts, so a visual bug points at one PR.

## How to run it

Read the whole plan first. Run it as the lead: **you write no code.**

1. At the start of each checkpoint, give every task that can run in parallel to its own sub-agent, all at once. Each brief names its task, its files and only those, the guides to retrieve, the bar to meet (the task's Proof line), and the report format: files changed; commands run with their last 20 lines; classes it needed but didn't find in the vocabulary; anything that didn't match the plan. Tell it **not to run git** and not to edit files outside its list.
   **Models (Ali, 2026-11-26, from CP3 on):** start every sub-agent with `model: "sonnet"`. If a task fails its Proof line or its result doesn't hold up when the lead checks the files, re-run that task on Opus with the failure in the brief.
2. You alone: check the actual files (not the report), edit `test_frontend_stack.py`, run the checkpoint's checks, commit, and write the result and the evidence (A/B summary line per page that was > 0 %, `legacy-scan` count, test counts) into Progress.
3. Anything not in the plan (a missing class, a page that can't be reached, a design change) goes into the plan first, then gets built.
4. Per PR, the release runbook from `docs/plans/dependency-upgrades-2026-11.md` "How to run it" step 4. Every step that needs Ali waits for his explicit OK in this session. Never push, merge or release on your own:
   - Branch `claude/frontend-cpN-<slug>` from the latest `origin/main`.
   - Ask Ali to push and open the PR. The body ends with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`, and commits end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Wait for CI to go green.
   - Ali runs `infra/vm/release.sh --target staging <branch>`.
   - Run `smoke.mjs --cp9` against staging (public pages; host allowlist unchanged). Before CP5, ask Ali whether to recreate `upg-smoke` for a logged-in staging pass. The local A/B already covers logged-in pages.
   - Ali merges. Record the previous prod sha. Only CP1 changes Python deps, and no checkpoint adds migrations.
   - Ali runs `release.sh --target prod`. Run the prod smoke past the 60 s Cloudflare edge TTL and watch Sentry for an hour.
5. Rollback: `infra/vm/release.sh --target prod --force <previous-prod-sha>`. Nothing in this plan migrates the DB.
6. After each checkpoint, if your context window is half full, write which checkpoint is next in Progress and stop. A fresh session continues from this plan.

## Proof

### Per acceptance criterion

| # | Test | One-line change that must make it fail |
|---|---|---|
| 1 | `test_frontend_stack.RemovedLibrariesTest` + `DeadFilesTest`; the CP5 grep | Put `<script src="{% static 'vendor/jquery/jquery.min.js' %}"></script>` back in `_base.html` → asset test fails |
| 1 | `bootstrap3` not installed | Add `"bootstrap3"` to `INSTALLED_APPS` → fails |
| 2 | `ab.mjs` main vs branch, every page × 2 viewports < 1 % | In `base.css` change the body `font-size` by 1 px → many pages ≥ 1 %, exit 1 |
| 3 | `ab.mjs --interact` named checks | Remove `popovertarget` from the nav button → `nav-open-*` fail; remove the `beforematch`/click handler in `site.js` → `team-see-more` fails |
| 4 | `ab.mjs` bytes, B < A per page | Add `<script src="{% static 'vendor/chartjs/chart.umd.min.js' %}">` to `_base.html` → public pages fail |
| 5 | Full test suite; `ab.mjs` console and failed-request diff | Add `undefinedFn();` at the top of `site.js` → console error on every page, exit 1 |
| 6 | `DeadFilesTest` | Recreate an empty `coderdojochi/static/js/cdc.js` → fails |
| 7 | `legacy-scan` count in Progress (6 → 6 → 6 → ≤ 4 → 0); review checklist per task | — (process; the review step in "How to run it" checks the guide ids against the diff) |

When a test is written: make its one-line change, confirm it fails, then undo it with the exact reverse edit. Never `git checkout` or reset to undo.

### Whole-build commands (every checkpoint)

```bash
uv run ruff check . && uv run ruff format --check .
```

```bash
DJANGO_SETTINGS_MODULE=coderdojochi.test_settings uv run python manage.py test coderdojochi.tests accounts weallcode
```

```bash
uv run pre-commit run --all-files
```

```bash
uv run invoke vendor
```

```bash
node /tmp/wac-smoke/classcheck.mjs
```

```bash
NPM_CONFIG_CACHE=/tmp/npm-cache npx -y modern-web-guidance@latest legacy-scan <copy of templates + weallcode/static/weallcode + coderdojochi/static/css> --json
```

`legacy-scan` must not scan `vendor/`. Copy the sources into `/tmp/wac-lscan/src` as on 2026-11-25. Then run the A/B:

```bash
node /tmp/wac-smoke/ab.mjs --a http://127.0.0.1:8001 --b http://127.0.0.1:8000 --cp <cp> --sessions /tmp/wac-ab/sessions.json --interact
```

### Manual

- Before each PR: open `/` at 390 px in a real browser, open the nav with touch emulation and by keyboard, and click Donate (the donation widget opens).
- CP4, on prod after the release: Ali (staff) opens a meeting that hasn't been announced and checks that "Announce" shows the confirm link. **Never click the link**: it emails every mentor. Close the popover with Escape.
- CP5, on prod: Ali opens `/admin/`, toggles Show/Hide and opens the mobile nav.
- Before calling the plan done: use prod through Cloudflare as a visitor, as a guardian or mentor, and as staff, and confirm that normal use still works.

## Pitfalls

- **Layer maths.** Any layered rule beats an unlayered one, and for `!important` the lowest layer wins. Foundation's `!important` utilities (`.hide`, spacing) in `legacy` still beat everything on elements that keep those classes. That's why migrated templates must drop **all** Foundation classes, not some of them.
- **`app.css` was unlayered.** Once it moves into a layer, anything in it that used to beat Foundation must still sit above `legacy` (it does), and anything that relied on beating new code doesn't exist yet. A/B catches the rest.
- **Classes that do nothing.** Many Bootstrap names on Foundation pages are unstyled today. Removing them is correct. Styling them would change the look.
- **Pixel A/B noise.** Fonts must have finished loading (`document.fonts.ready`), images must be decoded, and both servers must use the same DB at the same minute, because pages list upcoming sessions relative to now. If a page is ≥ 1 % only because of masked or dynamic content, add a `data-ab-mask` in the template only if Ali agrees. Otherwise fix the mask list in `ab.mjs`.
- **Popover nav at ≥ 40em:** a `popover` element is hidden by the UA stylesheet until it's opened. The wide layout must override it as the `navbar` guide shows, or the desktop nav vanishes.
- **`hidden="until-found"`:** never put `display` or `visibility` on that element (`search-hidden-content`).
- **Donation widget** (`embed.donsplus.com`): third-party, may assume globals. Check it after CP2.
- **Manifest storage:** every `url()` and `@import` in the new CSS must point at a file that exists, or `collectstatic` fails on deploy. The manifest test runs in CI.
- **`CSRF_COOKIE_HTTPONLY`** stays `False` in this plan. With `cdc.js` gone, check whether any JS still reads the cookie (`account/email.html:61-70` doesn't). Flipping it to `True` is a follow-up with its own test change (`test_security_settings.py:94`).
- **Cloudflare** caches logged-out HTML for 60 s. Smoke past that, or use a `sessionid=x` cookie to reach origin.
- **`/tmp` is volatile.** The A/B tool's spec is in 1A. Rebuild it if it's gone.

## Plan review findings

Fresh review sub-agent, 2026-11-25: 22 findings, 5 of them blockers. The lead spot-checked them: 12 `bootstrap_form`/`buttons` uses confirmed, and `origin/main` = `6c1c1a20` confirmed. Finding 16 is partly wrong: `/tmp/wac-smoke/smoke.mjs` and `package.json` still exist (2026-11-25). **Every row below overrides the plan text above.** Fold each into its task's brief.

| # | Sev | Where | Change to the plan |
|---|---|---|---|
| 1 | major | Cascade, 2C, vocabulary | `app.css` reuses Foundation names: `.button` (`:178-190`), `.menu`/`.main-menu a.button` (`:566-577`), `.reveal`, `.reveal-overlay`, `.input-group-label`, `.active`, and its own `.margin-*-half`/`.padding-*-half` (`:120-170`). 2C rewrites those selectors to the new names (`.cta`, `.cta-tertiary`, `.nav-list`) and drops the `*-half` rules (2A owns `.mt-h`). `classcheck` exempts only `app.css` names that don't exist in Foundation. |
| 2 | major | 2C, 2E | `app.css:566,637,674` use `html[data-whatintent="mouse"]` for hover. 2C converts them to `@media (hover: hover) { …:hover }`. `ab.mjs` adds a hover screenshot of the desktop main menu and a footer link. |
| 3 | major | Design: mobile nav | Today's open nav is an overlay (`position:absolute; top:3rem; bottom:0`, `app.css:583-591`), with two markups (`_header.html:16-27` wide, `:33-50` mobile). `app.js:7` also toggles `.main-logo.show` (`app.css:691`). Replace that with `body.home:has(#site-nav:popover-open) .main-logo` (`:has` is widely available). `ab.mjs` adds an "open nav" pair: A clicks `.mobile-nav-trigger`, B clicks the new button. |
| 4 | **blocker** | Design: hints, 4C | `coderdojochi_extras.py` has 3 popover branches (age+gender `:78-82`, age `:96-100`, gender `:114-118`), and the disabled trigger is a `<span … disabled>` (`:62,121`). 4C covers all 3 as one "eligibility hint". The trigger is a real `<button type="button">`, or the text is shown inline. `hint-gender` also tests the age branch. |
| 5 | major | AC 2, 1A | A full-page diff under 1 % misses small losses. `ab.mjs` also: (a) every icon in A (`[class*="fa-"]`, `.glyphicon`) has a B counterpart (`svg.icon`) in the same place with the same box ±1 px; (b) an above-the-fold (first 800 px) diff, and any page > 0.1 % there gets a lead look before commit. |
| 6 | minor | Icon map | `calendar-check` → FA7 `regular/`. `glyphicon-check` → `regular/square-check`. Drop `users` and the `fa-fw` rule: they're used only in dead `home.html`/`contact.html`. 2D vendors `svgs/regular/` too, and checks that the 7.x tarball has `svgs/{solid,regular,brands}`. |
| 7 | **blocker** | Read first, 1D | django-bootstrap3 is also used as `{% buttons %}` (`guardian/home.html:23-25`, `mentor/home.html:76-78`) and `{% bootstrap_form %}` in `account/signup.html:15`, `password_change.html:12`, `password_reset.html:17`, `password_reset_from_key.html:16`, `password_set.html:12`, `socialaccount/signup.html:14`, `student_detail.html:14`, `welcome.html:47` and `dashboard/session_donations.html:39`. 1D owns **all** of them: it writes `accounts/templates/account/_form.html` + `_field.html` (with a `bootstrap` flag, so `session_donations` keeps `form-group`/`control-label`/`form-control` until CP5), copying bootstrap3's label-as-placeholder and its error and help markup. **1C's `welcome.html` edit moves into 1D**, so one owner holds that file. 4A, 4D and 5D take over these templates in later checkpoints. |
| 8 | major | 1B | Also dead: `coderdojochi/templates/_topnav.html` (every dashboard page overrides `{% block topnav %}`, and its `{% url 'home'/'about'/'volunteer' %}` don't resolve) and `menu_is_active` (`coderdojochi_extras.py:133-142`). The `old_views` range is `:49-90`; remove the imports left unused (ruff). Drop `_topnav.html` from 5A. **`coderdojochi_extras.py` is 1B's file in CP1.** |
| 9 | major | A/B page list | Add `/account/logout/`, `/account/password/change/`, `/account/email/`, the socialaccount pages, `/400/`, `/403/`, `/404/` (`urls.py:325-339`; a random path under DEBUG shows Django's technical 404), and a logged-out public session detail. The associate board is at `/join-us/associate-board/` (`weallcode/urls.py:44`). |
| 10 | minor | 4A | Add `socialaccount/snippets/login_extra.html` and `provider_list.html` explicitly. |
| 11 | **blocker** | 1E ratchet | Don't hand-write the regex. Build the token set from the class selectors in `foundation.min.css` ∪ `bootstrap.min.css`, minus the brand names we keep (the same source as `classcheck`), plus `fa*`/`glyphicon*` and the `data-toggle|data-target|data-dismiss|data-ride|data-toggler` attributes. Match `class=["']`, and split values on whitespace (so `main-menu` doesn't count as `menu`). Templates only. `forms.py` and `coderdojochi_extras.py` get a separate string-literal scan with the same token set. |
| 12 | minor | 4D | `forms.py:372,390` `"form-control hidden"`: `hidden` is unstyled today, so those textareas are visible. Drop the class; **never** turn it into the `hidden` attribute. Dropping the `expand` span changes the label text, so keep it, or report it to Ali. |
| 13 | major | See more, 2A | Put `hidden="until-found"` on a plain wrapper `<div>` around the `.cols` grid (`team.html:141,180`), never on the flex element. `reset.css` uses `[hidden]:not([hidden="until-found"]) { display: none !important }`. Today the button's wrapper (`:149`) hides itself after the click. Keep that, and have `team-see-more` assert that the members are visible and the button is gone. |
| 14 | **blocker** | 1E, 2E, 4G | `REMOVED` is split into `REMOVED_PUBLIC` (pages on the weallcode base) and `REMOVED_DASHBOARD` (`/admin/` etc.). jQuery joins the public list in CP2 and the dashboard list only in 5E. |
| 15 | **blocker** | AC 4, 1A exit rule | Bytes rule: fail if B > A on any page. Require B < A only on the pages the checkpoint changes, and on every page at CP5. The 1A A = B proof expects equal bytes. |
| 16 | major | Runbook staging smoke | `smoke.mjs --cp9` asserts `.mobile-nav-trigger` and `[data-toggler]`, which are gone after CP2. 1A adds a `--frontend` mode to `smoke.mjs`: same page list and host allowlist as `--cp9`, font ACAO check, `site.js` loads 200 with ACAO, and the nav uses `[popovertarget="site-nav"]` and reveal uses `[data-reveal-target]`. Record the spec in Progress so it can be rebuilt. |
| 17 | major | 1A environment | `DEBUG=True` turns django-debug-toolbar on (`settings.py:387-403`). `seed.sh` exports one `SECRET_KEY` for both servers, and `ab.mjs` masks `#djDebug` and leaves `/__debug__/` and `/static/debug_toolbar/` out of bytes and request counts. Better still, run both with the toolbar off, if `settings.py` allows it via env. |
| 18 | **blocker** | 4C security | `student_register_link` returns `Template(form).render(context)` (`:125`), which parses session fields as template source, and `href={url}` is unquoted (`:49`). 4C builds the markup with `format_html` and returns it directly (no `Template()`), and adds a test where the message contains `{{` and `<`. Mutation: put back `Template(...).render` → test fails. |
| 19 | minor | 2E, pages CSS | `ManifestFilesMixin` doesn't rewrite ES `import` paths. `site.js` stays one file with no `import`s. A `url()` moved from `app.css` (`:231,306,314,401`) into `css/pages/` needs `../../images/`. |
| 20 | minor | 2B/2C/2E | 2B owns all nav CSS. 2C leaves `app.css:513-640` (nav rules) out of `brand.css`. |
| 21 | minor | Facts | `session_stats.html` has **1** `progress` finding (`:23`), not 5. Branch from the current `origin/main` (`6c1c1a20` on 2026-11-25, CP7b Python 3.13). Remove FA5 from `vendor.json` by version (a 7.x entry for the same package stays). Drop `focusable="false"` from the icon tag (IE-only). |
| 23 | **blocker** | 2B, 2C, 2E (lead, 2026-11-26, overrides rows 1 and 20) | In CP2 the page templates still use Foundation names (`button`, `menu`, `margin-*-half`…), so row 1's rename would unstyle them. 2C moves app.css rules whose selectors use Foundation names (or app.css's own `*-half` spacing) **verbatim** into `weallcode/css/brand-legacy.css` (`@layer components`, linked right after `brand.css`, ignored by `classcheck`, deleted in 4G); every other rule goes to `brand.css`. The `whatintent` → `@media (hover: hover)` rewrite still happens. **2E, not 2B, owns all header/mobile-nav CSS**, in `weallcode/css/nav.css` (`@layer components`, linked after `components.css`), so one task owns the nav markup and its CSS. 2B does no nav. |
| 24 | **blocker** | Cascade, 2A, 4G (lead, 2026-11-26) | Element rules in `reset`/`base` sit above `legacy`, so they beat every Foundation class rule on the same property (e.g. `div{margin:0}` beat `.grid-container` centring). 2A ends `reset.css` and `base.css` with a "legacy bridge", `:is([class], <Foundation component> *, #legacy-bridge) { all: revert-layer }`, so classed elements fall back to Foundation while it's loaded. **4G deletes both bridge blocks and the `[hidden="until-found"]{display:revert !important}` rule in the same change that removes `legacy.css`.** 2A proved the post-4G state (no Foundation, no bridges) at 0.000 % on its geometry page. Also: the gutter is 1.875rem at every breakpoint in this build (not 20/30 px); vocabulary gains `md-px-3`, `md-py-3`, `lg-py-4`, `h-100`. |
| 22 | minor | Ambiguities | `--post-invalid` belongs to 1A. 1B's grep proof runs after 1D lands (lead runs it). The icon test uses `override_settings(DEBUG=True)`, and the tag reads `settings.DEBUG` at render time. "4F" isn't a task: each 4A–4E task owns `css/pages/<its first template>.css`. Always include `dashboard/_messages.html` by the `dashboard/` path (`settings.py:144` DIRS makes `_messages.html` ambiguous). |

## Progress

### Checkpoint 1: built 2026-11-25, branch `claude/frontend-cp1-safety-net` (from `origin/main` `72aa0f44`). Not pushed.

**Plan drift found and applied (these override the text above):**

- `72aa0f44` (#1645) already deleted `cdc.js`, reworded the `settings.py`/`test_security_settings.py` comments and fixed the `cdc_admin` `ZeroDivisionError`. 1B skipped those.
- `coderdojochi/templates/admin/filter.html` is **live**: it overrides Django admin's `ListFilter` template (`TEMPLATES` DIRS) on 16 ModelAdmins. Kept, and not in `DeadFilesTest`.
- `dashboard/_admin_base.html` still included the deleted `_topnav.html` inside `{% block topnav %}`. The lead emptied the block.
- 1D added `accounts/templatetags/form_fields.py` (`render_widget` filter, lead-approved), because templates can't add the placeholder/title widget attrs that bootstrap3 added. Its test is `accounts/test_form_fields.py`. `account/_field.html` and `_form.html` keep Bootstrap classes under `bootstrap=True` (only `dashboard/session_donations.html`). **Owners for later:** 4B takes `_field.html`/`_form.html` plain mode off the ratchet; 5D removes the `bootstrap` flag and the `form-control` literal in `form_fields.py`.
- `invoke vendor` always wrote 1 file (`bootstrap3/LICENSE` is CRLF in npm, LF in git via `* text=auto`). `tasks.py` now writes text files with LF. Second run: 0 written.
- Vocabulary: `.stack` (and `column`, `vertical`) are Foundation classes. Renamed to `.nav-list-stack` in the table.
- Ratchet token source is a committed data file, `coderdojochi/tests/legacy_class_tokens.txt` (1079 names, sha256s of the 3 source CSS files in its header). app.css names that are only in Bootstrap (`bg-primary`, `list-unstyled`, `show`, `text-primary`) are ours. app.css `*-half` spacing names are legacy (2C drops them). Regenerate the sets with `manage.py shell -c "from coderdojochi.tests.test_frontend_stack import print_legacy_sets; print_legacy_sets()"`.
- URLs: meetings are under `/old/meetings/`; socialaccount is under `/account/3rdparty/`. Unreachable in A/B: staff student detail (redirects non-guardians; covered as guardian), socialaccount signup (needs a pending social login), provider login (off-site).
- `test/cypress/.../create-account.spec.js:59,70` selects `.control-label` and `.checkbox > label`, which plain mode no longer renders. Cypress is not in CI.

**A/B tooling (`/tmp`, rebuild from 1A if gone):** `/tmp/wac-ab/seed.sh [setup|start|stop|status|restart|sessions]`. Both servers run `DJANGO_SETTINGS_MODULE=ab_settings` (`/tmp/wac-ab/pyset/ab_settings.py`: imports the tree's settings, turns the debug toolbar off, forces the anymail test backend, drops sqlite `sslmode`). Seed: `loaddata fixtures/*.json` on sqlite (285 objects) + `/tmp/wac-ab/seed_objects.py` (5 users incl. `ab-mentor_nobg`; 4 students covering the 3 eligibility-hint branches; future girls-only class, partner class with password, unannounced meeting, sign-ups, 20 public mentors). `ab.mjs` extras: `--only`, `--vp`, `--jobs`, `--no-jquery`, `--post-invalid` (local only), `--require-smaller`; route guard aborts every non-GET except the post-invalid submit and any `*/announce/*`. Third-party request failures are warnings, not failures. Bytes = first-party CSS+JS+font. Mobile DPR 1.

**`smoke.mjs --frontend` spec:** everything `--cp9` does; mobile `/` `[popovertarget="site-nav"]` opens `#site-nav:popover-open`; desktop `/team/` `[data-reveal-target]` reveals its `aria-controls` target; `weallcode/js/site*.js` 200 (+ ACAO cross-origin) on every non-admin page; `window.jQuery` unset on public pages. Fails by design before CP2.

**Evidence:**

- 1A proof, A = B = main: 98 runs (49 pages × 2), max 0.000 %, bytes equal 98/98, exit 0. Patched `app.css` (`body{font-size:17px}`): 82/94 runs fail, max 38.66 %, exit 1 (the 12 passes don't load `app.css`). `app.css` shasum identical after undo.
- Lead A/B, main vs branch, `--interact --post-invalid`: **98 runs, 0 failing, max 0.006 %** (`not-found`, desktop 0.006 % / mobile 0.003 %: Django's technical 404 lists URL patterns). CSS+JS+font bytes equal 96/98, B > A on 0 (welcome drops js-datepicker). Interact: 5 pass on old markup (`nav-open-click`, `nav-tap`, `team-see-more`, `dash-nav`, `dash-rows`), 4 skipped as expected (`nav-open-keyboard`: old trigger has no href; 3 hints: known broken).
- Guard tests: 1E mutations failed as required (`class="callout"` in a throwaway template; empty `cdc.js`; `bootstrap3` in `INSTALLED_APPS` fails while present). `LEGACY_TEMPLATES` 55, `LEGACY_PYTHON` 2.
- Whole build: ruff + format clean (130 files); full suite **140 tests OK**; pre-commit all passed; `invoke vendor` 0 written twice; `import bootstrap3` fails; `makemigrations --check` no changes, no planned operations from bootstrap3.
- `legacy-scan`: **6** (same baseline 6).

**Released:** PR https://github.com/WeAllCode/website/pull/1647, CI green (django-postgres, infra, pre-commit, tests). Staging `b0c7d7ea`: `smoke.mjs --cp9 --basic-auth-op "op://homelab/WAC staging basic auth/password" --baseline out/cp9g-staging/report.json` 24/24 pass (without a baseline every page fails on this network's blocks of `embed.double.giving` and `static.cloudflareinsights.com`). Merged as `25ce01b7`; previous prod `491d8d87`. Prod live 05:34 UTC 2026-11-26; `smoke.mjs --cp9 --baseline out/cp9-prod/report.json` 23/24, the one failure a third-party reCAPTCHA CSP report POST to `csp.withgoogle.com` (ERR_BLOCKED_BY_ORB) on desktop `/account/signup/`. Sentry: the Sentry connectors here only reach `braven-org`, so Ali watches the We All Code project. `gcloud` needs `gcloud auth login --configuration wac` when its token expires.

### Checkpoint 2: built 2026-11-26, branch `claude/frontend-cp2-css-core` (from `origin/main` `4c0eb2cd`). Not pushed.

**Plan drift found and applied (see review rows 23 and 24):**

- Row 23: page templates still use Foundation names in CP2, so app.css rules on those names moved verbatim to `brand-legacy.css` (deleted in 4G); 2E owns header/nav CSS in `nav.css`.
- Row 24: the "legacy bridge" at the end of `reset.css` and `base.css` (`all: revert-layer` on classed elements). **4G deletes both bridges and the `until-found` `!important` rule with `legacy.css`.**
- **Layer beats specificity for normal declarations too** (new pitfall). app.css rules that used to lose to more specific Foundation rules now win. 2C fixed 4 with `:not(:where(…))`, which adds no specificity: `.program-icon` width/padding inside grid cells (`/our-story/`, `/join-us/` grew 224/448 px), `.text-*` on `a:hover/:focus`, `footer a` on hover/focus, `.sub-menu a` vs `.menu .active > a`. Every CP3+ task that leaves a Foundation class on an element next to layered CSS can hit this; the A/B catches it.
- Icons: 4 FA7 glyphs differ in width from FA5 (`check`, `graduation-cap`, `handshake-angle` 3 px narrower, `google` ~1 px wider at 24 px). Height and alignment match. **The `ab.mjs` icon box check is relaxed to height and position ±1 px, width within the glyph difference** (lead decision; to apply in `ab.mjs` before CP3). `.icon` uses `inline-size: auto`.
- `.cta` darker state shows on `:focus-visible` (Foundation used `:focus`): a mouse click no longer leaves a button dark. Disabled tertiary no longer turns blue on hover. Skip link is pinned top-left when focused (guide pattern). Smooth scroll respects reduced motion.
- Notes for CP3/CP4: `button-danger` has no CSS rule today (`meeting_detail.html:89` renders as a plain link), so 4D drops it rather than mapping to `.cta-danger`. `.sub-menu .menu` / `.sub-menu .active a` (brand-legacy) need `.sub-menu .nav-list` / `[aria-current]` equivalents in `brand.css` when 3x migrates sub-menus. Hint triggers have no "more info" affordance class (4B/4C decide). `aria-disabled` links also drop `href`. Print: Foundation's print `*{background:0 0!important}` now beats `.bg-*` (lower layer wins for `!important`); left as is.
- New names: `header-nav`, `main-menu-donate` (nav.css); `md-px-3`, `md-py-3`, `lg-py-4`, `h-100` (utilities.css); `--space-4` token.
- The gutter is 1.875rem at every breakpoint in this Foundation build.
- `ab.mjs` fixes (lead): `team-see-more` measures the wrapper's content (`hidden="until-found"` keeps a 0 px box); `applyMasks` skips elements that fail `checkVisibility()` or sit in `[hidden]`.
- `write_token_file()` now reads `app.css` from git at `25ce01b7`.
- PR #1650 (on main after this branch's base) shows volunteers only with ≥ 3 checked-in classes in 2 years. When both A/B trees move past it, `seed_objects.py` must give the 20 public mentors 3 checked-in classes each, or "See more" won't render.
- Donation widget: untestable here (`embed.donsplus.com` → `embed.double.giving` is refused on this network; `donsPlus is not defined` identically on main). **Ali clicks Donate on staging.**

**Evidence:**

- Lead A/B, main (`4c0eb2cd`) vs branch, `--interact --post-invalid --no-jquery`: **98 runs, 0 failing, max 0.006 %** (`not-found` only, Django's technical 404). CSS+JS+font bytes B < A on 86/98 (e.g. `/` 639,894 → 318,008), equal on 12 (dashboard pages), B > A on 0. `window.jQuery` undefined on every public page.
- Interact: `nav-open-click`, `nav-open-keyboard`, `nav-tap`, `team-see-more` pass on the new markup; `dash-nav`, `dash-rows` pass on old markup; 3 hints skipped (CP4).
- 2A geometry page (Foundation markup vs vocabulary, 8 widths, CP3 and post-4G variants): 0.0000 %. 2B components page: 0 % per component incl. hover. 2C emulated cascade: 82 runs + 18 hover/focus pairs, 0.0000 % and 0 computed-style diffs.
- `classcheck.mjs`: 9 files, 278 names, 0 collisions. `legacy-scan`: **6** (unchanged). `invoke vendor` 0 written. Full suite **148 tests OK** (incl. 8 icon tests; the `aria-hidden` mutation fails one). ruff clean. `LEGACY_TEMPLATES` 51 (the 4 chrome partials removed); `REMOVED_PUBLIC` += `jquery`, `what-input`, `foundation.min.js`.

## Sources

- https://github.com/GoogleChrome/modern-web-guidance
- https://web.dev/baseline
- https://docs.djangoproject.com/en/5.2/topics/forms/#reusable-field-group-templates
- https://developer.mozilla.org/en-US/docs/Web/CSS/@layer
- https://developer.mozilla.org/en-US/docs/Web/API/Popover_API
- https://fontawesome.com/license/free
