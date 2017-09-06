# -*- coding: utf-8 -*-

'''
Django settings for coderdojochi project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
'''

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import sys
import raven
from coderdojochi.util import str_to_bool

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        os.pardir
    )
)
PACKAGE_ROOT = os.path.abspath(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = str_to_bool(
    os.environ.get('DEBUG')
) and 'test' not in sys.argv or False
DEBUG_EMAIL = str_to_bool(os.environ.get('DEBUG_EMAIL')) or False

ALLOWED_HOSTS = ['*']

SITE_URL = os.environ.get('SITE_URL') or 'http://coderdojochi.local'
SITE_NAME = 'CoderDojoChi'
SITE_ID = 1

USE_TZ = True
TIME_ZONE = 'America/Chicago'

# Application definition

INSTALLED_APPS = [

    # django contrib
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # vendor
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
    'storages',
    'import_export',
    'raven.contrib.django.raven_compat',

    # coderdojochi
    'coderdojochi',
    'django_nose',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(PROJECT_ROOT, 'coderdojochi/templates/'),
            os.path.join(PROJECT_ROOT, 'coderdojochi/templates/dashboard/'),
            os.path.join(PROJECT_ROOT, 'coderdojochi/emailtemplates/'),

            os.path.join(PROJECT_ROOT, 'coderdojochi/mentors/templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.csrf',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',

                'coderdojochi.context_processors.main_config_processor',
            ],
        },
    },
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
)

ROOT_URLCONF = 'coderdojochi.urls'

WSGI_APPLICATION = 'coderdojochi.wsgi.application'

AUTH_USER_MODEL = 'coderdojochi.CDCUser'

# LOGIN_URL = '/accounts/login/'
# LOGOUT_URL = '/accounts/logout/'
# LOGIN_REDIRECT_URL = '/dojo/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('POSTGRES_DB'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': os.environ.get('POSTGRES_HOST'),
        'PORT': os.environ.get('POSTGRES_PORT'),
    }
}

CACHES = {
    'default': {
        # 'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

if DEBUG:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Chicago'

USE_I18N = True

USE_L10N = True


# URL prefix for static files.
# Example: 'http://example.com/static/', 'http://static.example.com/'
STATIC_URL = '/static/'
STATIC_ROOT = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(os.path.dirname(__file__), 'static'),
)

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: 'http://example.com/media/', 'http://media.example.com/'
MEDIA_URL = '/media/'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: '/var/www/example.com/media/'
MEDIA_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'media')


SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'


# AWS S3
AWS_HEADERS = {
    'Expires': 'Thu, 31 Dec 2099 20:00:00 GMT',
    'Cache-Control': 'max-age=94608000',
}

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')

if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:

    AWS_S3_CALLING_FORMAT = 'boto.s3.connection.OrdinaryCallingFormat'

    AWS_STATIC_BUCKET_NAME = os.environ.get('AWS_STATIC_BUCKET_NAME')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')

    STATICFILES_STORAGE = 'coderdojochi.custom_storages.S3StaticStorage'
    DEFAULT_FILE_STORAGE = 'coderdojochi.custom_storages.S3MediaStorage'

    AWS_STATIC_CUSTOM_DOMAIN = AWS_STATIC_BUCKET_NAME
    AWS_S3_CUSTOM_DOMAIN = AWS_STORAGE_BUCKET_NAME

    STATIC_URL = u'https://{}/'.format(AWS_STATIC_BUCKET_NAME)
    MEDIA_URL = u'https://{}/'.format(AWS_STORAGE_BUCKET_NAME)


# Paypal
PAYPAL_RECEIVER_EMAIL = 'info@coderdojochi.org'
PAYPAL_BUSINESS_ID = 'CXD22M5GNXDE4'
PAYPAL_TEST = False


# django allauth
LOGIN_REDIRECT_URL = '/dojo'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_SIGNUP_FORM_CLASS = 'coderdojochi.forms.SignupForm'
SOCIALACCOUNT_ADAPTER = (
    'coderdojochi.social_account_adapter.SocialAccountAdapter'
)

# Sentry configuration
SENTRY_DSN = os.getenv('SENTRY_DSN')

if SENTRY_DSN:
    RAVEN_CONFIG = {
        'dsn': SENTRY_DSN,
        # 'release': raven.fetch_git_sha(os.path.dirname(os.pardir)),
    }

# Email
EMAIL_BACKEND = 'djrill.mail.backends.djrill.DjrillBackend'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')
CONTACT_EMAIL = os.environ.get('CONTACT_EMAIL')
MANDRILL_API_KEY = os.environ.get('MANDRILL_API_KEY')
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = os.environ.get('EMAIL_PORT')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = MANDRILL_API_KEY
SERVER_EMAIL = DEFAULT_FROM_EMAIL

if DEBUG and DEBUG_EMAIL:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

if DEBUG:

    def custom_show_toolbar(request):
        return True

    DEBUG_TOOLBAR_PATCH_SETTINGS = False

    MIDDLEWARE_CLASSES += (
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    )

    INSTALLED_APPS += (
        'debug_toolbar',
    )

    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': custom_show_toolbar,
        'TAG': 'div',
        'ENABLE_STACKTRACES': True,
    }
