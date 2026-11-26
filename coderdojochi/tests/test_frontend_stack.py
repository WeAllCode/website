"""Guard tests for the front-end rewrite (docs/plans/frontend-rewrite.md, task 1E).

- ``LegacyRatchetTest``: templates (and the two Python modules that build HTML)
  may only use Foundation, Bootstrap 3, Font Awesome or Glyphicons classes if
  they are listed in ``LEGACY_TEMPLATES`` / ``LEGACY_PYTHON``. Each checkpoint
  removes the files it migrates, so the lists only shrink.
- ``RemovedLibrariesTest``: no rendered page loads a library that has been
  removed, and django-bootstrap3 is gone.
- ``DeadFilesTest``: dead front-end code deleted in Checkpoint 1 stays deleted.

Refresh the ratchet sets after a checkpoint (prints both sets as Python)::

    EMAIL_BACKEND=anymail.backends.test.EmailBackend RESEND_API_KEY= \\
    DJANGO_SETTINGS_MODULE=coderdojochi.test_settings uv run python manage.py \\
    shell -c "from coderdojochi.tests.test_frontend_stack import print_legacy_sets; print_legacy_sets()"

The legacy class names live in ``legacy_class_tokens.txt`` next to this file
(about 1,100 names: too long for a readable constant, and the CSS it comes from
is deleted in CP4/CP5). Regenerate it, while the legacy CSS still exists, with
``write_token_file()`` the same way.
"""

import ast
import hashlib
import importlib.util
import re
import subprocess
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

from allauth.socialaccount.models import SocialApp
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.test import SimpleTestCase
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from coderdojochi.factories import SessionFactory
from coderdojochi.models import Guardian
from coderdojochi.models import Mentor
from coderdojochi.models import Order
from coderdojochi.models import Student
from coderdojochi.tests.test_vendored_assets import _asset_urls

REPO = Path(__file__).resolve().parents[2]
TOKEN_FILE = Path(__file__).with_name("legacy_class_tokens.txt")

# ---------------------------------------------------------------------------
# Legacy-class ratchet
# ---------------------------------------------------------------------------

TEMPLATE_DIRS = [
    "weallcode/templates",
    "coderdojochi/templates",
    "accounts/templates",
]
# HTML emails use inline styles and are out of scope.
TEMPLATE_EXCLUDES = ["accounts/templates/account/email/"]
PYTHON_GLOBS = ["coderdojochi/forms.py", "coderdojochi/templatetags/*.py"]

# Templates that still use a legacy class or attribute. Only ever remove lines.
LEGACY_TEMPLATES = frozenset(
    {
        "accounts/templates/account/_base.html",
        "accounts/templates/account/_field.html",
        "accounts/templates/account/_form.html",
        "accounts/templates/account/email.html",
        "accounts/templates/account/email_confirm.html",
        "accounts/templates/account/guardian/home.html",
        "accounts/templates/account/login.html",
        "accounts/templates/account/logout.html",
        "accounts/templates/account/mentor/home.html",
        "accounts/templates/account/password_change.html",
        "accounts/templates/account/password_reset.html",
        "accounts/templates/account/password_reset_from_key.html",
        "accounts/templates/account/password_set.html",
        "accounts/templates/account/signup.html",
        "accounts/templates/socialaccount/connections.html",
        "accounts/templates/socialaccount/signup.html",
        "accounts/templates/socialaccount/snippets/provider_list.html",
        "coderdojochi/templates/_messages_bootstrap.html",
        "coderdojochi/templates/coderdojochi/mentor_detail.html",
        "coderdojochi/templates/coderdojochi/mentor_list.html",
        "coderdojochi/templates/dashboard/admin.html",
        "coderdojochi/templates/dashboard/meeting_check_in.html",
        "coderdojochi/templates/dashboard/session_check_in.html",
        "coderdojochi/templates/dashboard/session_check_in_mentors.html",
        "coderdojochi/templates/dashboard/session_donations.html",
        "coderdojochi/templates/dashboard/session_stats.html",
        "coderdojochi/templates/guardian/session_detail.html",
        "coderdojochi/templates/guardian/session_sign_up.html",
        "coderdojochi/templates/meeting_detail.html",
        "coderdojochi/templates/meeting_sign_up.html",
        "coderdojochi/templates/meetings.html",
        "coderdojochi/templates/mentor/session_detail.html",
        "coderdojochi/templates/mentor/session_sign_up.html",
        "coderdojochi/templates/public/session_detail.html",
        "coderdojochi/templates/session_partner_password.html",
        "coderdojochi/templates/student_detail.html",
        "coderdojochi/templates/unsubscribe.html",
        "coderdojochi/templates/welcome.html",
    },
)

