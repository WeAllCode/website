"""Front-end assets are served from our own static files, not third-party CDNs.

Checkpoint 9 vendored jQuery, Foundation, Font Awesome and friends into
``coderdojochi/static/vendor/``. These tests keep CDN URLs from creeping back
into the rendered pages and check that the manifest storage can hash the
vendored files (CSS ``url()`` references included).
"""

import json
import shutil
import tempfile
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

from allauth.socialaccount.models import SocialApp
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from coderdojochi.factories import SessionFactory
from coderdojochi.models import Guardian
from coderdojochi.models import Order
from coderdojochi.models import Student

# Third-party hosts that are allowed to serve scripts/styles: (host, path prefix).
ALLOWED_EXTERNAL = [
    ("www.google.com", "/recaptcha"),
    ("www.gstatic.com", "/recaptcha"),
    ("www.googletagmanager.com", "/"),
    ("embed.donsplus.com", "/"),
]

# <link rel> values that point at a page URL rather than a fetched asset.
NON_ASSET_RELS = {
    "canonical",
    "alternate",
    "preconnect",
    "dns-prefetch",
    "author",
    "license",
}


class _AssetCollector(HTMLParser):
    """Collect every ``<script src>`` and asset-loading ``<link href>``."""

    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script" and attrs.get("src"):
            self.urls.append(attrs["src"])
        elif tag == "link" and attrs.get("href"):
            href = attrs["href"]
            rels = set((attrs.get("rel") or "").lower().split())
            path = urlsplit(href).path.lower()
            if (
                "stylesheet" in rels
                or path.endswith((".css", ".js"))
                or not rels & NON_ASSET_RELS
            ):
                self.urls.append(href)

    handle_startendtag = handle_starttag


def _asset_urls(html):
    parser = _AssetCollector()
    parser.feed(html)
    parser.close()
    return parser.urls


def _is_allowed(url):
    if url.startswith(settings.STATIC_URL):
        return True
    parts = urlsplit(url)
    if not parts.scheme and not parts.netloc:
        return True
    return any(
        parts.netloc == host and parts.path.startswith(prefix)
        for host, prefix in ALLOWED_EXTERNAL
    )


@override_settings(SECURE_SSL_REDIRECT=False)
class NoCdnAssetsTest(TestCase):
    def assert_no_cdn(self, html, label):
        urls = _asset_urls(html)
        assert urls, f"{label}: no <script src>/<link href> found; parser or page broke"
        offending = [u for u in urls if not _is_allowed(u)]
        assert not offending, f"{label} loads assets from disallowed hosts: {offending}"

    def assert_page_no_cdn(self, path):
        response = self.client.get(path)
        assert response.status_code == 200, f"{path} returned {response.status_code}"
        self.assert_no_cdn(response.content.decode(), path)

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
                self.assert_page_no_cdn(path)

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
        self.assert_page_no_cdn(reverse("cdc-admin"))

    def test_welcome_without_role(self):
        user = get_user_model().objects.create_user(
            username="newbie",
            email="newbie@example.com",
        )
        assert not user.role
        self.client.force_login(user)
        self.assert_page_no_cdn(reverse("welcome"))

    @override_settings(SENTRY_DSN="https://public@sentry.example.com/1")
    def test_500_page_with_sentry(self):
        request = RequestFactory().get("/")
        html = render_to_string(
            "500.html",
            {"SENTRY_DSN": settings.SENTRY_DSN, "sentry_event_id": "abc123"},
            request=request,
        )
        assert "abc123" in html, "Sentry block did not render"
        self.assert_no_cdn(html, "500.html")


@override_settings(SECURE_SSL_REDIRECT=False)
class GoogleAnalyticsTest(TestCase):
    @override_settings(GA_MEASUREMENT_ID="G-TEST123")
    def test_gtag_rendered_when_id_set(self):
        response = self.client.get(reverse("weallcode-home"))
        self.assertContains(response, "gtag/js?id=G-TEST123")

    @override_settings(GA_MEASUREMENT_ID="")
    def test_no_gtag_when_id_empty(self):
        response = self.client.get(reverse("weallcode-home"))
        self.assertNotContains(response, "googletagmanager")


class ManifestStaticFilesTest(TestCase):
    def test_collectstatic_with_manifest_storage(self):
        static_root = tempfile.mkdtemp(prefix="wac-static-")
        self.addCleanup(shutil.rmtree, static_root, ignore_errors=True)
        storages = {
            **settings.STORAGES,
            "staticfiles": {
                "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
            },
        }

        with override_settings(STORAGES=storages, STATIC_ROOT=static_root):
            call_command("collectstatic", "--noinput", verbosity=0)

        manifest = json.loads((Path(static_root) / "staticfiles.json").read_text())
        assert "vendor/fontawesome5/css/all.min.css" in manifest["paths"]
