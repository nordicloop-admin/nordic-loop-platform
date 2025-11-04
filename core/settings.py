from pathlib import Path
import environ
import dj_database_url
from pathlib import Path
import os
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

# Environment configuration
# ENV = env('DJANGO_ENV', 'development').lower()
ENV = env('DJANGO_ENV')
PRODUCTION = ENV == 'production'
DEBUG = env.bool('DJANGO_DEBUG', default=not PRODUCTION)


# Security settings
SECRET_KEY = env('DJANGO_SECRET_KEY')

# Hosts / Domains the Django site can serve.
# You can override these in your .env file with a comma-separated list, e.g.:
# DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,nordic-loop-platform.onrender.com,my.custom.domain
# django-environ's `env.list` will split on commas and (by default) also on spaces.
ALLOWED_HOSTS = env.list(
    'DJANGO_ALLOWED_HOSTS',
    default=[
        "app",
        "127.0.0.1",
        "localhost",
        "magical-outgoing-grizzly.ngrok-free.app",  # Backend ngrok URL (override/remove in production env var)
        "nordic-loop-platform.onrender.com",
    ]
)
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=['http://localhost:3000'])

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',  # Add token blacklist support
    'corsheaders',
    'django_extensions',
    'base.apps.BaseConfig',
    'company.apps.CompanyConfig',
    'users',
    'category',
    'ads',
    'bids',
    'notifications.apps.NotificationsConfig',
    'category_subscriptions',
    'pricing.apps.PricingConfig',
    'payments.apps.PaymentsConfig',

]
AUTH_USER_MODEL = 'users.User'


MIDDLEWARE = [
    'core.middleware.http_metrics.HttpMetricsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
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
        'DIRS': [],
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

WSGI_APPLICATION = 'core.wsgi.application'

# Database
# https://docs.djangoproject.com/en/stable/ref/settings/#databases
# https://github.com/jazzband/dj-database-url

DATABASE_URL = os.getenv("DATABASE_URL")
SECONDARY_DATABASE_URL = env('SECONDARY_DATABASE_URL', default=None)

if DEBUG:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'dbv2.sqlite3',
        }
    }

# Optional secondary database (used for cloning / migration)
if SECONDARY_DATABASE_URL:
    DATABASES['secondary'] = dj_database_url.parse(
        SECONDARY_DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
    )

# Authentication
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

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_PAGINATION_CLASS': 'base.utils.pagination.StandardResultsSetPagination',
    'PAGE_SIZE': 10
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files (User-uploaded files)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Simplified static file serving.
# https://warehouse.python.org/project/whitenoise/
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Security headers
if not DEBUG and PRODUCTION:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# CORS Configuration
CORS_ALLOWED_ORIGINS = (
    "http://localhost:3000",
    "https://testingnordicloop.vercel.app",
    "https://nordicloop.onrender.com",
    "https://nordicloop.se",
    # "https://magical-outgoing-grizzly.ngrok-free.app",  # Backend ngrok URL
   

)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = (
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
)
CORS_ALLOW_HEADERS = (
    "accept",
    "authorization",
    "content-type",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
)

# Additional CORS settings for debugging
CORS_ALLOW_ALL_ORIGINS = True  # Only for development - allows any origin
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.ngrok-free\.app$",
    r"^https://.*\.ngrok\.io$",
]

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Helper function to read RSA keys from files
def read_key_from_file(key_path):
    """Read RSA key from file"""
    try:
        full_path = BASE_DIR / key_path.lstrip('./')
        with open(full_path, 'r') as key_file:
            return key_file.read()
    except FileNotFoundError:
        if DEBUG:
            print(f"Warning: JWT key file not found: {key_path}")
        return None

SIMPLE_JWT = {
    # Token lifetimes - shorter for better security
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),  # 15 minutes instead of 1 day
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),     # 7 days instead of 90
    
    # Use RS256 algorithm with RSA key pair
    "ALGORITHM": "RS256",
    "SIGNING_KEY": read_key_from_file(env('JWT_PRIVATE_KEY_PATH', default='./jwt_private_key.pem')),
    "VERIFYING_KEY": read_key_from_file(env('JWT_PUBLIC_KEY_PATH', default='./jwt_public_key.pem')),
    
    # Token rotation and blacklist settings
    "ROTATE_REFRESH_TOKENS": True,          # Generate new refresh token on use
    "BLACKLIST_AFTER_ROTATION": True,       # Blacklist old refresh tokens
    "UPDATE_LAST_LOGIN": True,              # Track login times
    
    # JWT Claims configuration
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    
    # Token validation
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    
    # Additional claims for security and functionality
    "JTI_CLAIM": "jti",                     # JWT ID for revocation
    
    # Use custom token classes that include additional claims
    "TOKEN_OBTAIN_SERIALIZER": "users.serializers.CustomTokenObtainPairSerializer",
}



ASGI_APPLICATION = "core.asgi.application"
if PRODUCTION:
    BASE_LINK = "https://nordic-loop-platform.onrender.com/"
else:
    BASE_LINK = "http://127.0.0.1:8000/"

# Firebase Configuration
FIREBASE_STORAGE_BUCKET = env('FIREBASE_STORAGE_BUCKET', default='your-project-id.appspot.com')
FIREBASE_CREDENTIALS_PATH = env('FIREBASE_CREDENTIALS_PATH', default=None)

# Cloudflare R2 Configuration
USE_R2 = env.bool('USE_R2', default=False)
CLOUDFLARE_ACCOUNT_ID = env('CLOUDFLARE_ACCOUNT_ID', default='')
CLOUDFLARE_R2_BUCKET = env('CLOUDFLARE_R2_BUCKET', default='')
CLOUDFLARE_R2_ACCESS_KEY_ID = env('CLOUDFLARE_R2_ACCESS_KEY_ID', default='')
CLOUDFLARE_R2_SECRET_ACCESS_KEY = env('CLOUDFLARE_R2_SECRET_ACCESS_KEY', default='')
R2_PUBLIC_BASE_URL = env('R2_PUBLIC_BASE_URL', default='')
R2_SIGNED_URL_TTL = env.int('R2_SIGNED_URL_TTL', default=3600)
DUAL_WRITE_R2 = env.bool('DUAL_WRITE_R2', default=False)

# Backend URL for local image serving
BACKEND_URL = env('BACKEND_URL', default='http://127.0.0.1:8000')

# Firebase environment variables for production (when not using service account file)
# These should be set in your production environment:
# GOOGLE_APPLICATION_CREDENTIALS (path to service account JSON)
# Or individual Firebase config variables

# Stripe settings
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET', default='')

# Frontend URL for Stripe redirects
FRONTEND_URL = env('FRONTEND_URL', default='http://localhost:3000')

# Email settings (if not already configured)
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = env('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@nordicloop.com')