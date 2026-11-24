"""Google Cloud Storage backends for static and media files.

Objects keep the ``static/`` and ``media/`` prefixes from the old S3 bucket, so
file names stored in the database (relative to ``location``) keep working.
"""

from django.contrib.staticfiles.storage import ManifestFilesMixin
from storages.backends.gcloud import GoogleCloudStorage


class StaticStorage(ManifestFilesMixin, GoogleCloudStorage):
    location = "static"


class MediaStorage(GoogleCloudStorage):
    location = "media"
    file_overwrite = False
