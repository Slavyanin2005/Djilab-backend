"""
Django settings for djilab project.
"""

from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY")

DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="*", cast=Csv())

INSTALLED_APPS = [
    "django_prometheus",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "catalog",
    "drf_spectacular",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # ✅ ПЕРВЫМ!
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:4173",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.0.107:5173",
    "http://tauri.localhost",
    "tauri://localhost",
    "http://localhost:1420",
    "https://slavyanin2005.github.io",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = config(
    "CORS_ALLOW_HEADERS",
    default="accept,accept-encoding,authorization,content-type,dnt,origin,user-agent,x-csrftoken,x-requested-with",
    cast=Csv(),
)
CORS_EXPOSE_HEADERS = ["set-cookie", "content-length", "content-type"]

ROOT_URLCONF = "djilab.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "djilab.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST"),
        "PORT": config("DB_PORT"),
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "catalog": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://redis:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "djilab",
    }
}

CACHE_TTL = 60

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

LANGUAGE_CODE = config("LANGUAGE_CODE", default="ru-ru")
TIME_ZONE = config("TIME_ZONE", default="Europe/Moscow")
USE_I18N = config("USE_I18N", default=True, cast=bool)
USE_TZ = config("USE_TZ", default=True, cast=bool)

STATIC_URL = config("STATIC_URL", default="/static/")
STATIC_ROOT = BASE_DIR / "staticfiles"

MINIO_URL = config("MINIO_URL")
MINIO_BUCKET = config("MINIO_BUCKET")
MINIO_ACCESS_KEY = config("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = config("MINIO_SECRET_KEY")

MEDIA_URL = f"{MINIO_URL}/{MINIO_BUCKET}/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ORDER_STATUS_CHOICES = [
    ("draft", "Черновик"),
    ("deleted", "Удалён"),
    ("formed", "Сформирован"),
    ("completed", "Завершён"),
    ("rejected", "Отклонён"),
]

SERVICE_STATUS_CHOICES = [
    ("active", "Действует"),
    ("deleted", "Удалён"),
]

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:4173",
    "http://127.0.0.1:5173",
    "http://192.168.0.107:5173",
    "http://tauri.localhost",
    "https://192.168.0.107:8000",
    "http://backend:8000",
    "tauri://localhost",
    "http://localhost:1420",
    "https://slavyanin2005.github.io",
]

SESSION_COOKIE_SAMESITE = "None"
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_DOMAIN = None

CSRF_COOKIE_SAMESITE = "None"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False

SPECTACULAR_SETTINGS = {
    "TITLE": "DJI Lab API",
    "DESCRIPTION": "API для системы заказа лабораторного оборудования",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": True,
    "COMPONENT_SPLIT_REQUEST": True,
    "ENUM_NAME_OVERRIDES": {
        "OrderStatusEnum": "catalog.models.ORDER_STATUS_CHOICES",
        "ServiceStatusEnum": "catalog.models.SERVICE_STATUS_CHOICES",
    },
}
