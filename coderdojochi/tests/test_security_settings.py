import json
import os
import subprocess
import sys
from http import HTTPStatus

from django.conf import settings
from django.test import SimpleTestCase
from django.test import TestCase
from django.test import override_settings

PRINT_SETTINGS = """
import json
from django.conf import settings
print(json.dumps({
    name: getattr(settings, name)
    for name in (
        "SECURE_SSL_REDIRECT",
        "SECURE_PROXY_SSL_HEADER",
        "SESSION_COOKIE_SECURE",
        "SESSION_COOKIE_HTTPONLY",
        "CSRF_COOKIE_SECURE",
        "CSRF_COOKIE_HTTPONLY",
        "SECURE_HSTS_SECONDS",
        "SECURE_HSTS_INCLUDE_SUBDOMAINS",
        "SECURE_HSTS_PRELOAD",
    )
}))
"""

ONE_DAY = 86400
ONE_YEAR = 31536000


def load_settings(**overrides):
    """Settings are read at import, so load them in a subprocess."""
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in ("DATABASE_URL", "DJANGO_SETTINGS_MODULE")
        and not k.startswith("DJANGO_SECURE_")
    }
    env.update(
        {
            "DJANGO_SETTINGS_MODULE": "coderdojochi.settings",
            "DEBUG": "False",
            "GS_BUCKET_NAME": "wac-test-bucket",
            "SECRET_KEY": "test-secret-key",
            "SITE_URL": "http://testserver",
            "DJANGO_SECURE_SSL_REDIRECT": "False",
            "DEFAULT_FROM_EMAIL": "hello+test@weallcode.org",
            "CONTACT_EMAIL": "hello+test@weallcode.org",
        }
    )
    env.update(overrides)
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", PRINT_SETTINGS],
        capture_output=True,
        text=True,
        env=env,
        cwd=settings.BASE_DIR,
        timeout=60,
        check=False,
    )
    if result.returncode != 0:
        msg = f"settings import failed:\n{result.stderr}"
        raise AssertionError(msg)
    return json.loads(result.stdout.strip().splitlines()[-1])


class ProductionSecuritySettingsTest(SimpleTestCase):
    """Prod runs with DEBUG=False and DJANGO_SECURE_SSL_REDIRECT=False."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.prod = load_settings()

    def test_ssl_redirect_stays_off(self):
        assert self.prod["SECURE_SSL_REDIRECT"] is False

    def test_proxy_header_trusted(self):
        assert self.prod["SECURE_PROXY_SSL_HEADER"] == [
            "HTTP_X_FORWARDED_PROTO",
            "https",
        ]

    def test_cookies_secure_without_redirect(self):
        assert self.prod["SESSION_COOKIE_SECURE"] is True
        assert self.prod["CSRF_COOKIE_SECURE"] is True

    def test_csrf_cookie_readable_by_js(self):
        # cdc.js reads csrftoken from document.cookie.
        assert self.prod["CSRF_COOKIE_HTTPONLY"] is False
        assert self.prod["SESSION_COOKIE_HTTPONLY"] is True

    def test_hsts_one_day_no_subdomains_no_preload(self):
        assert self.prod["SECURE_HSTS_SECONDS"] == ONE_DAY
        assert self.prod["SECURE_HSTS_INCLUDE_SUBDOMAINS"] is False
        assert self.prod["SECURE_HSTS_PRELOAD"] is False

    def test_hsts_overridable_from_env(self):
        prod = load_settings(DJANGO_SECURE_HSTS_SECONDS=str(ONE_YEAR))
        assert prod["SECURE_HSTS_SECONDS"] == ONE_YEAR


class DebugSecuritySettingsTest(SimpleTestCase):
    def test_debug_cookies_not_secure(self):
        dev = load_settings(DEBUG="True")
        assert dev["SESSION_COOKIE_SECURE"] is False
        assert dev["CSRF_COOKIE_SECURE"] is False
        assert dev["SECURE_HSTS_SECONDS"] == 0


@override_settings(SECURE_SSL_REDIRECT=False)
class SecurityHeadersTest(TestCase):
    def test_login_sets_secure_csrf_cookie_and_hsts(self):
        response = self.client.get("/dj-admin/login/", secure=True)
        assert response.status_code == HTTPStatus.OK
        assert response["Strict-Transport-Security"] == f"max-age={ONE_DAY}"
        cookie = response.cookies["csrftoken"]
        assert cookie["secure"] is True
        assert not cookie["httponly"]


@override_settings(SECURE_SSL_REDIRECT=False)
class SentryTestRouteRemovedTest(TestCase):
    def test_test_sentry_route_is_gone(self):
        response = self.client.get("/test--sentry/", secure=True)
        assert response.status_code == HTTPStatus.NOT_FOUND
