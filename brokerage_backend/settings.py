from pathlib import Path
from datetime import timedelta
import dj_database_url
import dotenv
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-secret-key")


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "False") == "True"

ALLOWED_HOSTS = ["tronexi.onrender.com", "tronexi.com", "www.tronexi.com", "localhost", "127.0.0.1"]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'core',  # your app
    # other apps
    
    

    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'django_otp',
    'django_otp.plugins.otp_totp',

]

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Include your app-level static folders
STATICFILES_DIRS = [
    BASE_DIR / "brokerage_backend" / "static",
    BASE_DIR / "core" / "static",
]

# Whitenoise storage for better caching & compression
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',  # ✅ Add OTP Middleware
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

ROOT_URLCONF = 'brokerage_backend.urls'

# Load environment variables from .env file
dotenv.load_dotenv()

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # ✅ This tells Django where to look for your custom templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'brokerage_backend.wsgi.application'

# Database
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(default=DATABASE_URL)
    }
else:
    # Local fallback to SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ✅ Custom User Model
AUTH_USER_MODEL = 'core.CustomUser'

# ✅ REST Framework Config
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

# ✅ JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),  # 24-hour access token
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),   # 7-day refresh token
    'ROTATE_REFRESH_TOKENS': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# BROKEAGE_BACKEND APPLICATION FOR RADIS FOR CHANNEL LAYOUT 

ASGI_APPLICATION = 'brokerage_backend.asgi.application'

# Redis for channel layer
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get("REDIS_URL")],
        },
    },
}




USE_I18N = True

LANGUAGE_CODE = 'en'

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Long in and Out

LOGIN_REDIRECT_URL = '/dashboard/'  # where to go after successful login
LOGOUT_REDIRECT_URL = 'home'  # where to go after logout


# --- Email backend (DEV: console; PROD: SMTP) ---
# DEV (prints emails to the terminal):
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# PROD example (SMTP)
# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_HOST = "smtp.yourhost.com"
# EMAIL_PORT = 587
# EMAIL_HOST_USER = "no-reply@tronexi.com"
# EMAIL_HOST_PASSWORD = "********"
# EMAIL_USE_TLS = True

DEFAULT_FROM_EMAIL = "Tronexi <no-reply@tronexi.com>"

# --- Branding for emails ---
SITE_NAME = "Tronexi"
SITE_URL = "http://127.0.0.1:8000"  # set your real domain in prod
BRAND_LOGO_STATIC_PATH = "image/logo_nextwhite.png"  # your existing logo in /static/image/