# Python modules whose string literals still hold a legacy class or attribute.
LEGACY_PYTHON = frozenset(
    {
        "coderdojochi/forms.py",
        "coderdojochi/templatetags/coderdojochi_extras.py",
    },
)

LEGACY_CSS = {
    "foundation": "weallcode/static/weallcode/css/foundation.min.css",
    "bootstrap": "coderdojochi/static/vendor/bootstrap3/css/bootstrap.min.css",
    "app": "weallcode/static/weallcode/css/app.css",
}

# Font Awesome 4/5 and Glyphicons, matched by name rather than listed.
ICON_CLASS = re.compile(r"fa|fa[srbld]|fa-.+|glyphicons?(-.+)?")
LEGACY_DATA_ATTR = re.compile(
    r"(?<![\w-])data-(toggle|toggler|target|dismiss|ride)(?![\w-])",
    re.IGNORECASE,
)
_TEMPLATE_COMMENT = re.compile(
    r"{%\s*comment\b.*?%}.*?{%\s*endcomment\s*%}|{#.*?#}|<!--.*?-->",
    re.DOTALL,
)
_TEMPLATE_TAG = re.compile(r"{%.*?%}|{{.*?}}", re.DOTALL)
_CLASS_ATTR = re.compile(
    r"""(?<![\w-])class\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+))""",
    re.IGNORECASE,
)


def _load_tokens():
    # A missing file gives an empty set, which test_tokens_loaded reports.
    lines = TOKEN_FILE.read_text().splitlines() if TOKEN_FILE.exists() else []
    return frozenset(
        line.strip() for line in lines if line.strip() and not line.startswith("#")
    )


LEGACY_CLASSES = _load_tokens()


def legacy_hits(text):
    """Legacy class names and ``data-*`` attributes in a template's markup.

    Comments are dropped. Template tags and variables become spaces, so the
    literal class names around them still count (``{% if x %}active{% endif %}``
    counts ``active``). Class values are split on whitespace, so ``main-menu``
    is not ``menu``.
    """
    text = _TEMPLATE_COMMENT.sub(" ", text)
    text = _TEMPLATE_TAG.sub(" ", text)
    hits = set()
    for match in _CLASS_ATTR.finditer(text):
        value = next(group for group in match.groups() if group is not None)
        for name in value.split():
            if name in LEGACY_CLASSES or ICON_CLASS.fullmatch(name):
                hits.add(name)
    hits.update(m.group(0).lower() for m in LEGACY_DATA_ATTR.finditer(text))
    return hits


def _python_markup(source):
    """Every string literal that can end up in HTML, as markup to scan.

    f-strings are joined with a space for each placeholder. Values assigned to
    a ``"class"`` key (widget ``attrs``) are wrapped as ``class="…"``.
    """
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.JoinedStr):
            yield "".join(
                part.value if isinstance(part, ast.Constant) else " "
                for part in node.values
            )
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node.value
        if isinstance(node, ast.Dict):
            pairs = zip(node.keys, node.values, strict=True)
        elif isinstance(node, ast.Assign | ast.AugAssign):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            pairs = [
                (target.slice, node.value)
                for target in targets
                if isinstance(target, ast.Subscript)
            ]
        else:
            continue
        for key, value in pairs:
            if (
                isinstance(key, ast.Constant)
                and key.value == "class"
                and isinstance(value, ast.Constant)
                and isinstance(value.value, str)
            ):
                yield f'class="{value.value}"'


def python_legacy_hits(source):
    hits = set()
    for markup in _python_markup(source):
        hits |= legacy_hits(markup)
    return hits


