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

TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = ['*']


SITE_URL = 'http://localhost:8000'

# Application definition

INSTALLED_APPS = (
    # django contrib
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    #vendor
    'registration',
    'social_auth',
    'south',
    'avatar',
    'bootstrap3',
    'html5',
    'contact_form',
    'djrill',

    #coderdojochi
    'coderdojochi',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request'
)

AUTHENTICATION_BACKENDS = (
    'social_auth.backends.facebook.FacebookBackend',
    'social_auth.backends.google.GoogleOAuth2Backend',
    'django.contrib.auth.backends.ModelBackend',
)

ROOT_URLCONF = 'coderdojochi.urls'

WSGI_APPLICATION = 'coderdojochi.wsgi.application'



# Registration
ACCOUNT_ACTIVATION_DAYS = 7
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dojo/'
LOGIN_ERROR_URL = '/accounts/login/'
GOOGLE_OAUTH2_CLIENT_ID = '294736693640-inucj2ptaap06iggukfurmqihblavbt8.apps.googleusercontent.com'
GOOGLE_OAUTH2_CLIENT_SECRET = 'rgdutyo5mqCN7yOIMxET9hHv'
GOOGLE_DISPLAY_NAME = 'CoderDojoChi'
FACEBOOK_APP_ID = '1454178301519376'
FACEBOOK_API_SECRET = '36edff0d6d4a9686647f76f2d0f511ed'
SESSION_SERIALIZER='django.contrib.sessions.serializers.PickleSerializer'

AUTH_USER_MODEL = 'coderdojochi.CDCUser'
SOCIAL_AUTH_USER_MODEL = 'coderdojochi.CDCUser'

SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True

# Email
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: '/var/www/example.com/media/'
MEDIA_ROOT = os.path.join(PACKAGE_ROOT, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: 'http://example.com/media/', 'http://media.example.com/'
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' 'static/' subdirectories and in STATICFILES_DIRS.
# Example: '/var/www/example.com/static/'
MEDIA_ROOT = os.path.join(PACKAGE_ROOT, 'static')

# URL prefix for static files.
# Example: 'http://example.com/static/', 'http://static.example.com/'
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like '/home/html/static' or 'C:/www/django/static'.
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    #'/Users/bkellgren/Sites/arb/arb/admin_bootstrap/static',
    os.path.join(PACKAGE_ROOT, 'static'),
)

TEMPLATE_DIRS = (
    '/Users/bkellgren/Sites/coderdojochi/coderdojochi/templates/',
)

# Vender App Config

AVATAR_GRAVATAR_BACKUP = False
AVATAR_DEFAULT_URL = 'http://www.gravatar.com/avatar/?s=350&d=mm'


# search for environment specific settings to override settings.py

try:
    from local_settings import *
except ImportError:
    pass

try:
    from test_settings import *
except ImportError:
    pass

try:
    from production_settings import *
except ImportError:
    pass
