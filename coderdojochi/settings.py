"""
Django settings for coderodojochi project.

Generated by 'django-admin startproject' using Django 2.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os
import dj_database_url
import django_heroku
import environ

env = environ.Env(
    DEBUG=(bool, False),
    ENABLE_DEV_FIXTURES=(bool, False),
    SECURE_SSL_REDIRECT=(bool, False),
    PAYPAL_TEST=(bool, False),
)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')  # False if not in os.environ

# If True, the SecurityMiddleware redirects all non-HTTPS requests to HTTPS
# (except for those URLs matching a regular expression listed in SECURE_REDIRECT_EXEMPT).
SECURE_SSL_REDIRECT = env('SECURE_SSL_REDIRECT')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',

    # vendor

    # allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.google',

    'bootstrap3',
    'django_cleanup',
    'djrill',
    'html5',
    'loginas',
    'paypal.standard.ipn',
    'stdimage',
    'import_export',

    # coderdojochi
    'coderdojochi',
    'django_nose',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'coderdojochi.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'coderdojochi/templates/'),
            os.path.join(BASE_DIR, 'coderdojochi/templates/dashboard/'),
            os.path.join(BASE_DIR, 'coderdojochi/emailtemplates/'),
            os.path.join(BASE_DIR, 'coderdojochi/mentors/templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'debug': DEBUG,
        },
    },
]

WSGI_APPLICATION = 'coderdojochi.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': env('POSTGRES_DB'),
        'USER': env('POSTGRES_USER'),
        'PASSWORD': env('POSTGRES_PASSWORD'),
        'HOST': env('POSTGRES_HOST'),
        'PORT': env('POSTGRES_PORT'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Chicago'
USE_I18N = True
USE_L10N = True
USE_TZ = True

SITE_ID = 1
SITE_NAME = env('SITE_NAME')
SITE_URL = env('SITE_URL')

# Change 'default' database configuration with $DATABASE_URL.
DATABASES['default'].update(dj_database_url.config(conn_max_age=500, ssl_require=True))

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Allow all host headers
ALLOWED_HOSTS = ['*']

if not DEBUG:
    # STORAGES
    # ------------------------------------------------------------------------------
    # https://django-storages.readthedocs.io/en/latest/#installation
    INSTALLED_APPS += ['storages']  # noqa F405
    # https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
    AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
    # https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
    AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
    # https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
    AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
    # https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
    AWS_AUTO_CREATE_BUCKET = True
    # https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
    AWS_QUERYSTRING_AUTH = False
    # DO NOT change these unless you know what you're doing.
    _AWS_EXPIRY = 60 * 60 * 24 * 7
    # https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': f'max-age={_AWS_EXPIRY}, s-maxage={_AWS_EXPIRY}, must-revalidate',
    }

    # STATIC
    # ------------------------
    STATICFILES_STORAGE = 'coderdojochi.settings.StaticRootS3BotoStorage'
    STATIC_URL = f'https://s3.amazonaws.com/{AWS_STORAGE_BUCKET_NAME}/static/'

    # MEDIA
    # ------------------------------------------------------------------------------
    # region http://stackoverflow.com/questions/10390244/
    from storages.backends.s3boto3 import S3Boto3Storage  # noqa E402

    class StaticRootS3BotoStorage(S3Boto3Storage):
        def __init__(self):
            super().__init__(location='static')

    class MediaRootS3BotoStorage(S3Boto3Storage):
        def __init__(self):
            super().__init__(location='media', file_overwrite=False)

    # endregion
    DEFAULT_FILE_STORAGE = 'coderdojochi.settings.MediaRootS3BotoStorage'
    MEDIA_URL = f'https://s3.amazonaws.com/{AWS_STORAGE_BUCKET_NAME}/media/'

else:
    # Static files (CSS, JavaScript, Images)
    # https://docs.djangoproject.com/en/2.0/howto/static-files/
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATIC_URL = '/static/'

    # Extra places for collectstatic to find static files.
    STATICFILES_DIRS = [
        os.path.join(PROJECT_ROOT, 'static'),
    ]

    # Media files
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    MEDIA_URL = '/media/'


AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
)

AUTH_USER_MODEL = 'coderdojochi.CDCUser'


# Paypal
PAYPAL_RECEIVER_EMAIL = env('PAYPAL_RECEIVER_EMAIL')
PAYPAL_BUSINESS_ID = env('PAYPAL_BUSINESS_ID')
PAYPAL_TEST = env('PAYPAL_TEST')


# django allauth
LOGIN_REDIRECT_URL = '/dojo'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_SIGNUP_FORM_CLASS = 'coderdojochi.forms.SignupForm'
SOCIALACCOUNT_ADAPTER = (
    'coderdojochi.social_account_adapter.SocialAccountAdapter'
)


# Email
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'djrill.mail.backends.djrill.DjrillBackend'
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')
CONTACT_EMAIL = env('CONTACT_EMAIL')
MANDRILL_API_KEY = env('MANDRILL_API_KEY')
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = MANDRILL_API_KEY
SERVER_EMAIL = DEFAULT_FROM_EMAIL

if DEBUG:

    def custom_show_toolbar(request):
        return True

    DEBUG_TOOLBAR_PATCH_SETTINGS = False

    INSTALLED_APPS += (
        'debug_toolbar',
    )

    MIDDLEWARE += (
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    )

    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': custom_show_toolbar,
        'TAG': 'div',
        'ENABLE_STACKTRACES': True,
    }


# Activate Django-Heroku.
django_heroku.settings(locals(), staticfiles=False)