def template_paths():
    for directory in TEMPLATE_DIRS:
        for path in sorted((REPO / directory).rglob("*.html")):
            rel = path.relative_to(REPO).as_posix()
            if not any(rel.startswith(prefix) for prefix in TEMPLATE_EXCLUDES):
                yield rel


def python_paths():
    for pattern in PYTHON_GLOBS:
        for path in sorted(REPO.glob(pattern)):
            yield path.relative_to(REPO).as_posix()


def scan_templates():
    """``{path: hits}`` for every template with a legacy class or attribute."""
    hits = {rel: legacy_hits((REPO / rel).read_text()) for rel in template_paths()}
    return {rel: found for rel, found in hits.items() if found}


def scan_python():
    hits = {rel: python_legacy_hits((REPO / rel).read_text()) for rel in python_paths()}
    return {rel: found for rel, found in hits.items() if found}


def print_legacy_sets():
    """Print ``LEGACY_TEMPLATES`` and ``LEGACY_PYTHON`` for the current tree."""
    out = []
    for name, found in [
        ("LEGACY_TEMPLATES", scan_templates()),
        ("LEGACY_PYTHON", scan_python()),
    ]:
        out.append(f"{name} = frozenset(\n    {{")
        out.extend(f'        "{rel}",' for rel in sorted(found))
        out.append(f"    }},\n)\n# {len(found)} files\n")
    sys.stdout.write("\n".join(out))


