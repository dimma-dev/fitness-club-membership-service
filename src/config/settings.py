from pathlib import Path
from datetime import timedelta

import dj_database_url
from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent

SECRET_KEY = config("SECRET_KEY", default="django-insecure-77rp0gyhi2(e(b8(qz3y+vqarbean2mw@8$jvkfl1=rbeo_=zd")
DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS", default="localhost,127.0.0.1,web,django_web", cast=Csv()
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "django_filters",
    "drf_spectacular",
    "users"
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


DATABASE_URL = config("DATABASE_URL", default="")
if not DATABASE_URL and config("POSTGRES_DB", default=""):
    DATABASE_URL = (
        f"postgres://{config('POSTGRES_USER')}:{config('POSTGRES_PASSWORD')}"
        f"@{config('POSTGRES_HOST', default='db')}:{config('POSTGRES_PORT', default='5432')}"
        f"/{config('POSTGRES_DB')}"
    )


if DATABASE_URL:
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]



LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Kyiv"
USE_I18N = True
USE_TZ = True



STATIC_URL = config("STATIC_URL", default="/static/")
STATIC_ROOT = ROOT_DIR / "staticfiles"  #

MEDIA_URL = config("MEDIA_URL", default="/media/")
MEDIA_ROOT = ROOT_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- DJANGO REST FRAMEWORK ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


# --- DRF SPECTACULAR ---
SPECTACULAR_SETTINGS = {
    "TITLE": "Fitness Club Membership API",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]",
    "COMPONENT_SPLIT_REQUEST": True,
    "SECURITY": [{"bearerAuth": []}],
}

# --- CELERY ----
CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://redis:6379/0")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default="redis://redis:6379/0")
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Europe/Kyiv"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60

# --Production security ----
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
