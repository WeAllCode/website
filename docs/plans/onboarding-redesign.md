# Onboarding redesign for parents and volunteers: intent in the session, not in `?next=`

Status: **plan only.** Nothing built. Written 2026-11-26 from `main` at `7e29406d` (PR 1660). Product decisions by Ali, 2026-11-26 (below).

**Ali's decisions (2026-11-26). These override anything below that contradicts them:**

- **Infer the role, allow a switch.** A visitor who starts from a class "Enroll" button is a parent; one who starts from a meeting "Attend" or class "Volunteer" button is a volunteer. Skip the "Who are you?" screen for them, and show a one-line "Not a parent? I'm volunteering" (or the reverse) switch on the next screen.
- **Parents: one page.** "About you" (the `GuardianForm` fields) and "Your first student" (the `StudentForm` fields) are one form with one submit.
- **Public class pages get a "Volunteer at this class" button** next to "Enroll now". Its intent survives signup and returns the volunteer to the class.
- **Volunteers: one short required step** after the role: birthday, phone and zip. Birthday decides background check vs the under-18 waiver (PR 1657). Then the destination, with the account-home checklist as today.
- Releases need Ali's explicit OK. Never push, merge or release without it.
- **Never send any email** in local runs, staging or prod checks (same rule as `docs/plans/frontend-rewrite.md`). Every local server runs with `EMAIL_BACKEND=anymail.backends.test.EmailBackend` and `RESEND_API_KEY=` (empty). Anything that needs an email to prove itself gets a Django test with `mail.outbox`. On staging and prod: page loads only, no form submits.

## Goal and done

**User story (parent).** As a parent who found a class on weallcode.org, I want to sign up, tell you about me and my kid once, and land back on that class ready to enroll, so that signing up for a free class takes one sitting and I never hit a dead end.

**User story (volunteer).** As a volunteer who found a class or a mentor meeting, I want to sign up, give the few details you need, and land back on that class or meeting, so that I can see what's left (background check or under-18 waiver) and sign up.

**User story (maintainer).** As the maintainer, I want no user-controlled URL to ever decide where the site redirects, so that weallcode.org can't be used as an open redirect and the flow is easy to change.

**Acceptance criteria.**

1. **No off-site redirect.** No view under `/welcome/`, `/account/`, `/classes/` or `/old/meetings/` redirects off-site or to a URL name taken from the request, whatever `next`, `enroll`, `student` or `Referer` holds. The only `next` left is allauth's own on `/account/login/` and `/account/signup/`, which allauth validates.
2. **Class enroll round trip.** A logged-out visitor who clicks "Enroll now" on a class, signs up, and submits the one-page parent form lands on that class's sign-up confirmation for the new student (`/classes/<pk>/sign-up/<student_id>/`).
3. **Meeting round trip.** A logged-out visitor who clicks "Attend" on a meeting, signs up and submits the volunteer step lands on that meeting's page, and "Attend Meeting" then works (today the POST is a 500, see Current journeys).
4. **Class volunteer round trip.** A logged-out visitor who clicks "Volunteer at this class" lands back on the class after the volunteer step. If they need a background check, or are under 18 and waiting on the waiver, the mentor class page shows the note and a sign-up attempt flashes the message and stays on the class; nothing redirects to the `Referer`.
5. **Role inferred.** With a class-enroll intent the parent form shows without the "Who are you?" screen; with a meeting or volunteer intent the volunteer step does. The switch link swaps the form. The role is saved only when the form is submitted.
6. **Intent is used once.** After the destination is reached the intent is gone: the next login or `/welcome/` visit goes to the normal default.
7. **Login keeps intent too.** An existing user who clicks a start button, then "I already have an account" and logs in, lands on the same destination (after any missing step).
8. **No dead ends.** A logged-in user without a role who opens a class page is sent to onboarding with that class as the intent (today: 404). An anonymous POST to a meeting sign-up redirects to login (today: 500).
9. **A parent can only enroll their own students.** `/classes/<pk>/sign-up/<student_id>/` 404s for another guardian's student (today it doesn't check).
10. **The edge cache is unaffected.** Logged-out GETs of the cached public pages (`PUBLIC_CACHE_VIEW_NAMES` in `coderdojochi/middleware.py:15`) and of public class pages set no session cookie. For logged-out visitors on public pages, only the start endpoints write the session (logged-in views such as 1C, 1E and the partner-password page already have a session).
11. **Old links still work.** A legacy `/welcome/?next=/classes/<pk>/&enroll=True` or `/account/?next=/old/meetings/<pk>/` (bookmarks, old emails) still reaches the same destination, through the same validation.
12. Full test suite, `ruff check`, `ruff format --check` and `pre-commit run --all-files` pass. Every criterion has a test with a recorded mutation (Proof).

