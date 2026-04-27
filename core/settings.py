from pathlib import Path
from decouple import config
import dj_database_url
import os
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-=c^uynh9*!efh=v-g$ap9z=t$5=v04o=220kod479#h3=7mmp1')

DEBUG = True #config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default=['*']) #przystanekperfumy.pl

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'products',
    'sellers',
    'orders',
    'policies',
    'import_export',
    'cloudinary_storage',
    'cloudinary',
    'django.contrib.sitemaps',
    'reviews',
    'blog',
    'anymail',
]
CSRF_TRUSTED_ORIGINS = [
    'https://web-production-0c35c.up.railway.app',
    'https://przystanekperfumy.pl',
    'https://www.przystanekperfumy.pl',
]

SITE_URL = 'https://przystanekperfumy.pl'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

DATABASE_URL = config('DATABASE_URL', default=None)
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST'),
            'PORT': config('DB_PORT'),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pl'
TIME_ZONE = 'Europe/Warsaw'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

LOGIN_REDIRECT_URL = '/panel/'
LOGOUT_REDIRECT_URL = '/'

EMAIL_BACKEND = 'anymail.backends.sendinblue.EmailBackend'
# EMAIL_HOST = config('EMAIL_HOST', default='smtp-relay.brevo.com')
# EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
# EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
# EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
# EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
# EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='')
CONTACT_EMAIL = config('CONTACT_EMAIL', default='')
ANYMAIL = {
    "SENDINBLUE_API_KEY": config("BREVO_API_KEY", default=''),
}
BREVO_API_KEY = config('BREVO_API_KEY', default='')

# if not EMAIL_HOST_USER:
#     EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Cloudinary – opcjonalne, tylko jeśli zmienne istnieją
CLOUDINARY_CLOUD_NAME = config('CLOUDINARY_CLOUD_NAME', default='')
CLOUDINARY_API_KEY = config('CLOUDINARY_API_KEY', default='')
CLOUDINARY_API_SECRET = config('CLOUDINARY_API_SECRET', default='')

if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': CLOUDINARY_CLOUD_NAME,
        'API_KEY': CLOUDINARY_API_KEY,
        'API_SECRET': CLOUDINARY_API_SECRET,
    }
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
else:
    # Fallback na lokalne przechowywanie plików (lub inne)
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

CSRF_TRUSTED_ORIGINS = [
    'https://web-production-0c35c.up.railway.app',
    'https://przystanekperfumy.pl',
    'https://www.przystanekperfumy.pl',
]

SITE_URL = 'http://127.0.0.1:8000'  # lub http://127.0.0.1:8000 lokalnie #https://web-production-0c35c.up.railway.app/
ANTHROPIC_API_KEY = config('ANTHROPIC_API_KEY', default='')

LANGUAGE_CODE = 'pl'

LANGUAGES = [
    ('pl', 'Polski'),
    ('es', 'Español'),
]

USE_I18N = True
USE_L10N = True

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]