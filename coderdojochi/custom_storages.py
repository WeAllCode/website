# -*- coding: utf-8 -*-

from django.conf import settings
from storages.backends.s3boto import S3BotoStorage


class S3StaticStorage(S3BotoStorage):
    "S3 storage backend that sets the static bucket."
    def __init__(self, *args, **kwargs):
        super(S3StaticStorage, self).__init__(
            bucket=settings.AWS_STATIC_BUCKET_NAME,
            custom_domain=settings.AWS_STATIC_CUSTOM_DOMAIN,
            secure_urls=False,
            *args,
            **kwargs
        )


class S3MediaStorage(S3BotoStorage):
    "S3 storage backend that sets the media bucket."
    def __init__(self, *args, **kwargs):
        super(S3MediaStorage, self).__init__(
            bucket=settings.AWS_STORAGE_BUCKET_NAME,
            custom_domain=settings.AWS_S3_CUSTOM_DOMAIN,
            secure_urls=False,
            *args,
            **kwargs
        )
