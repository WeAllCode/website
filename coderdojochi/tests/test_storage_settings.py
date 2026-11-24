import json
import os
import subprocess
import sys

from django.conf import settings
from django.test import SimpleTestCase

from coderdojochi.storage_backends import MediaStorage
from coderdojochi.storage_backends import StaticStorage

PRINT_SETTINGS = """
import json
from django.conf import settings
print(json.dumps({
    "STORAGES": settings.STORAGES,
    "MEDIA_URL": settings.MEDIA_URL,
    "STATIC_URL": settings.STATIC_URL,
}))
"""


class ProductionStorageSettingsTest(SimpleTestCase):
    """Settings are read at import, so load production settings in a subprocess."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
            }
        )
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
        cls.prod = json.loads(result.stdout.strip().splitlines()[-1])

    def test_default_storage_is_media_storage(self):
        default = self.prod["STORAGES"]["default"]
        assert default["BACKEND"] == "coderdojochi.storage_backends.MediaStorage"
        assert default["OPTIONS"]["bucket_name"] == "wac-test-bucket"
        assert default["OPTIONS"]["default_acl"] is None
        assert not default["OPTIONS"]["querystring_auth"]

    def test_staticfiles_storage_is_static_storage(self):
        assert (
            self.prod["STORAGES"]["staticfiles"]["BACKEND"]
            == "coderdojochi.storage_backends.StaticStorage"
        )

    def test_media_url_points_at_bucket(self):
        assert self.prod["MEDIA_URL"].startswith(
            "https://storage.googleapis.com/wac-test-bucket/"
        )

    def test_static_url_points_at_bucket(self):
        assert (
            self.prod["STATIC_URL"]
            == "https://storage.googleapis.com/wac-test-bucket/static/"
        )


class StorageBackendsTest(SimpleTestCase):
    def test_backends_keep_bucket_prefixes(self):
        media = MediaStorage(bucket_name="wac-test-bucket")
        assert media.location == "media"
        assert not media.file_overwrite
        # Instantiating StaticStorage loads the manifest from the bucket, so
        # check the class attribute instead.
        assert StaticStorage.location == "static"
