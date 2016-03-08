'''
Django settings for coderdojochi project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
'''

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
PACKAGE_ROOT = os.path.abspath(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'e^u3u$pukt$s=6#&9oi9&jj5ow6563fuka%y9t7i*2laalk^l$'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# TEMPLATE_DEBUG = DEBUG

IS_PRODUCTION = not DEBUG

ALLOWED_HOSTS = ['*']

SITE_URL = 'http://localhost:8000'
SITE_ID = 1

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

    #vendor
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.google',
    'avatar',
    'bootstrap3',
    'html5',
    'djrill',
    'loginas',
    'paypal.standard.ipn',

    #coderdojochi
    'coderdojochi',
]

MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'dealer.contrib.django.Middleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(PROJECT_ROOT, 'coderdojochi/templates/'),
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

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('POSTGRES_DB'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': os.environ.get("POSTGRES_HOST"),
        'PORT': os.environ.get("POSTGRES_PORT"),
    }
}

CONTACT_EMAIL = 'info@coderdojochi.org'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Chicago'

USE_I18N = True

USE_L10N = True


# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: 'http://example.com/media/', 'http://media.example.com/'
MEDIA_URL = '/media/'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: '/var/www/example.com/media/'
MEDIA_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'media')


# URL prefix for static files.
# Example: 'http://example.com/static/', 'http://static.example.com/'
STATIC_URL = '/static/'
STATIC_ROOT = '/build/static'

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(os.path.dirname(__file__), 'static'),
)


SESSION_SERIALIZER='django.contrib.sessions.serializers.PickleSerializer'

# Gravatar

AVATAR_GRAVATAR_BACKUP = False
AVATAR_DEFAULT_URL = 'http://www.gravatar.com/avatar/?s=350&d=mm'
# Should be 2MB, current recommended
AVATAR_MAX_SIZE = 2*1024*1024

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
SOCIALACCOUNT_ADAPTER = 'coderdojochi.social_account_adapter.SocialAccountAdapter'
