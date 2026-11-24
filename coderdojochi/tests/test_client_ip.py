import os
import subprocess
import sys

from allauth.account.adapter import get_adapter
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from django.test import TestCase
from django.test import override_settings

PRINT_HEADER = """
from django.conf import settings
print(repr(settings.ALLAUTH_TRUSTED_CLIENT_IP_HEADER))
"""


class ClientIPTest(TestCase):
    """gunicorn on a Unix socket leaves REMOTE_ADDR empty behind Cloudflare."""

    def _request(self, **extra):
        return RequestFactory().post("/account/login/", REMOTE_ADDR="", **extra)

    @override_settings(ALLAUTH_TRUSTED_CLIENT_IP_HEADER="CF-Connecting-IP")
    def test_uses_cloudflare_header_when_trusted(self):
        request = self._request(HTTP_CF_CONNECTING_IP="203.0.113.7")
        assert get_adapter().get_client_ip(request) == "203.0.113.7"

    @override_settings(ALLAUTH_TRUSTED_CLIENT_IP_HEADER=None)
    def test_denied_without_header_setting_or_remote_addr(self):
        request = self._request(HTTP_CF_CONNECTING_IP="203.0.113.7")
        try:
            ip = get_adapter().get_client_ip(request)
        except PermissionDenied:
            return
        msg = f"expected PermissionDenied, got {ip!r}"
        raise AssertionError(msg)

    def test_settings_reads_header_from_env(self):
        """Settings are read at import, so load production settings in a subprocess."""
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in ("DATABASE_URL", "DJANGO_SETTINGS_MODULE")
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
                "ALLAUTH_TRUSTED_CLIENT_IP_HEADER": "CF-Connecting-IP",
            }
        )
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-c", PRINT_HEADER],
            capture_output=True,
            text=True,
            env=env,
            cwd=settings.BASE_DIR,
            timeout=60,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip().splitlines()[-1] == "'CF-Connecting-IP'"