**Out of scope.** Multiple guardian emails (#1551) and class prerequisites (#1553), see "Related issues". Redesigning the account home pages. The front-end rewrite's CSS work (this plan uses its class vocabulary). Staff avatar approve and reject links (`coderdojochi/old_views.py:61,97`): they build `?next=` from our own `reverse()` and allauth validates it on login, so they're safe; leave them. Captcha, password rules and email verification.

## Current journeys (mapped on `main` at `7e29406d`)

Verified with a throwaway test-client probe (scratch, not committed) unless marked "read".

### Parent, from a public class page

1. `/classes/<pk>/` logged out → `public/session_detail.html:30` "Enroll now" → `/account/signup/?next=/classes/<pk>/&enroll=True`.
2. Signup page (`accounts/templates/account/signup.html:13`) posts to `?next=/classes/<pk>/` **+ `/enroll/`** (the template appends `/enroll/` to the query, giving `?next=/classes/<pk>//enroll/`). Allauth's hidden `next` input wins, so it redirects to `/classes/<pk>/`. (read)
3. **Dead end:** a logged-in user with no role on `/classes/<pk>/` gets a **404**: `SessionDetailView` (`coderdojochi/views/sessions.py:142-165`) sends every non-mentor to `guardian.SessionDetailView`, whose `get_object_or_404(Guardian, …)` fails. The enroll intent is lost. (probe: 404)
4. If they find `/welcome/` (e.g. via `/account/`, `accounts/views.py:52-66`): "Who are you?" → Parent. The parent form posts to `action=""`, so the query survives; the volunteer form re-echoes `next` and `enroll` unencoded (`welcome.html:44,65`).
5. Contact form (`GuardianForm`: phone, zip, gender, race/ethnicity, birthday) → redirect to `next?enroll=True`.
6. Back on `/welcome/` → student form → redirect to `next?enroll=True&student=<id>`. **No view reads `enroll` or `student`.** The parent lands on the class page and clicks "Enroll" next to the student.
7. `/classes/<pk>/sign-up/<student_id>/` → confirm → `Order` + confirmation email.

Five screens and four redirects after signup, one of them a 404.

### Parent, logged in, from their class page

`guardian/session_detail.html:63,69` "Add another student" / "Add Students to Enroll" → `/welcome/?next=<path>&enroll=True` → student form → back to the class.

### Volunteer, from a meeting page

1. `/old/meetings/<pk>/` logged out → `meeting_detail.html:94` "Login or register to sign up for this mentor **object**" (copy bug) → `/account/signup/?next=/old/meetings/<pk>/`.
2. Signup → `/old/meetings/<pk>/` → "Attend Meeting" → `/old/meetings/<pk>/register/` → `meeting_sign_up` (`coderdojochi/views/meetings.py:117`) does `get_object_or_404(Mentor, user=request.user)` with no role check (404 without a role) and no `login_required` (anonymous → error).
3. **The POST always 500s:** line 216 does `redirect("meeting_detail", …)` but the URL name is `meeting-detail` (`coderdojochi/urls.py:59`). Probe: `NoReverseMatch`. The `MeetingOrder` and the confirmation email are written before the crash.

### Volunteer, from a class page or the welcome screen

1. There is no volunteer button on the public class page today.
2. `/welcome/` → Volunteer → `create_new_user` sends the welcome email and redirects to `?next=<next>` (relative to `/welcome/`) or `account_home`.
3. `WelcomeView.dispatch` (`welcome.py:28-41`): a mentor whose user has a first name (always true after signup, since `SignupForm.signup` sets it, `coderdojochi/forms.py:137-140`) is redirected straight to `next`. **This is the open redirect.** Probe: after picking Volunteer with `?next=https://evil.example/`, the next GET of `/welcome/?next=https://evil.example/` returns `302 https://evil.example/` once the user has a first name. The bio form in `welcome.html` is effectively dead for mentors.
4. Account home checklist (`accounts/templates/account/mentor/home.html:15-38`): name, bio, avatar, background check or under-18 email (`Mentor.awaiting_minor_waiver`, `Mentor.needs_background_check`, `coderdojochi/models/mentor.py:127-142`), attend a class. Zip is a profile field (`home.html:76`, `MentorForm.zip` optional, `forms.py:195-204`).
5. Class sign-up (`SessionSignUpView.check_access`, `sessions.py:259-280`): waiver or background-check message, then **redirect to `HTTP_REFERER`** (fallback `/dojo`, which doesn't exist). A link from another site to `/classes/<pk>/sign-up/` bounces back to that site.

### Other `next` producers (lead's list, confirmed)

- `coderdojochi/mixins.py:30` `RoleRedirectMixin`: role-less user on a sign-up URL → `/welcome/?next=<class>[&enroll=True]`.
- `accounts/views.py:57` forwards a raw `next` to `/welcome/`.
- `accounts/templates/account/guardian/home.html:54` "Add another student" → `/welcome/?next=/account/`.
- Login: allauth's own `next` (`accounts/templates/account/login.html:32`, tests `accounts/tests.py:42-63`). Allauth validates it. Keep.

### UX gaps found on the way

Fixed by this plan:

- The 404 for a role-less user on a class page (above).
- The meeting sign-up 500 and the anonymous meeting sign-up error.
- Redirect to `Referer` / `/dojo` on the background-check and waiver blocks.
- Guardians can enroll or cancel any student by id (`sessions.py:236-239` looks up `Student` by id only).
- Signup page's `…/enroll/` query corruption.
- Role asked even when the button already said which.
- Parent contact info and first student on two screens.
- "this mentor object" / "attend this object" copy (`meeting_detail.html:88,94`).
- `welcome.html:5` title renders `{{ class.title }} Sign Up` with no `class` in context → " Sign Up".
- Volunteers can't start from a class page.

Noted, not fixed (follow-ups, listed in the PR):

- Public class page shows "Enroll now" even when full: `public.SessionDetailView` never sets `spots_remaining`, so `public/session_detail.html:27` never fires.
- `GuardianForm` asks the parent's own gender, race/ethnicity and birthday, all required, before the student. Worth asking whether they can be optional; not changed here (reporting may depend on them).
- `meetings` live under `/old/meetings/`. Moving them is its own change.
- Mobile: the role buttons are two `medium-4` cells; on a phone they stack with no gap above the second. The new templates use CP4's stacked layout instead, so this goes away with `welcome.html`.

## New flow

**One idea:** a click on a start button stores a typed intent, never a URL: `{"kind": "session" | "meeting" | "none", "pk": int | None, "role": "guardian" | "mentor" | None, "new_student": bool}`. Only buttons set a `role` (the exact list is "Who sets a role on an intent" under Tasks); an intent captured any other way (a role-less user who browsed to a class, the legacy converter without `enroll`) has `role=None`, so the "Who are you?" screen still shows (Ali: infer only from the button). Where to go is always computed with `reverse()` from that intent, after checking the object still exists. Nothing from the request is ever passed to `redirect()`. This improves on "validate `next` once, then store it": a stored URL can still be any same-site path (logout, admin, a URL-name string); a stored `(kind, pk)` can only ever produce a class or meeting page.

**Start endpoints** (GET, not cached, the only views that write the intent for logged-out visitors; logged-in views in 1B–1E also write it):

| URL | Name | Intent |
| --- | --- | --- |
| `/classes/<pk>/enroll/` | `session-enroll-start` | `session`, `guardian` |
| `/classes/<pk>/enroll/new-student/` | `session-add-student-start` | `session`, `guardian`, `new_student=True` |
| `/classes/<pk>/volunteer/` | `session-volunteer-start` | `session`, `mentor` |
| `/old/meetings/<pk>/attend/` | `meeting-attend-start` | `meeting`, `mentor` |
| `/welcome/add-student/` | `add-student-start` | `none`, `guardian`, `new_student=True` (guardian home "Add another student") |
| `/welcome/done/` | `welcome-done` | not a start: the PR 1655 "N students registered / Find a class / Done" page, its own URL so the router never loops on it |

Each start stores the intent, then: logged out → `/account/signup/`; logged in → `onboarding.next_url(request)`. Each start checks: session `is_active` (on purpose stricter than the class page, which renders inactive sessions because no class view filters on it, `sessions.py:145`; an inactive class's start link 404s) **and** partner password (`SessionDetailView.validate_partner_session_access`, `sessions.py:167-191`; without access → `session-password`); meeting `is_active`, and `is_public` for anonymous users (`meetings.py:50-59`). Responses carry `X-Robots-Tag: noindex, nofollow`, and every link to them has `rel="nofollow"`, so crawlers don't mint sessions (there is no `robots.txt` in the repo; adding one is a follow-up).

**The router** `onboarding.next_url(request)` returns the first thing the user still needs, else the destination. A role other than `mentor` or `guardian` counts as no role, everywhere (router, `RoleRedirectMixin`, `RoleTemplateMixin`, `SessionDetailView`): use one helper, `intent.user_role(user) -> "guardian" | "mentor" | None`. The "pending role" is the role the user has, else `request.session["onboarding_role"]` (set by the role step or the switch link), else `intent["role"]`.

1. **Role mismatch**, judged on the **saved** role only (`saved = user_role(user)`), exactly: `saved and ((intent["role"] and intent["role"] != saved) or (intent["kind"] == "meeting" and saved == "guardian") or (intent["kind"] == "none" and saved == "mentor"))`. An intent with `role=None` for a class (a browsed class) is never a mismatch: clear the intent, flash `MISMATCH_MESSAGE` ("You're signed in as a parent, so …" / "…as a volunteer, so …"), destination = the object's page (`account_home` for kind `none`). Runs first so a mismatched user is never pushed through the other role's forms.
2. No pending role → `/welcome/` role step. **In CP1, no saved role → `/welcome/` whatever the intent says** (CP1 has no inferred-role screens; the current welcome view shows "Who are you?"). 2B replaces this CP1 rule with the pending-role rule.

The switch link calls `set_pending_role`, which also rewrites the intent so step 1 never fires on a switched user: kind `session` → swap `role` (`guardian` ↔ `mentor`); kind `meeting` switched to `guardian` → kind `none` (a parent can't attend a mentor meeting; they continue to the parent page and then `welcome-done`).
3. Pending role `guardian` without phone or zip → `/welcome/` parent page: "About you + first student" if the guardian has no students, "About you" only if they already have students.
4. Pending role `mentor` without birthday, phone or zip → `/welcome/` volunteer step. **CP2 only**: in CP1 the router has no mentor step (the CP1 welcome view redirects every named mentor, so a mentor step there would loop).
5. Guardian with 0 students, or intent `new_student=True` and no `last_student` set yet → `/welcome/` student-only form.
6. Destination, and `clear_intent` (which drops the intent, `onboarding_role` and `last_student` together):
   - class intent + `last_student` → `session-sign-up` for that class and student, **only if** the class takes internal sign-ups now: no `external_enrollment_url`, and the parent window is open (`start_date - MAX_DAYS_FOR_PARENTS <= now`, same rule as `guardian/sessions.py:39-52`). Otherwise `session-detail`, which explains why.
   - other class intent → `session-detail`; meeting intent → `meeting-detail`.
   - kind `none` or no intent → `welcome-done` for a guardian whose `last_student` was just set, else `account_home`.

Intents carry a `created` ISO timestamp; `get_intent` treats one older than 24 hours as absent and clears it.

`intent.current_step(request) -> "role" | "guardian" | "guardian-about" | "mentor" | "student" | None` is the same logic as steps 1-5, returning which `/welcome/` screen applies (`None` = no step, go to `next_url`). `next_url` uses it, so the view and the router can't disagree.

Allauth hooks: a new `accounts/adapter.py` `AccountAdapter` overrides `get_login_redirect_url` and `get_signup_redirect_url` to return `next_url(request)`. Allauth still prefers a validated `next` when one is present (`allauth/account/utils.py:38-56`), so `login_required` round trips are unchanged; **in that case the adapter's redirect methods aren't called, so `AccountAdapter.post_login` (`allauth/account/adapter.py:551-572`) clears any stored intent when `redirect_url or get_next_redirect_url(request)` is set**, then calls `super()`, or the intent would fire at a later, unrelated login. `post_login` is the one place that sees Google's `next` too: allauth keeps it in `sociallogin.state` and passes it as `redirect_url` (`allauth/socialaccount/models.py:400-402`, `socialaccount/internal/flows/login.py:30`); the callback request itself carries no `next`, so a `user_logged_in` signal reading the request would miss it. allauth also calls `get_login_redirect_url` when a logged-in user opens the login or signup page (`RedirectAuthenticatedUserMixin`, `allauth/account/mixins.py:89`), after email confirmation (`adapter.py:292`) and on reauth; that's fine because `next_url` only clears the intent when it returns a destination the user would have gone to anyway. Django's `login()` keeps an anonymous session's data (`cycle_key`), so the intent survives signup, login and the Google flow.

**Parent, new (from a class):** Enroll now → signup (name, email, password, or Google) → one page "About you + your first student" → class sign-up confirmation for that student → Confirm. **Two screens after signup instead of five; no role screen.**

**Volunteer, new (from a meeting or class):** Attend / Volunteer at this class → signup → one short step (birthday, phone, zip) → back on the meeting or class, which shows the background-check or under-18 note and the sign-up button. **One screen after signup.**

**Anyone, no intent (e.g. `/account/signup/` from the nav):** signup → "Who are you?" → parent page or volunteer step → default destination. Same as today minus one parent screen.

## Read first

The builder reads these before any task. Line numbers are on `main` at `7e29406d`; PR 1661 moves template lines, so re-find them after it merges.

| File | Lines | Why |
| --- | --- | --- |
| `coderdojochi/views/welcome.py` | all (225) | The view being replaced. `dispatch` 28-41 (open redirect), `update_account` 92-120, `add_student` 122-146, `create_new_user` 148-225 (role save and the two welcome emails: copy the email calls and `merge_global_data` exactly) |
| `coderdojochi/templates/welcome.html` | all | Current screens; PR 1661 rewrites its markup (copy CP4's version, not this one) |
| `coderdojochi/mixins.py` | 19-40 | `RoleRedirectMixin`, used only by `SessionSignUpView` |
| `coderdojochi/views/sessions.py` | 142-191, 211-285 | `SessionDetailView` role dispatch (404 bug), `SessionSignUpView.dispatch` (student lookup 236-239), `check_access` (Referer 269, 278) |
| `coderdojochi/views/meetings.py` | 117-222 | `meeting_sign_up`: no login check, wrong URL name at 216 |
| `accounts/views.py` | 52-66, 166-173 | `AccountHomeView.dispatch` legacy `next`; `get` falls back to `welcome` for no role |
| `coderdojochi/forms.py` | 29, 119-143, 145-218, 266-305, 308-469 | `ZIP_CODE`; `SignupForm` (captcha, `signup()` sets names); `MentorForm` birthday/phone/zip widgets to copy; `GuardianForm`; `StudentForm` (excludes `guardian`) |
| `coderdojochi/models/mentor.py` | 40-51, 84-100, 127-142 | `background_check_waived`, `phone`, `zip`, `is_minor`, `needs_background_check`, `awaiting_minor_waiver` |
| `coderdojochi/models/session.py`, `meeting.py` | `session.py:285-289`, `meeting.py:89-93` | `get_absolute_url` / `get_sign_up_url` names |
| `coderdojochi/urls.py` | 47-84, 167-227, 276-283 | Meeting block; class block (`session-detail` at 183); welcome block |
| `coderdojochi/middleware.py` | 1-70 | Edge-cache rules: a response that sets a cookie is never cached; keep start endpoints out of `PUBLIC_CACHE_VIEW_NAMES` |
| `coderdojochi/settings.py` | 314-323 | allauth settings; add `ACCOUNT_ADAPTER` here |
| `coderdojochi/templatetags/coderdojochi_extras.py` | 28-80 | `student_register_link`, the Enroll buttons on the guardian class page |
| `coderdojochi/tests/test_signup_and_welcome.py` | all | Test style to copy (`@override_settings(SECURE_SSL_REDIRECT=False)`, `CDCUserFactory`, `force_login`) |
| `coderdojochi/tests/test_mentor_minor.py` | 57-82 | How sign-up access is tested for minors |
| `coderdojochi/tests/test_frontend_stack.py` | 69-110, 318-360, 456-485 | Legacy-template ratchet (new templates must use no legacy classes) and two `/welcome/` tests to update |
| `accounts/tests.py` | 22-63 (about +3 after PR 1661) | `SocialApp` setup needed by any test that renders signup or login |
| `docs/plans/frontend-rewrite.md` | "Class vocabulary", "Checkpoint 4", "Progress" | Class names for the new templates; what PR 1661 changed |
| `.venv/…/allauth/account/adapter.py` | 246-268 | `get_signup_redirect_url`, `get_login_redirect_url` |
| `.venv/…/allauth/account/utils.py` | 38-56 | `next` beats the adapter |

Docs:

- Django `url_has_allowed_host_and_scheme` (only for the legacy converter) isn't in the reference docs; read `.venv/…/django/utils/http.py` and copy its use from `.venv/…/django/contrib/auth/views.py` (`RedirectURLMixin.get_redirect_url`).
- Django sessions survive login: https://docs.djangoproject.com/en/5.2/topics/auth/default/#django.contrib.auth.login ("data set during the anonymous session is retained").
- allauth adapter: https://docs.allauth.org/en/latest/account/advanced.html#custom-redirects

Test helpers every new test needs:

- Signup in tests: `mock.patch("django_recaptcha.fields.ReCaptchaField.validate")` (the signup form has a reCAPTCHA v3 field, `forms.py:122`), and a Google `SocialApp` attached to the current `Site` (copy `accounts/tests.py:25-31`), or the template tag raises `SocialApp.DoesNotExist`.
- `@override_settings(SECURE_SSL_REDIRECT=False)` on every client test.
- Email: anymail's test backend (`test_settings.py:39`); assert on `mail.outbox`, never send.
- Sessions: `SessionFactory(is_active=True)`. `Session.is_active` defaults to `False` (`models/session.py:120-121`) and the factory doesn't set it (`factories.py:48-56`), so a plain `SessionFactory()` makes every round-trip test 404 or land on `account_home`. Never change the code to make such a test pass.

## Template coordination with the front-end rewrite (PR 1661, CP4)

PR 1661 touches every existing template this plan edits, plus `accounts/views.py`, `coderdojochi/forms.py` and `coderdojochi/templatetags/coderdojochi_extras.py`.

**Templates this plan touches:**

| Template | Checkpoint | Change |
| --- | --- | --- |
| `coderdojochi/templates/onboarding/role.html` (new) | 2 | "Who are you?" |
| `coderdojochi/templates/onboarding/guardian.html` (new) | 2 | One-page parent form; student-only variant |
| `coderdojochi/templates/onboarding/mentor.html` (new) | 2 | Volunteer step |
| `coderdojochi/templates/welcome.html` | 2 | Reduced to the PR 1655 "N students registered / Find a class / Done" page, served at `welcome-done` |
| `coderdojochi/templates/public/session_detail.html` | 2 | Enroll → `session-enroll-start`; add "Volunteer at this class" |
| `coderdojochi/templates/guardian/session_detail.html` | 2 | Lines 63, 69 → `session-add-student-start` |
| `coderdojochi/templates/meeting_detail.html` | 2 | Line 94 → `meeting-attend-start` and login; "object" copy |
| `accounts/templates/account/guardian/home.html` | 2 | Line 54 → `{% url 'add-student-start' %}` (no `next`) |
| `coderdojochi/templates/mentor/session_detail.html` | 2 | Background-check / under-18 note above the sign-up button |
| `accounts/templates/account/signup.html` | 2 | Drop the `next`/`enroll` echo from `action`; intent line ("You're signing up to enroll in …") |
| `accounts/templates/account/login.html` | 2 | Same intent line; `next` input untouched |

**Order (avoids every conflict):**

1. **Checkpoint 1 touches no template** and none of PR 1661's hunks (its `accounts/views.py` changes are at lines 14 and 176-241; ours are 52-66). It can merge before or after PR 1661. It closes the open redirect on its own.
2. **Checkpoint 2 starts only after PR 1661 is merged** and its branch is cut from that `main`. New templates are written in CP4's vocabulary, so they pass `test_frontend_stack.LegacyRatchetTest`. New Python goes in a new `coderdojochi/onboarding/` package so `forms.py` and `coderdojochi_extras.py` aren't edited.
3. Front-end CP5 (dashboard) touches none of these files. If CP5 is in flight when Checkpoint 2 starts, no rebase is needed.

## Tasks

New package layout (fixed here so tasks can run in parallel):

```
coderdojochi/onboarding/__init__.py   # empty
coderdojochi/onboarding/intent.py     # CP1 Task 1A
coderdojochi/onboarding/forms.py      # CP2 Task 2B
coderdojochi/onboarding/start.py      # CP2 Task 2A
accounts/adapter.py                   # CP1 Task 1D
```

**`intent.py` API (fixed; tasks 1B–1E and 2A–2B code against it):**

```python
SESSION_KEY = "onboarding_intent"

MISMATCH_MESSAGE = {"guardian": "…", "mentor": "…"}

def user_role(user) -> str | None               # "guardian" | "mentor" | None (any other value → None)
def set_intent(request, kind: str, pk: int | None, role: str | None, new_student: bool = False) -> None
                                                # keeps an existing intent for the same (kind, pk) if it has a role and the new one doesn't
def get_intent(request) -> dict | None          # validated: unknown kind/role, non-int pk for session/meeting, or older than 24 h → None
def clear_intent(request) -> None               # drops the intent, "onboarding_role" and "onboarding_last_student"
def set_pending_role(request, role: str) -> None  # role step and switch link (CP2); also rewrites intent["role"] (see New flow)
def intent_from_legacy_next(request) -> None    # reads GET["next"] once; stores an intent if valid; never returns a URL
def set_last_student(request, student_id: int) -> None   # destination rule 6
def current_step(request) -> str | None         # which /welcome/ screen applies (router steps 1-5)
def next_url(request) -> str                    # the router; always a reverse() result
```

`intent_from_legacy_next`: take `request.GET.get("next")`; require `url_has_allowed_host_and_scheme(url, allowed_hosts={request.get_host()}, require_https=request.is_secure())`; take `urlsplit(url).path`; `resolve()` it inside `try/except Resolver404`; accept only `url_name in {"session-detail", "session-sign-up", "meeting-detail", "meeting-register"}` and use `kwargs["pk"]`. Role: `guardian` only when `enroll` is in `GET`; otherwise `None` (the role screen decides). Anything else is ignored silently.

`next_url` steps and destinations are exactly the router in "New flow". It checks the object exists (`Session.objects.filter(pk=…, is_active=True).exists()`, `Meeting.objects.filter(pk=…, is_active=True).exists()`); a stale intent is cleared and the default is used. It clears (via `clear_intent`) only when it returns a destination (steps 1 and 6), not a step.

**Who sets a role on an intent** (one list, so tasks don't contradict "Only the start endpoints… set a role"): the five start endpoints; the legacy converter when `enroll` is present (`guardian`); `RoleRedirectMixin` when `enroll` is present (`guardian`); `meeting_sign_up` for a role-less user (`mentor`, 1E: the user clicked "Attend Meeting", which is a button). Nothing else.

### Checkpoint 1: close the open redirect and the dead ends (backend only, no templates)

**1A runs first, alone** (1B–1E import `intent.py`). Then 1B, 1C, 1D and 1E run in parallel: each owns its files, and they share only the `intent.py` API. 1D's `test_legacy_meeting_next_still_works` also goes through 1B's welcome view, so the lead runs 1D's Proof after 1B has landed.

**1A. Intent module.** Files: `coderdojochi/onboarding/__init__.py`, `coderdojochi/onboarding/intent.py`, `coderdojochi/tests/test_onboarding_intent.py`, `coderdojochi/test_settings.py` (add `SLACK_WEBHOOK_URL = ""` so `Mentor.save()` can never post from a test; `settings.py:337` reads it from the env).
- Write the API above. In CP1 the router has steps 1, 2 (no saved role → welcome, whatever the intent says), 3, 5 (all map to `reverse("welcome")`, which the current welcome view handles) and 6; **no step 4** (see "New flow"); `current_step` exists and CP1's `next_url` already calls it (CP1 returns only `"role"`, `"guardian"` or `"student"`, all rendered by the current welcome view); `set_pending_role` exists but only CP2 calls it. `welcome-done` doesn't exist yet in CP1, so step 6's "guardian just added a student, no intent" returns `reverse("welcome")` (today's behaviour, `welcome.py:132-133`).
- Copy the host check from `django/contrib/auth/views.py` (`RedirectURLMixin.get_redirect_url`).
- Pitfalls: `resolve()` needs a path, not a URL; `session-sign-up` has two patterns (with and without `student_id`, `urls.py:213-224`); never store `request.GET` values other than the resolved int `pk`.
- Proof: `… manage.py test coderdojochi.tests.test_onboarding_intent` passes. Cases: `https://evil.example/classes/1/`, `//evil.example/classes/1/`, `/\evil.example`, `https:/evil.example`, `javascript:alert(1)`, `account_home`, `/account/logout/`, `/dj-admin/` → no intent; `/classes/1/` with `enroll` → `session/guardian`; `/classes/1/` without `enroll` → `session/None`; `/old/meetings/1/` → `meeting/None`; inactive or missing session → router returns `account_home` and clears; guardian with a meeting intent → meeting page, intent cleared, `MISMATCH_MESSAGE["guardian"]` flashed (step 1); a user with `role="teacher"` counts as no role; an intent older than 24 h is ignored (patch `timezone.now`); `set_intent(..., role=None)` over a same-class intent with `role="guardian"` keeps `guardian`; a class whose parent window isn't open, or with `external_enrollment_url`, plus `last_student` → `session-detail`, not `session-sign-up`. Test users are built with `first_name`, and mentors with `birthday`, `phone` and `zip`, unless the case is about them being missing (`CDCUserFactory` sets no name). There's no `MeetingFactory`/`GuardianFactory`/`StudentFactory`: build `Meeting` with a `MeetingType` and `Location` (the confirmation email reads both, `meetings.py:168-191`), and copy `Guardian`/`Student` creation from `test_signup_and_welcome.py:47-66`.

**1B. Welcome view stops redirecting to `next`.** Files: `coderdojochi/views/welcome.py`, `coderdojochi/tests/test_welcome_redirects.py`.
- `dispatch`: call `intent.intent_from_legacy_next(request)` once; stop putting `next_url` in kwargs or context (the template's `{% if next_url %}` actions then render `action=""`, which posts back to the same URL; no template edit needed).
- Replace every `redirect(next_url)` and every `f"{next_url}?enroll=…"` (lines 38, 103-109, 129-134, 169-225) with `redirect(intent.next_url(request))`. In `add_student`, call `intent.set_last_student(request, new_student.id)` first. Keep the two welcome emails and `merge_global_data` exactly.
- Pitfall: `redirect()` treats a bare string as a URL name; `next_url()` always returns a path, so wrap nothing else.
- Proof: test file passes. Cases: complete mentor (first name, birthday, phone, zip, so the case still holds at CP2), `GET /welcome/?next=https://evil.example/` → `Location == reverse("account_home")`; a named role-less user picking Volunteer with the same `next` → `account_home`; a nameless mentor still gets the 200 `MentorForm` page (no loop); legacy parent flow `/welcome/?next=/classes/<pk>/&enroll=True` → contact form → student form → `Location == reverse("session-sign-up", kwargs={"pk": pk, "student_id": new.id})`; welcome email in `mail.outbox` (count only the `welcome_guardian` subject; tests that sign up through allauth also get allauth's confirmation email, since verification is "optional").

**1C. Session views: no 404, no Referer, own students only.** Files: `coderdojochi/mixins.py`, `coderdojochi/views/sessions.py`, `coderdojochi/tests/test_session_onboarding.py`.
- Both mixins use `intent.user_role(user)` instead of `user.role`: `RoleRedirectMixin` (`mixins.py:24`) treats an unknown role as none, and `RoleTemplateMixin` (`mixins.py:7-16`) falls back to the plain `template_name` instead of an unbound variable (today a 500).
- `RoleRedirectMixin.dispatch`: replace the `next` string with `intent.set_intent(request, "session", session_obj.pk, "guardian" if "enroll" in request.GET else None)` and `redirect("welcome")`. Keep the warning message.
- `SessionDetailView.get` (`sessions.py:153-165`): an authenticated user with no role (or a role other than mentor/guardian) → `set_intent(..., role=None)` → `redirect("welcome")`.
- `check_access` (269, 278): redirect to `kwargs["session_obj"].get_absolute_url()` instead of `HTTP_REFERER`/`/dojo`, in both the waiver and the background-check branch.
- `dispatch` (236-239): `get_object_or_404(Student, id=kwargs.get("student_id"), guardian=kwargs["guardian"])`, so a guardian on `/classes/<pk>/sign-up/` without a student id gets a 404, not a `KeyError` 500.
- `check_access`, guardian branch: before the student limits, refuse with a message and redirect to the class page when the session has `external_enrollment_url`, or when the parent window isn't open yet (`start_date - MAX_DAYS_FOR_PARENTS > now`; copy the computation from `guardian/sessions.py:39-52`). Today only the class page hides the buttons; the sign-up URL itself accepts the Order. Applies only to new sign-ups (`not user_signed_up`), so cancelling still works.
- `SessionSignUpView.dispatch`: a password-protected session the user hasn't unlocked → `redirect("session-password", pk=…)`, reusing `SessionDetailView.validate_partner_session_access` (today only the detail page checks it, so the router's direct `session-sign-up` destination would skip it).
- Pitfall: `SessionDetailView` also handles password-protected sessions first (`sessions.py:147-151`); keep that order.
- Proof: test file passes. Cases: role-less user `GET /classes/<pk>/` → 302 to `/welcome/`, `get_intent` is the class with `role=None`; adult mentor needing a background check **and** an unwaived minor mentor, each `POST /classes/<pk>/sign-up/` with `HTTP_REFERER="https://evil.example/"` → `Location` is the class page; guardian B on guardian A's student → 404; guardian on the student-less sign-up URL → 404; password session not unlocked → `session-password`; guardian `POST` for a class 31+ days out → class page with the message, no `Order`; same for a class with `external_enrollment_url`; a user with `role="teacher"` on a sign-up URL → `/welcome/`, not a 500.

**1D. Account home and the allauth adapter.** Files: `accounts/views.py` (lines 52-66 only), `accounts/adapter.py`, `coderdojochi/settings.py` (allauth block only), `accounts/test_onboarding_redirects.py`.
- `AccountHomeView.dispatch`: no role → `intent.intent_from_legacy_next(self.request)` → `redirect("welcome")`. Keep the warning message when there was no `next`.
- `AccountAdapter(DefaultAccountAdapter)`: `get_login_redirect_url` and `get_signup_redirect_url` return `intent.next_url(request)`. `ACCOUNT_ADAPTER = "accounts.adapter.AccountAdapter"`.
- `AccountAdapter.post_login(self, request, user, **kwargs)`: if `kwargs.get("redirect_url") or get_next_redirect_url(request)`, call `intent.clear_intent(request)`; then `return super().post_login(request, user, **kwargs)`. This covers password login, signup and Google (Google's `next` arrives as `redirect_url`).
- Pitfall: don't touch PR 1661's lines (14, 176-241). `LOGIN_REDIRECT_URL` stays; the adapter now decides instead.
- Proof: test file passes. Cases: `/account/?next=https://evil.example/` as role-less → `Location == "/welcome/"`; with an intent in the session, signup POST (captcha patched) → `Location == "/welcome/"`, and a complete mentor logging in with a meeting intent → `Location == meeting.get_absolute_url()`; `/account/login/?next=/account/` still lands on `/account/` (allauth's `next` wins) **and** leaves no intent behind; a logged-in user opening `/account/login/` with an intent is redirected without a crash; `AccountAdapter().post_login(request, user, redirect_url="/account/", …)` called directly with an intent stored and **no** `next` in the request clears the intent (this is what Google's callback looks like); `test_legacy_meeting_next_still_works` (`/account/?next=/old/meetings/<pk>/` as role-less → `/welcome/` with a `meeting` intent; after picking Volunteer → the meeting).

**1E. Meeting sign-up works.** Files: `coderdojochi/views/meetings.py`, `coderdojochi/tests/test_meeting_sign_up.py`.
- `meeting_sign_up`: `@login_required`; the meeting must be `is_active` unless the user is staff (`get_object_or_404(Meeting.objects.filter(...), pk=pk)`, matching `MeetingDetailView.get_queryset` for a logged-in user, `meetings.py:50-59`; no `is_public` filter, since logged-in users see private meetings there and the view is `login_required`); no role → `set_intent(request, "meeting", pk, "mentor")` → `redirect("welcome")`; a guardian → `messages.info(…"Meetings are for volunteers…")` → `redirect("meeting-detail", pk)` (no intent); fix line 216 to `redirect("meeting-detail", meeting_obj.id)`.
- Proof: test file passes. Cases: mentor `POST /old/meetings/<pk>/register/` → 302 to the meeting, `MeetingOrder` active, one email in `mail.outbox`; anonymous POST → 302 to login; role-less → `/welcome/` with the meeting intent; guardian → the meeting page, no `MeetingOrder`.

**Checkpoint 1 check (lead):** full suite, ruff, pre-commit; **every Proof row whose test file is created in CP1** (`test_onboarding_intent`, `test_welcome_redirects`, `test_session_onboarding`, `test_meeting_sign_up`, `accounts/test_onboarding_redirects`), which covers AC 1, 2, 3, 5, 6, 8, 9 and 11, and AC 7 only at the adapter level (CP1 has no way to store an intent for a logged-out visitor, so the test seeds the session; the real "I already have an account" round trip is proved in CP2 by `test_onboarding_flow::test_existing_user_login_round_trip`); the probe scenario (mentor, `?next=https://evil.example/`) now returns `account_home`. Then a PR with CI green and Ali's OK to release.

### Checkpoint 2: the new flow (after PR 1661 is merged)

**2A runs first, alone** (2B's round-trip tests need its endpoints; 2C and 2D reverse its URL names). It adds a stub `WelcomeDoneView` (renders `welcome.html` with the current context) to `coderdojochi/views/welcome.py` so `urls.py` imports. Then 2B, 2C and 2D run in parallel; 2B replaces the stub.

**2A. Start endpoints.** Files: `coderdojochi/onboarding/start.py`, `coderdojochi/urls.py` (class, meeting and welcome blocks: `urls.py:47-84`, `167-227`, `276-283`), `coderdojochi/views/welcome.py` (stub `WelcomeDoneView` only), `coderdojochi/tests/test_onboarding_start.py`.
- One `StartView(View)` with class attributes `kind`, `role`, `new_student` (set per URL via `as_view(kind=…, role=…, new_student=…)`), and `get()`: for kind `none` (`add-student-start`) there's no object: anonymous → `redirect_to_login` (`account_login`, with `next` = this URL, which allauth validates), else `set_intent` and `redirect(intent.next_url(request))`. Otherwise `get_object_or_404` the session/meeting (session: active, and partner-password access via `SessionDetailView.validate_partner_session_access` else `redirect("session-password", pk=…)`; meeting: active, and `is_public` when anonymous); `set_intent`; anonymous → `redirect("account_signup")`; else `redirect(intent.next_url(request))`. Every response sets `X-Robots-Tag: noindex, nofollow`. Register the five start URLs from the table, plus `path("welcome/done/", WelcomeDoneView.as_view(), name="welcome-done")` (the view is 2B's, imported from `coderdojochi.views.welcome`).
- Pitfall: these must never be in `PUBLIC_CACHE_VIEW_NAMES`, and the public class page itself must not write the session.
- Proof: test file passes. Cases: anonymous `GET /classes/<pk>/enroll/` → 302 to `/account/signup/` with a `sessionid` cookie and the intent stored; anonymous `GET /classes/<pk>/` sets no cookie; complete guardian with students `GET /classes/<pk>/enroll/` → the class page; `GET /classes/<pk>/enroll/new-student/` → `/welcome/`; mentor on `/classes/<pk>/enroll/` → class page, intent cleared (mismatch); password session not unlocked → `session-password`; anonymous on a non-public meeting's attend link → 404; `X-Robots-Tag` present; anonymous `GET /welcome/add-student/` → login, no intent stored.

**2B. Onboarding steps.** Files: `coderdojochi/views/welcome.py`, `coderdojochi/onboarding/forms.py`, `coderdojochi/onboarding/intent.py` (CP2 router changes: step 2 becomes the pending-role rule, step 3 gains `guardian-about`, step 4 (mentor) is added, step 6's no-intent guardian destination becomes `welcome-done`, `set_pending_role` rewrites the intent), `coderdojochi/tests/test_onboarding_intent.py`, `coderdojochi/tests/test_welcome_redirects.py` and `accounts/test_onboarding_redirects.py` (retire or replace the CP1-only tests, see "CP1 tests at CP2" under Proof), `coderdojochi/templates/onboarding/{role,guardian,mentor}.html`, `coderdojochi/templates/welcome.html`, `coderdojochi/tests/test_onboarding_flow.py`, `coderdojochi/tests/test_frontend_stack.py` (only the two welcome tests, about 32 lines above their `main` position after PR 1661, and `PYTHON_GLOBS`: add `coderdojochi/onboarding/*.py` and `accounts/templatetags/*.py`; never add to `LEGACY_TEMPLATES`, which only shrinks), `coderdojochi/tests/test_signup_and_welcome.py` (`WelcomeNextStepsTest` must GET `reverse("welcome-done")`: after CP2 a complete guardian on `/welcome/` is redirected to `account_home`, so the test would read an empty body).
- `WelcomeView` becomes a step dispatcher: `intent.current_step(request)` picks the template; `None` → `redirect(intent.next_url(request))` (never to itself). Add router step 4 (mentor) to `intent.py`. `WelcomeDoneView` (same file) renders the reduced `welcome.html` (PR 1655 buttons) and is never a router step. Every form carries a hidden `step` field, and the POST picks its handler from that field, not from `current_step` (so a stale second POST still reaches the duplicate guard); an unknown `step` re-renders the current step. Role step: POST `role` calls `intent.set_pending_role` (session), not the user. Parent page: `GuardianForm(prefix="guardian")` + `StudentForm(prefix="student")`; both valid → in one `transaction.atomic()`: lock and **re-read** the user (`user = User.objects.select_for_update().get(pk=request.user.pk)`, never the cached `request.user`); on the first-time parent page (`step=guardian`), if `intent.user_role(user)` is already set, skip creation and redirect to `next_url` (double submit); `Guardian.objects.get_or_create(user=user)` (`Guardian.user` and `Mentor.user` are `ForeignKey`s, `guardian.py:9`, `mentor.py:28`, so a second row would make every `get_object_or_404(Guardian, user=…)` raise `MultipleObjectsReturned`); save the form onto it and call `save_m2m()` for `race_ethnicity`; `user.role = "guardian"`; save the student with that guardian; `set_last_student`. Send `welcome_guardian` (copy `welcome.py:206-220`) in `transaction.on_commit`, then redirect to `next_url`. "About you" only variant (`guardian-about`) when the guardian already has students; student-only variant when they have phone and zip. Volunteer step: same pattern: `atomic` + `select_for_update` + `Mentor.objects.get_or_create(user=user)`, `MentorStartForm(instance=mentor)`, same locked re-read and `user_role` guard on `step=mentor` for users with no role (an existing mentor on this step just saves the form), `role = "mentor"`, `welcome_mentor` (copy `welcome.py:176-198`) in `on_commit`, redirect to `next_url`. The switch link is a POST of the other `role` to the same view (`set_pending_role`). Tests wrap submits in `self.captureOnCommitCallbacks(execute=True)` before asserting `mail.outbox`.
- `MentorStartForm(ModelForm)`: `Mentor`, fields `birthday`, `phone`, `zip`, all required. Copy the widgets from `MentorForm` (`forms.py:172-204`) and `ZIP_CODE`; zip `required=True` here (Ali's decision), still optional on the account page.
- Pitfalls: `Mentor.save()` sends a Slack notification on create (`mentor.py:144-146`); the tests already patch or tolerate it (see `test_slack_notifications.py`). `Guardian` creation must not happen on the role click (no orphans if the user switches). Existing role-set users without phone/zip (mentors with no birthday) will get the step at their next login; that's intended, but **send `welcome_guardian`/`welcome_mentor` only when `intent.user_role(user)` was `None` before the submit** (not raw `user.role`: a user with an unknown role such as `"bogus"`, `accounts/tests.py:65-82`, would otherwise skip creation and loop back to the parent page forever) (today only `create_new_user` sends them, `welcome.py:148-225`). `WelcomeDoneView` is `login_required` and sends anyone who isn't a guardian to `account_home`.
- Templates: CP4 vocabulary, `{% include "account/_form.html" %}` for fields, one `<h1>`, the intent line ("Enrolling in *Course title*, *date*") at the top, the switch link under the submit. Mobile first: one column.
- Proof: test file passes; `test_frontend_stack` passes. Cases in "Proof" AC 2, 3, 4, 5, 6.

**2C. Coderdojochi template links.** Files: `coderdojochi/templates/public/session_detail.html`, `coderdojochi/templates/guardian/session_detail.html`, `coderdojochi/templates/mentor/session_detail.html`, `coderdojochi/templates/meeting_detail.html`, `coderdojochi/tests/test_onboarding_links.py`.
- Every start link gets `rel="nofollow"`. Public class: "Enroll now" → `{% url 'session-enroll-start' object.pk %}`; add "Volunteer at this class" → `{% url 'session-volunteer-start' object.pk %}` styled as the secondary button. Guardian class 63, 69 → `{% url 'session-add-student-start' object.pk %}`. Meeting 94 → `{% url 'meeting-attend-start' object.pk %}` with "Log in or sign up to attend" when logged out and "Volunteer to attend" for logged-in role-less users; logged-in guardians see the 1E text "Meetings are for volunteers…" and no link; fix "object" → "meeting" at 88 and 94. Mentor class page: above the sign-up button, `{% if account.awaiting_minor_waiver %}` the under-18 note, `{% elif account.needs_background_check %}` the background-check link (copy the wording from `account/mentor/home.html:28-32`; `account` is the mentor, `mentor/sessions.py:27`).
- Proof: test file passes: each page's HTML contains the new `href` and no `?next=`.

**2D. Accounts template links.** Files: `accounts/templates/account/guardian/home.html`, `accounts/templates/account/signup.html`, `accounts/templates/account/login.html`, `accounts/templatetags/onboarding.py` (new tag `onboarding_intent` that returns the intent's object title and date, or nothing), `accounts/test_onboarding_templates.py`.
- Guardian home 54 → `{% url 'add-student-start' %}`. Signup 13: `action="{% url 'account_signup' %}"` only; keep allauth's hidden `next` input. Signup and login: intent line from the tag.
- Proof: test file passes: signup HTML has no `enroll` and no unencoded `next` in `action`; with a class intent the course title shows.

**Checkpoint 2 check (lead):** full suite, ruff, pre-commit, every mutation in Proof except rows retired in "CP1 tests at CP2", then the manual walk-through. PR with CI green; Ali's OK to release.

## Checkpoints

| # | Delivers | Check | Can merge |
| --- | --- | --- | --- |
| 1 | Open redirect closed; meeting sign-up 500, role-less 404, Referer redirect and student IDOR fixed; old links still work | Suite + CP1 mutations; probe returns `account_home` | Any time (no template, no PR 1661 hunk) |
| 2 | Start buttons, inferred role, one-page parent form, volunteer step, intent line, no `?next=` in templates | Suite + CP2 mutations + manual walk-through | After PR 1661 merges |

## How to run it

Read the whole plan first. Run it as the lead: **you write no code.**

1. Branch `claude/onboarding-cp1` from the latest `origin/main` (CP2: `claude/onboarding-cp2`, from `main` after PR 1661 and CP1 are merged).
2. At the start of each checkpoint, give every task that can run in parallel to its own sub-agent, all at once (model `sonnet`; re-run a task on Opus if it fails its Proof line or the files don't hold up). Each brief names its task, its files and only those, this plan's path and the sections to read ("Read first", the task, "Proof"), the bar (the task's Proof line plus its mutations), and the report format: files changed; commands run with their last 20 lines; anything that didn't match the plan. Tell it **not to run git**, not to edit files outside its list, and never to send email.
3. You alone: read the actual files (not the report), run the checkpoint's check and every mutation for that checkpoint, commit, and write the result and evidence (test counts, each mutation's failing test name) into Progress.
4. Anything not in the plan (a missing field, a page that can't be reached, a product question) goes into the plan first. Product questions go to Ali with `AskUserQuestion`; never guess.
5. Per checkpoint: commit (messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`), push, open a PR (body ends with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`), CI green. Then the release runbook in `docs/plans/dependency-upgrades-2026-11.md` "How to run it" step 4, every step with Ali's explicit OK: staging, then merge, then prod; watch Sentry for an hour. No migrations in this plan. Rollback: `infra/vm/release.sh --target prod --force <previous-prod-sha>`.
6. After each checkpoint, if your context window is half full, write which checkpoint is next in Progress and stop. A fresh session continues from this plan.

## Proof

### Per acceptance criterion

For each test: write it, make the one-line change, confirm the named test fails, then undo it with the exact reverse edit (never `git checkout`/reset).

| AC | Test (file::name) | One-line change that must make it fail |
| --- | --- | --- |
| 1 | `test_onboarding_intent::test_off_site_next_is_ignored` (the URL list in 1A) | In `intent_from_legacy_next`, replace the `url_has_allowed_host_and_scheme(...)` call with `True` (`https://evil.example/classes/1/` then stores an intent) |
| 1 | `test_welcome_redirects::test_mentor_off_site_next_goes_home` | Re-add `if request.GET.get("next"): return redirect(request.GET["next"])` at the top of the mentor branch in `WelcomeView.dispatch` |
| 1 | `test_session_onboarding::test_blocked_mentor_not_sent_to_referer` | Restore `request.META.get("HTTP_REFERER", "/dojo")` at `check_access`'s background-check branch |
| 1 | `test_onboarding_links::test_no_next_in_templates` (CP2) | Put `?next={{ request.path }}` back on `guardian/session_detail.html`'s add-student link |
| 2 | `test_welcome_redirects::test_legacy_class_enroll_lands_on_sign_up` (CP1) | In `next_url`, drop the `student_id` kwarg from the `session-sign-up` reverse (lands on the plain sign-up URL) |
| 2 | `test_onboarding_flow::test_class_enroll_round_trip` (CP2: anonymous start → signup → parent page → `Location == reverse("session-sign-up", kwargs={"pk": s.pk, "student_id": new.pk})`) | In `next_url`, return `reverse("account_home")` instead of the session destination |
| 3 | `test_meeting_sign_up::test_mentor_post_redirects_to_meeting` | Change `"meeting-detail"` back to `"meeting_detail"` in `meeting_sign_up` |
| 3 | `test_onboarding_flow::test_meeting_round_trip` (start → signup → volunteer step → `Location == meeting.get_absolute_url()`) | In `next_url`, map `kind == "meeting"` to `reverse("account_home")` |
| 4 | `test_onboarding_flow::test_class_volunteer_round_trip` (lands on class; adult needs background check → class page shows the note; `POST` sign-up flashes it and stays on the class) | In `coderdojochi/urls.py`, change `session-volunteer-start`'s `as_view(role="mentor")` to `role="guardian"` |
| 4 | `test_onboarding_flow::test_minor_volunteer_sees_waiver_note` | In `MentorStartForm`, drop `birthday` from `fields` |
| 5 | `test_onboarding_flow::test_enroll_intent_skips_role_screen` | In the router, ignore `intent["role"]` when the user has no role |
| 5 | `test_onboarding_flow::test_switch_role_has_no_orphan` (no intent: POST `role=guardian`, then switch to volunteer, submit the volunteer step → no `Guardian` row) | Create the `Guardian` on the role POST instead of on the parent-form POST |
| 5 | `test_onboarding_flow::test_guardian_with_students_gets_about_only` (existing guardian with a student and no zip, enroll intent → page has no student fields) | In `current_step`, drop the `guardian-about` branch |
| 2 | `test_session_onboarding::test_sign_up_refused_before_window` (CP1) | Delete the parent-window check in `check_access` |
| 2 | `test_onboarding_flow::test_double_submit_one_guardian` (POST the parent page twice with the same `step=guardian` body; the hidden `step` makes the second POST reach the guard → one `Guardian`, one student, one welcome email) | Delete the "`user.role` already set → skip creation" guard |
| 2 | `test_onboarding_flow::test_stray_guardian_row_reused` (role-less user who already has a `Guardian` row, as today's `welcome.py:151-161` can leave, submits the parent page → still exactly one row) | Replace `get_or_create` with `create` |
| 5 | `test_onboarding_flow::test_switch_on_volunteer_intent_reaches_parent_page` (volunteer intent for a class, switch to Parent, submit → `session-sign-up` for the new student, no mismatch flash) | In `set_pending_role`, don't rewrite `intent["role"]` |
| 6 | `test_onboarding_flow::test_existing_mentor_step_sends_no_welcome` (saved mentor missing a zip submits the volunteer step → `mail.outbox` has no `Welcome!`) | Drop the "role was `None` before" condition on the welcome email |
| 6 | 5 | `test_onboarding_intent::test_browsed_class_then_volunteer_no_mismatch` (role-less user browses a class, intent `session`/`None`, picks Volunteer, completes the step → class page, no mismatch flash) | In step 1, drop the `intent["role"] and` guard |
| 2 | `test_onboarding_flow::test_unknown_role_completes_parent_page` (`role="bogus"` user submits the parent page → one `Guardian`, role `guardian`, no loop) | Change the guard to read raw `user.role` |
| 3 | `test_meeting_sign_up::test_private_meeting_ok_for_mentor` (CP1: logged-in mentor POSTs a non-public, active meeting → 302 to it, order saved) | Add `is_public=True` to the `meeting_sign_up` queryset |
| 6 | `test_onboarding_flow::test_welcome_done_guardians_only` (anonymous → login; mentor → `account_home`) | Remove `login_required` from `WelcomeDoneView` |
| 7 | `test_onboarding_flow::test_existing_user_login_round_trip` (CP2: anonymous → `session-enroll-start` → signup page → login page → log in as a complete guardian → class page) | In `StartView`, redirect anonymous users to `account_login` with no intent set |
| 3 | `test_meeting_sign_up::test_inactive_meeting_404` (CP1) | Drop `is_active=True` from the `meeting_sign_up` queryset |
| 6 | `test_onboarding_intent::test_intent_cleared_after_destination` | Delete the `clear_intent(request)` call in `next_url`'s destination branch |
| 6 | `test_onboarding_flow::test_add_student_does_not_loop` (guardian home → add-student-start → submit → `welcome-done`, then `/welcome/` again → `account_home`) | In step 5, drop the "and no `last_student` set yet" condition |
| 6 | `accounts/test_onboarding_redirects::test_valid_next_clears_intent` (password login with `next=/account/`, then the direct `post_login(redirect_url=…)` case) | In `post_login`, drop `kwargs.get("redirect_url") or` from the condition (the Google-shaped case then keeps the intent) |
| 5 | `test_onboarding_intent::test_role_mismatch_goes_to_object_page` (asserts the page **and** the `MISMATCH_MESSAGE` flash: without step 1 the destination is the same page, so only the message tells them apart) | Delete router step 1 |
| 5 | `test_session_onboarding::test_browsed_class_keeps_role_screen` (role-less user on a class page → `/welcome/`, and `get_intent(...)["role"] is None`; the CP1 welcome view always shows the role screen, so the HTML can't tell) | In `SessionDetailView.get`'s role-less branch, pass `role="guardian"` |
| 1 | `test_welcome_redirects::test_named_new_mentor_no_loop` (CP1: named mentor with no zip → `account_home`, not `/welcome/`) | Add a mentor step (`if not mentor.zip: return reverse("welcome")`) to the CP1 router |
| 1 | `test_onboarding_intent::test_cp1_roleless_mentor_intent_shows_welcome` (CP1: role-less user, meeting intent with `role="mentor"` → `/welcome/`, intent kept) | In CP1 step 2, skip it when `intent["role"]` is set |
| 7 | `accounts/test_onboarding_redirects::test_login_with_meeting_intent` | Make `AccountAdapter.get_login_redirect_url` return `super().get_login_redirect_url(request)` |
| 8 | `test_session_onboarding::test_roleless_class_page_goes_to_onboarding` | Delete the role-less branch in `SessionDetailView.get` |
| 8 | `test_meeting_sign_up::test_anonymous_post_goes_to_login` | Remove `@login_required` from `meeting_sign_up` |
| 9 | `test_session_onboarding::test_cannot_enroll_other_guardians_student` | Remove `guardian=kwargs["guardian"]` from the `Student` lookup |
| 10 | `test_onboarding_start::test_public_class_page_sets_no_cookie` (only this test catches it: `session-detail` isn't in `PUBLIC_CACHE_VIEW_NAMES`, so `test_cache_headers` stays green) | Call `set_intent(...)` in `public.SessionDetailView.get_context_data` |
| 11 | `accounts/test_onboarding_redirects::test_legacy_meeting_next_still_works` (`/account/?next=/old/meetings/<pk>/` as role-less → volunteer → meeting) | In `intent_from_legacy_next`, remove `"meeting-detail"` from the accepted names |

### CP1 tests at CP2

2B owns these. Each one is retired (deleted with its Proof row marked "retired at CP2" in Progress) or replaced as listed; the CP2 check fails if any of them is still red.

| CP1 test | At CP2 |
| --- | --- |
| `test_onboarding_intent::test_cp1_roleless_mentor_intent_shows_welcome` | Replaced by `test_onboarding_flow::test_meeting_round_trip` (the volunteer step now shows); retire |
| `test_welcome_redirects::test_named_new_mentor_no_loop` | Replaced: a named mentor with no zip now gets the volunteer step once, then `account_home` (`test_onboarding_flow::test_existing_mentor_step_sends_no_welcome` covers it); retire |
| `test_welcome_redirects` "nameless mentor gets the 200 `MentorForm`" case | Retire (the volunteer step replaces `MentorForm` on `/welcome/`) |
| `test_welcome_redirects::test_legacy_class_enroll_lands_on_sign_up` | Keep the URL, change the posts to the one prefixed parent form (`guardian-…` + `student-…` fields) |
| `test_welcome_redirects` "named role-less user picking Volunteer with an off-site `next` → `account_home`" case | Keep; at CP2 it also posts the volunteer step (`step=mentor`, birthday, phone, zip), then asserts `account_home` |
| `accounts/test_onboarding_redirects::test_legacy_meeting_next_still_works` | Keep; at CP2 "after picking Volunteer" becomes "after picking Volunteer and posting the volunteer step", then the meeting |
| `test_welcome_redirects::test_mentor_off_site_next_goes_home` | Keep the test (its mentor is complete, so it still lands on `account_home`); its mutation becomes "in `WelcomeView.get`, return `redirect(request.GET[\"next\"])` when present" |

### Whole-build commands (every checkpoint)

```bash
DJANGO_SETTINGS_MODULE=coderdojochi.test_settings uv run python manage.py test
```

```bash
uv run ruff check .
```

```bash
uv run ruff format --check .
```

```bash
uv run pre-commit run --all-files
```

### Manual (CP2, local only)

`docker compose up --build` with `EMAIL_BACKEND=anymail.backends.test.EmailBackend` and `RESEND_API_KEY=` set **in `.env`** (`docker-compose.yml:5` uses `env_file: .env` only; shell variables don't reach the container); confirm with `docker compose run --rm app uv run python manage.py shell -c "from django.conf import settings; print(settings.EMAIL_BACKEND)"` before any form submit. Local signup sends nothing with that backend. At 1280 px and 390 px:

1. Logged out, open a class → Enroll now → sign up → one parent page → confirmation for the new student → Confirm. Count screens: 3 after the class page.
2. Logged out, open a meeting → Log in or sign up to attend → sign up → volunteer step → meeting page → Attend Meeting → success message.
3. Logged out, open a class → Volunteer at this class → sign up (birthday 16 years ago) → class page → Sign up → under-18 note, still on the class.
4. Existing guardian: class → Enroll now → "I already have an account" → log in → class page with their students.
5. `/welcome/?next=https://evil.example/` as a mentor → account home.
6. Normal use still works: log in from the nav with no intent → account home; guardian home "Add another student" → student form → "Find a class / Done" page.

On staging and prod after each release (page loads only, no submits): the class page shows both buttons; `/classes/<pk>/enroll/` logged out → 302 to `/account/signup/`; `/welcome/?next=https://evil.example/` logged out → 302 to login with no off-site hop.

## Pitfalls

- **Edge cache.** `coderdojochi/middleware.py` never caches a response that sets a cookie and the Transform Rule strips query strings only on the allowlisted paths. Writing the session anywhere except the start endpoints (and the steps behind login) would add a `Set-Cookie` to public pages and silently drop them from the cache.
- **`redirect()` and URL names.** `django.shortcuts.redirect("account_home")` reverses a name; a request value passed to it can pick any named URL. Only pass `reverse()` results or literal names.
- **Session `cycle_key`.** Django keeps anonymous session data on `login()`; allauth's logout flushes it. Don't call `request.session.flush()` anywhere in the flow.
- **Two `session-sign-up` patterns** share one name (`urls.py:213-224`); reverse with and without `student_id` explicitly.
- **Slack and email on save.** `Mentor.save()` posts to Slack on create (1A pins `SLACK_WEBHOOK_URL = ""` in `test_settings.py`); welcome emails go through `coderdojochi.util.email`. Tests use anymail's test backend (`test_settings.py:39`), which fills `mail.outbox`; never run a real send.
- **Line numbers move after PR 1661** (`forms.py` gains lines around 100-125 and loses `form-control` on the `MentorForm` widgets; `test_frontend_stack.py` shrinks). CP2 tasks re-find every line on the new `main`.
- **reCAPTCHA in tests.** Patch `django_recaptcha.fields.ReCaptchaField.validate` or signup always fails with "captcha: This field is required."
- **`test_frontend_stack`.** The ratchet fails on any legacy class in a new template, and two tests hit `/welcome/` (one expects the mentor birthday input, which moves to `onboarding/mentor.html`). Update those tests in 2B, not elsewhere.

## Related issues

- #1551 (multiple guardian emails): independent. If it lands first, the parent page's "About you" section may gain an extra email field; the intent and router don't change.
- #1553 (class prerequisites): the router's class destination is the natural place to show "this class needs X". Build it as a check in `SessionSignUpView.check_access` (redirects to the class page after CP1), not in onboarding.

## Plan review findings

Fresh sub-agent review, 2026-11-26. Every finding is folded into the sections above.

| # | Severity | Section | Finding | Fix in plan |
| --- | --- | --- | --- | --- |
| 1 | blocker | CP1 router, 1B | A mentor step in CP1 loops `/welcome/` → `/welcome/`, since the CP1 welcome view redirects every named mentor; test factories set no name, so tests wouldn't see it | No mentor step in CP1 (the mentor step is CP2 only); test users get names; `test_named_new_mentor_no_loop` |
| 2 | blocker | CP2 router, 2D | The guardian home "Add another student" link to plain `/welcome/` never shows the student form; a new parent with no intent went to `account_home` | Intent kind `none` + `add-student-start`; step 4 is "0 students, or `new_student` and no `last_student`" |
| 3 | should-fix | Router | `new_student` and the done page could loop | Step 4 ends once `last_student` is set; intent and `last_student` cleared together; done page is its own URL `welcome-done` |
| 4 | should-fix | 1C, converter | Hardcoded `guardian` intents skip the role screen for users who only browsed | `role=None` allowed; only start buttons and `enroll` set a role |
| 5 | should-fix | Router, 1E | A guardian clicking Attend, or a mentor clicking Enroll, had no defined path | Router mismatch step (now step 1); 1E guardian branch |
| 6 | should-fix | 2A, 1C | Start endpoints and the direct `session-sign-up` destination skipped partner passwords; non-public meetings were reachable by anonymous users | Password check in `StartView` and `SessionSignUpView`; `is_public` for anonymous |
| 7 | should-fix | CP1 order | 1B–1E import `intent.py`; one AC 11 test lived in the wrong task's file | 1A runs first; test moved to 1D's file |
| 8 | should-fix | AC 4 | No task added the class-page note | 2C edits `mentor/session_detail.html`; AC 4 reworded |
| 9 | should-fix | Safety | Slack could post from tests; the email backend is anymail's test backend, not locmem | `SLACK_WEBHOOK_URL = ""` in `test_settings.py` (1A); wording fixed |
| 10 | should-fix | Edge cache | Crawlers following GET start links would mint sessions | `rel="nofollow"` + `X-Robots-Tag`; `robots.txt` is a follow-up |
| 11 | should-fix | Adapter | When allauth's `next` wins, a stored intent would fire at a later login | `LoginView`/`SignupView.form_valid` clear it; test added |
| 12 | nit | Read first | Line numbers move after PR 1661; `LEGACY_TEMPLATES` only shrinks; `PYTHON_GLOBS` misses the new code | Pitfall added; 2B adds the globs, never touches `LEGACY_TEMPLATES` |
| 13 | nit | Proof | `test_cache_headers` can't catch AC 10; minor-waiver Referer branch untested; `role` is an `as_view` kwarg; no Meeting/Guardian/Student factories | Fixed in the table, 1C and 1A |
| 14 | nit | 1C | Guardian on the student-less sign-up URL → `KeyError` 500; unknown roles | `kwargs.get` + 404; unknown role counts as none |
| 15 | nit | 1B | The off-site test needed a complete mentor | 1B Proof spells it out |

**Second review** (fresh sub-agent, 2026-11-26, after the first was folded in). Every finding is folded into the sections above.

| # | Severity | Section | Finding | Fix in plan |
| --- | --- | --- | --- | --- |
| 1 | blocker | Router, 1C | The router sends parents straight to `session-sign-up`, which never checks the 30-day parent window or `external_enrollment_url` (only the class page does) | `check_access` refuses both (1C); router falls back to `session-detail`; tests added |
| 2 | should-fix | Proof AC 5 | `test_switch_role_has_no_orphan` never POSTs `role=guardian` with an enroll intent, so its mutation survives | Test starts with no intent and POSTs `role=guardian` first |
| 3 | should-fix | Proof AC 5 | Deleting the mismatch step lands on the same page | Test asserts the flash message |
| 4 | should-fix | Router | Mismatch ran after the profile steps | Mismatch is now step 1 |
| 5 | should-fix | CP1 router | A role-less user with a `mentor` intent skipped the role screen in CP1 and lost the intent; 1E contradicted "only start endpoints set a role" | CP1 step 2 ignores the intent's role; one "who sets a role" list |
| 6 | should-fix | 2B | An existing guardian with students but no zip was forced to add a student | `guardian-about` variant |
| 7 | should-fix | API | `WelcomeView` couldn't tell which step to render; the router never read `onboarding_role` | `current_step`, `set_pending_role`, "pending role" rule; `clear_intent` drops all three keys |
| 8 | should-fix | 2B | `Guardian.user`/`Mentor.user` are FKs: a double submit makes duplicate rows and 500s for good; email sent inside `atomic`; `save_m2m` missing | `select_for_update` + `get_or_create`, `on_commit` emails, `save_m2m`; double-submit test |
| 9 | should-fix | 2B | `WelcomeNextStepsTest` breaks once `/welcome/` redirects complete guardians | It GETs `welcome-done` |
| 10 | should-fix | 1C | The role-less class-page branch overwrote a stronger same-class intent | `set_intent` keeps the role for the same `(kind, pk)` |
| 11 | should-fix | CP2 order | 2A imports 2B's view; 2C/2D/2B need 2A's names; 2A's scope missed the welcome URL block; 1D's legacy test needs 1B | 2A first with a stub; scope widened; 1D Proof after 1B |
| 12 | should-fix | CP1 check | Listed only some ACs' mutations | Every row whose test file is created in CP1 |
| 13 | should-fix | Adapter | Google login with a `next` bypasses `form_valid`, so the intent survived; intents never expired | `user_logged_in` receiver (superseded by third review #3: `post_login`); 24 h expiry |
| 14 | nit | Proof AC 5 | The CP1 role screen always shows, so the HTML can't prove the role | Assert `role is None` |
| 15 | nit | Proof | allauth's confirmation email lands in `mail.outbox` | Count by subject |
| 16 | nit | New flow | Wrong allauth reference for the logged-in redirect | `allauth/account/mixins.py:89` |
| 17 | nit | Manual | Shell env doesn't reach the container | Set the email vars in `.env` |
| 18 | nit | 2C, router | "Log in or sign up" shown to logged-in users; kind `none` mismatch undefined | Copy by auth state; `none` mismatch → `account_home` |
| 19 | nit | 1C | Unknown roles only handled in `SessionDetailView`; `RoleTemplateMixin` 500s | `intent.user_role` used in both mixins |

**Third review** (fresh sub-agent, 2026-11-26). Every finding is folded into the sections above.

| # | Severity | Section | Finding | Fix in plan |
| --- | --- | --- | --- | --- |
| 1 | blocker | CP2 tasks, Proof | CP2's router changes (steps 2, 3, 6) and the CP1 tests they turn red had no owner | 2B owns `intent.py`'s CP2 changes and both CP1 test files; new "CP1 tests at CP2" table |
| 2 | should-fix | Proof | The double-submit mutation couldn't fail (the role guard returns first) | Mutation moved to the guard; new stray-row test carries the `get_or_create` mutation |
| 3 | should-fix | 1D | Google's `next` lives in `sociallogin.state`, not the callback request, so the signal missed it | `AccountAdapter.post_login` with `redirect_url`; signal dropped |
| 4 | should-fix | Router | Mismatch vs the switch link was undefined | Mismatch uses the saved role; `set_pending_role` rewrites the intent; switch test |
| 5 | should-fix | 2B | Existing users routed through a step got "Welcome!" again | Email only when the role was `None`; test |
| 6 | should-fix | Test helpers | `SessionFactory` makes inactive sessions; class pages don't filter on `is_active` | `SessionFactory(is_active=True)`; stricter start check stated on purpose |
| 7 | should-fix | 2A/2B | `WelcomeDoneView` had no access rule | `login_required`, guardians only; test |
| 8 | nit | AC 10 | "Only the start endpoints write the session" overstated | Scoped to logged-out visitors on public pages |
| 9 | nit | New flow | Two lists of who sets a role | New flow defers to the Tasks list |
| 10 | nit | Read first | `urls.py` and `accounts/tests.py` line refs | Fixed |
| 11 | nit | CP1 check | AC 7 isn't end-to-end in CP1 | Stated; CP2 round-trip test added |
| 12 | nit | 1E | `meeting_sign_up` ignored `is_active`/`is_public` | Added, with a test (corrected by fourth review #3: `is_active` only) |

**Fourth review** (fresh sub-agent, 2026-11-26). No blockers. Every finding is folded into the sections above.

| # | Severity | Section | Finding | Fix in plan |
| --- | --- | --- | --- | --- |
| 1 | should-fix | CP1 tests at CP2 | Three CP1 cases go red at CP2 and weren't listed; one lived in a file 2B couldn't edit; 1B's mentor fixture contradicted 1A | Rows added; `accounts/test_onboarding_redirects.py` in 2B; complete mentor fixture |
| 2 | should-fix | Proof, 2B | Sequential double POST never reached the guard; guard read cached `request.user` | Hidden `step` field picks the handler; re-read the locked row |
| 3 | should-fix | 1E | `is_public` filter didn't match `MeetingDetailView` for logged-in users | `is_active` unless staff only; private-meeting test |
| 4 | should-fix | Router step 1 | Mismatch undefined in intent fields; a browsed-class volunteer would be flashed | Exact boolean; test |
| 5 | should-fix | 2B | Unknown-role users looped (guard and email read raw `user.role`) | `intent.user_role` in both; test |
| 6 | nit | New flow | "Only start endpoints write the intent" overstated | Scoped to logged-out visitors |
| 7 | nit | 1A vs New flow | Whether CP1 `next_url` uses `current_step` | It does; stated |
| 8 | nit | 2A | Kind `none` had no object and no anonymous rule | No lookup; anonymous → login; test |
| 9 | nit | 2C | "Volunteer to attend" shown to guardians | Guardians see the 1E text, no link |
| 10 | nit | Line refs | `urls.py` class block range disagreed | `167-227` in both places |

## Progress

## Sources

- https://docs.djangoproject.com/en/5.2/topics/auth/default/#django.contrib.auth.login
- https://docs.djangoproject.com/en/5.2/topics/http/shortcuts/#redirect
- https://docs.allauth.org/en/latest/account/advanced.html#custom-redirects
- https://owasp.org/www-community/attacks/Unvalidated_Redirects_and_Forwards_Cheat_Sheet