def css_class_selectors(css):
    """Class names used in the selectors of a stylesheet."""
    css = re.sub(r"/\*.*?\*/", " ", css, flags=re.DOTALL)
    css = re.sub(r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'", '""', css)
    names = set()
    for prelude in re.findall(r"([^{};]+)\{", css):
        if prelude.lstrip().startswith("@"):
            continue
        selector = re.sub(r"\[[^\]]*\]", " ", prelude)
        names.update(re.findall(r"\.(-?[_a-zA-Z][_a-zA-Z0-9-]*)", selector))
    return names


def write_token_file():
    """Rebuild ``legacy_class_tokens.txt`` from the legacy CSS (CP1 to CP3 only).

    Tokens = class selectors in Foundation | Bootstrap, minus the ``app.css``
    names that are only in Bootstrap (brand names we keep: plan review row 1
    exempts app.css names that aren't in Foundation), plus app.css's
    Foundation-style spacing names (``margin-*-half``, ``medium-padding-*``…,
    which 2C drops), minus the Font Awesome / Glyphicon names ``ICON_CLASS``
    already matches.

    app.css was deleted in CP2 (split into brand.css / brand-legacy.css), so
    this reads it from git at the last commit that had it (25ce01b7, CP1).
    """
    sources = {
        key: (REPO / rel).read_text()
        for key, rel in LEGACY_CSS.items()
        if (REPO / rel).exists()
    }
    if "app" not in sources:
        sources["app"] = subprocess.run(  # noqa: S603 (fixed argv, dev helper)
            ["git", "-C", str(REPO), "show", f"25ce01b7:{LEGACY_CSS['app']}"],  # noqa: S607
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    found = {key: css_class_selectors(css) for key, css in sources.items()}
    foundation, bootstrap, app = found["foundation"], found["bootstrap"], found["app"]
    spacing = re.compile(r"((small|medium|large)-)?(margin|padding)-.+")
    tokens = (
        foundation
        | (bootstrap - (app - foundation))
        | {name for name in app if spacing.fullmatch(name)}
    )
    tokens = sorted(name for name in tokens if not ICON_CLASS.fullmatch(name))
    header = [
        "# Legacy class names for coderdojochi/tests/test_frontend_stack.py.",
        "# Generated by write_token_file() in that module. Don't edit by hand.",
        "# Sources (sha256):",
        *(
            f"#   {LEGACY_CSS[key]} {hashlib.sha256(css.encode()).hexdigest()}"
            for key, css in sources.items()
        ),
        "# = class selectors in foundation.min.css | bootstrap.min.css",
        "#   - app.css names found in Bootstrap but not Foundation (kept brand names)",
        "#   + app.css Foundation-style spacing names (dropped in 2C)",
        "#   - fa, fa-*, fa[srbld], glyphicon* (matched by pattern in the test).",
        f"# {len(tokens)} names.",
    ]
    TOKEN_FILE.write_text("\n".join([*header, *tokens]) + "\n")


class LegacyRatchetTest(SimpleTestCase):
    def test_tokens_loaded(self):
        assert len(LEGACY_CLASSES) > 1000, "legacy_class_tokens.txt is missing names"
        assert {"cell", "grid-x", "callout", "form-control", "navbar"} <= LEGACY_CLASSES
        assert "main-menu" not in LEGACY_CLASSES

    def test_no_new_legacy_templates(self):
        found = scan_templates()
        new = {rel: sorted(hits) for rel, hits in found.items()}
        new = {rel: hits for rel, hits in new.items() if rel not in LEGACY_TEMPLATES}
        assert not new, (
            f"Templates use legacy classes but aren't in LEGACY_TEMPLATES: {new}"
        )

    def test_legacy_templates_still_legacy(self):
        found = scan_templates()
        for rel in sorted(LEGACY_TEMPLATES):
            with self.subTest(template=rel):
                assert (REPO / rel).exists(), (
                    f"{rel} is gone: remove it from LEGACY_TEMPLATES"
                )
                assert rel in found, (
                    f"{rel} has no legacy classes left: remove it from LEGACY_TEMPLATES"
                )

    def test_no_new_legacy_python(self):
        found = scan_python()
        new = {rel: sorted(hits) for rel, hits in found.items()}
        new = {rel: hits for rel, hits in new.items() if rel not in LEGACY_PYTHON}
        assert not new, f"Python HTML uses legacy classes, not in LEGACY_PYTHON: {new}"

    def test_legacy_python_still_legacy(self):
        found = scan_python()
        for rel in sorted(LEGACY_PYTHON):
            with self.subTest(module=rel):
                assert (REPO / rel).exists(), (
                    f"{rel} is gone: remove it from LEGACY_PYTHON"
                )
                assert rel in found, (
                    f"{rel} has no legacy classes left: remove it from LEGACY_PYTHON"
                )

    def test_scanner(self):
        assert legacy_hits('<div class="cell main-menu">') == {"cell"}
        assert legacy_hits("<i class='fa fa-bars'></i>") == {"fa", "fa-bars"}
        assert legacy_hits('<a class="{% if a %}button{% endif %} x">') == {"button"}
        assert legacy_hits('<a class="{{ cls }}" data-toggler=".x">') == {
            "data-toggler",
        }
        assert legacy_hits('{# <div class="cell"> #}<p class="title">') == set()
        assert legacy_hits('<p data-class="cell" class="subtitle">') == set()
        assert python_legacy_hits(
            'w = {"class": "form-control"}\nx = f"<a class=\'button {y}\'>"',
        ) == {"form-control", "button"}


# ---------------------------------------------------------------------------
# Removed libraries
# ---------------------------------------------------------------------------

# Substrings of asset URLs for libraries removed so far. Later checkpoints append.
# Public = pages on the weallcode base; dashboard = /admin/ and the check-in pages.
REMOVED_PUBLIC = ["js-datepicker", "jquery", "what-input", "foundation.min.js"]
REMOVED_DASHBOARD = ["js-datepicker"]


class _InputCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inputs = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "input" and attrs.get("id"):
            self.inputs[attrs["id"]] = attrs

    handle_startendtag = handle_starttag


@override_settings(SECURE_SSL_REDIRECT=False)
class RemovedLibrariesTest(TestCase):
    def assert_not_removed(self, html, label, removed):
        urls = _asset_urls(html)
        assert urls, f"{label}: no <script src>/<link href> found; parser or page broke"
        offending = [url for url in urls if any(lib in url.lower() for lib in removed)]
        assert not offending, f"{label} loads removed libraries: {offending}"

    def get_html(self, path):
        response = self.client.get(path)
        assert response.status_code == 200, f"{path} returned {response.status_code}"
        return response.content.decode()

    def test_public_pages(self):
        # The login template renders the Google button, which needs a SocialApp.
        app = SocialApp.objects.create(
            provider="google",
            name="google",
            client_id="google-id",
            secret="google-secret",  # noqa: S106
        )
        app.sites.add(Site.objects.get_current())

        for path in [
            reverse("weallcode-home"),
            reverse("weallcode-programs"),
            reverse("account_login"),
        ]:
            with self.subTest(path=path):
                self.assert_not_removed(self.get_html(path), path, REMOVED_PUBLIC)

    def test_admin_dashboard(self):
        # cdc_admin averages checked-in students' ages, so it needs one.
        session = SessionFactory()
        guardian = Guardian.objects.create(
            user=get_user_model().objects.create_user(username="guardian"),
        )
        student = Student.objects.create(
            guardian=guardian,
            first_name="Kid",
            last_name="Tester",
            birthday=date(2015, 1, 1),
            gender="other",
        )
        Order.objects.create(
            guardian=guardian,
            session=session,
            student=student,
            check_in=timezone.now(),
        )
        staff = get_user_model().objects.create_user(
            username="staff",
            email="staff@example.com",
            is_staff=True,
        )
        self.client.force_login(staff)
        path = reverse("cdc-admin")
        self.assert_not_removed(self.get_html(path), path, REMOVED_DASHBOARD)

    def test_welcome_without_role(self):
        user = get_user_model().objects.create_user(
            username="newbie",
            email="newbie@example.com",
        )
        assert not user.role
        self.client.force_login(user)
        path = reverse("welcome")
        self.assert_not_removed(self.get_html(path), path, REMOVED_PUBLIC)

    def test_welcome_birthday_is_native_date_input(self):
        # A mentor without a name gets the MentorForm, which has the birthday.
        user = get_user_model().objects.create_user(
            username="new-mentor",
            email="new-mentor@example.com",
            role="mentor",
        )
        Mentor.objects.create(user=user)
        self.client.force_login(user)
        path = reverse("welcome")
        html = self.get_html(path)
        self.assert_not_removed(html, path, REMOVED_PUBLIC)

        parser = _InputCollector()
        parser.feed(html)
        parser.close()
        birthday = parser.inputs.get("id_birthday")
        assert birthday, f"{path}: no #id_birthday input"
        assert birthday.get("type") == "date", birthday

    @override_settings(SENTRY_DSN="https://public@sentry.example.com/1")
    def test_500_page(self):
        request = RequestFactory().get("/")
        html = render_to_string(
            "500.html",
            {"SENTRY_DSN": settings.SENTRY_DSN, "sentry_event_id": "abc123"},
            request=request,
        )
        self.assert_not_removed(html, "500.html", REMOVED_PUBLIC)

    def test_bootstrap3_not_installed(self):
        assert "bootstrap3" not in settings.INSTALLED_APPS
        assert importlib.util.find_spec("bootstrap3") is None, (
            "django-bootstrap3 is still installed"
        )


# ---------------------------------------------------------------------------
# Dead files
# ---------------------------------------------------------------------------

# Deleted in 1B (coderdojochi/static/js/cdc.js was deleted on main in 72aa0f44).
DEAD_FILES = [
    "coderdojochi/static/css/cdc.css",
    "coderdojochi/static/js/cdc.js",
    "coderdojochi/templates/home.html",
    "coderdojochi/templates/volunteer.html",
    "coderdojochi/templates/sessions.html",
    "coderdojochi/templates/contact.html",
    "coderdojochi/templates/_messages.html",
    "coderdojochi/templates/_topnav.html",
    "weallcode/templates/weallcode/contact.html",
    "weallcode/templates/weallcode/snippets/card.html",
]

# Deleted in 1B: (module, name).
DEAD_NAMES = [
    ("coderdojochi.old_views", "home"),
    ("coderdojochi.old_views", "volunteer"),
    ("coderdojochi.templatetags.coderdojochi_extras", "menu_is_active"),
]


class DeadFilesTest(SimpleTestCase):
    def test_dead_files_deleted(self):
        for rel in DEAD_FILES:
            with self.subTest(path=rel):
                assert not (REPO / rel).exists(), f"{rel} is dead code; delete it"

    def test_dead_functions_deleted(self):
        for module_name, name in DEAD_NAMES:
            with self.subTest(name=f"{module_name}.{name}"):
                module = importlib.import_module(module_name)
                assert not hasattr(module, name), f"{module_name}.{name} is dead code"
