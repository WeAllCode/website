"""Settings for running the test suite without Postgres, GCS or the debug toolbar.

Usage: DJANGO_SETTINGS_MODULE=coderdojochi.test_settings uv run python manage.py test
"""

import os

# Settings never call read_env, so set every required variable before import.
os.environ.setdefault("DEBUG", "False")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("GS_BUCKET_NAME", "wac-test-bucket")
os.environ.setdefault("DEFAULT_FROM_EMAIL", "hello+test@weallcode.org")
os.environ.setdefault("CONTACT_EMAIL", "hello+test@weallcode.org")
os.environ.setdefault("SITE_URL", "http://testserver")

from coderdojochi.settings import *  # noqa: F403
from coderdojochi.settings import INSTALLED_APPS
from coderdojochi.settings import MIDDLEWARE

INSTALLED_APPS = [a for a in INSTALLED_APPS if a != "debug_toolbar"]
MIDDLEWARE = [m for m in MIDDLEWARE if "debug_toolbar" not in m]
DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda r: False}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}

# Templates call {% static %}; the manifest storage needs collectstatic first.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

EMAIL_BACKEND = "anymail.backends.test.EmailBackend"
# No real ESP credentials in tests, even if the shell has RESEND_API_KEY set: a test
# that swaps in the Resend backend fails instead of emailing anyone.
ANYMAIL = {"RESEND_API_KEY": ""}