LANGUAGES = [
    ('aa', 'Afar'),
    ('ab', 'Abkhazian'),
    ('ae', 'Avestan'),
    ('af', 'Afrikaans'),
    ('ak', 'Akan'),
    ('am', 'Amharic'),
    ('an', 'Aragonese'),
    ('ar', 'Arabic'),
    ('as', 'Assamese'),
    ('av', 'Avaric'),
    ('ay', 'Aymara'),
    ('az', 'Azerbaijani'),
    ('ba', 'Bashkir'),
    ('be', 'Belarusian'),
    ('bg', 'Bulgarian'),
    ('bh', 'Bihari languages'),
    ('bi', 'Bislama'),
    ('bm', 'Bambara'),
    ('bn', 'Bengali'),
    ('bo', 'Tibetan'),
    ('br', 'Breton'),
    ('bs', 'Bosnian'),
    ('ca', 'Catalan'),
    ('ce', 'Chechen'),
    ('ch', 'Chamorro'),
    ('co', 'Corsican'),
    ('cr', 'Cree'),
    ('cs', 'Czech'),
    ('cu', 'Church Slavic'),
    ('cv', 'Chuvash'),
    ('cy', 'Welsh'),
    ('da', 'Danish'),
    ('de', 'German'),
    ('dv', 'Divehi'),
    ('dz', 'Dzongkha'),
    ('ee', 'Ewe'),
    ('el', 'Greek'),
    ('en', 'English'),
    ('eo', 'Esperanto'),
    ('es', 'Spanish'),
    ('et', 'Estonian'),
    ('eu', 'Basque'),
    ('fa', 'Persian'),
    ('ff', 'Fulah'),
    ('fi', 'Finnish'),
    ('fj', 'Fijian'),
    ('fo', 'Faroese'),
    ('fr', 'French'),
    ('fy', 'Western Frisian'),
    ('ga', 'Irish'),
    ('gd', 'Scottish Gaelic'),
    ('gl', 'Galician'),
    ('gn', 'Guarani'),
    ('gu', 'Gujarati'),
    ('gv', 'Manx'),
    ('he', 'Hebrew'),
    ('hi', 'Hindi'),
    ('ho', 'Hiri Motu'),
    ('hr', 'Croatian'),
    ('ht', 'Haitian'),
    ('hu', 'Hungarian'),
    ('hy', 'Armenian'),
    ('hz', 'Herero'),
    ('ia', 'Interlingua'),
    ('id', 'Indonesian'),
    ('ie', 'Interlingue'),
    ('ii', 'Sichuan Yi'),
    ('ik', 'Inupiaq'),
    ('io', 'Ido'),
    ('is', 'Icelandic'),
    ('it', 'Italian'),
    ('iu', 'Inuktitut'),
    ('ja', 'Japanese'),
    ('jv', 'Javanese'),
    ('ka', 'Georgian'),
    ('kg', 'Kongo'),
    ('ki', 'Kikuyu'),
    ('kj', 'Kwanyama'),
    ('kk', 'Kazakh'),
    ('kl', 'Kalaallisut'),
    ('km', 'Khmer'),
    ('kn', 'Kannada'),
    ('ko', 'Korean'),
    ('kr', 'Kanuri'),
    ('ks', 'Kashmiri'),
    ('ku', 'Kurdish'),
    ('kv', 'Komi'),
    ('kw', 'Cornish'),
    ('ky', 'Kyrgyz'),
    ('la', 'Latin'),
    ('lb', 'Luxembourgish'),
    ('lg', 'Ganda'),
    ('li', 'Limburgish'),
    ('ln', 'Lingala'),
    ('lo', 'Lao'),
    ('lt', 'Lithuanian'),
    ('lu', 'Luba-Katanga'),
    ('lv', 'Latvian'),
    ('mg', 'Malagasy'),
    ('mh', 'Marshallese'),
    ('mi', 'Maori'),
    ('mk', 'Macedonian'),
    ('ml', 'Malayalam'),
    ('mn', 'Mongolian'),
    ('mr', 'Marathi'),
    ('ms', 'Malay'),
    ('mt', 'Maltese'),
    ('my', 'Burmese'),
    ('na', 'Nauru'),
    ('nb', 'Norwegian Bokmål'),
    ('nd', 'North Ndebele'),
    ('ne', 'Nepali'),
    ('ng', 'Ndonga'),
    ('nl', 'Dutch'),
    ('nn', 'Norwegian Nynorsk'),
    ('no', 'Norwegian'),
    ('nr', 'South Ndebele'),
    ('nv', 'Navajo'),
    ('ny', 'Chichewa'),
    ('oc', 'Occitan'),
    ('oj', 'Ojibwa'),
    ('om', 'Oromo'),
    ('or', 'Oriya'),
    ('os', 'Ossetian'),
    ('pa', 'Punjabi'),
    ('pi', 'Pali'),
    ('pl', 'Polish'),
    ('ps', 'Pashto'),
    ('pt', 'Portuguese'),
    ('qu', 'Quechua'),
    ('rm', 'Romansh'),
    ('rn', 'Kirundi'),
    ('ro', 'Romanian'),
    ('ru', 'Russian'),
    ('rw', 'Kinyarwanda'),
    ('sa', 'Sanskrit'),
    ('sc', 'Sardinian'),
    ('sd', 'Sindhi'),
    ('se', 'Northern Sami'),
    ('sg', 'Sango'),
    ('si', 'Sinhala'),
    ('sk', 'Slovak'),
    ('sl', 'Slovenian'),
    ('sm', 'Samoan'),
    ('sn', 'Shona'),
    ('so', 'Somali'),
    ('sq', 'Albanian'),
    ('sr', 'Serbian'),
    ('ss', 'Swati'),
    ('st', 'Southern Sotho'),
    ('su', 'Sundanese'),
    ('sv', 'Swedish'),
    ('sw', 'Swahili'),
    ('ta', 'Tamil'),
    ('te', 'Telugu'),
    ('tg', 'Tajik'),
    ('th', 'Thai'),
    ('ti', 'Tigrinya'),
    ('tk', 'Turkmen'),
    ('tl', 'Tagalog'),
    ('tn', 'Tswana'),
    ('to', 'Tonga'),
    ('tr', 'Turkish'),
    ('ts', 'Tsonga'),
    ('tt', 'Tatar'),
    ('tw', 'Twi'),
    ('ty', 'Tahitian'),
    ('ug', 'Uyghur'),
    ('uk', 'Ukrainian'),
    ('ur', 'Urdu'),
    ('uz', 'Uzbek'),
    ('ve', 'Venda'),
    ('vi', 'Vietnamese'),
    ('vo', 'Volapük'),
    ('wa', 'Walloon'),
    ('wo', 'Wolof'),
    ('xh', 'Xhosa'),
    ('yi', 'Yiddish'),
    ('za', 'Zhuang'),
    ('zh', 'Chinese'),
    ('zu','Zulu'),
]

