DEBUG = True

ADMINS = (
    ('Brett Kellgren', 'brett@coderdojochi.org'),
	('Ali Karbassi', 'ali@karbassi.com'),
)

TEMPLATE_DIRS = (
    './coderdojochi/templates/',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'coderdojochi',
        'USER': '',
        'PASSWORD': '',
        'HOST': '127.0.0.1'
    }
}

MANDRILL_API_KEY = '2zSMfCAUBJA4aCqJAU-wIw'
EMAIL_BACKEND = 'djrill.mail.backends.djrill.DjrillBackend'
EMAIL_HOST = 'smtp.mandrillapp.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'coderdojochi'
EMAIL_HOST_PASSWORD = ''
DEFAULT_FROM_EMAIL = 'info@coderdojochi.org'
SERVER_EMAIL = 'info@coderdojochi.org'
