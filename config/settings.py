"""Django settings for the KGU admissions assistant."""
import os
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_SECURE=(bool, False),
    DJANGO_BEHIND_PROXY=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")


def _raw_env(name, default=""):
    """Read .env as-is: django-environ treats a leading $ as another variable."""
    value = os.environ.get(name, default)
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return value


SECRET_KEY = _raw_env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = [
    host.strip()
    for host in env("DJANGO_ALLOWED_HOSTS", default="").split(",")
    if host.strip()
]
if DEBUG:
    if not SECRET_KEY:
        SECRET_KEY = "unsafe-dev-key"
    for host in ("127.0.0.1", "localhost", "testserver"):
        if host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(host)
else:
    if not SECRET_KEY or SECRET_KEY in {"change-me", "unsafe-dev-key"}:
        raise ImproperlyConfigured(
            "Задайте DJANGO_SECRET_KEY в .env для production. "
            "Кавычки не нужны. Ключ с $ в начале Django читает как есть."
        )
    if not ALLOWED_HOSTS:
        raise ImproperlyConfigured("Задайте DJANGO_ALLOWED_HOSTS в .env для production.")
    if "*" in ALLOWED_HOSTS:
        raise ImproperlyConfigured("Не используйте * в DJANGO_ALLOWED_HOSTS в production.")

USE_HTTPS = env("DJANGO_SECURE") or not DEBUG
BEHIND_PROXY = (not DEBUG) or env("DJANGO_BEHIND_PROXY") or USE_HTTPS
# nginx already terminates TLS. Django must not 301 HTTP→HTTPS or the
# proxy loop (https → waitress http → 301 https) never ends.
SSL_REDIRECT = env.bool("DJANGO_SSL_REDIRECT", default=False)

CSRF_TRUSTED_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in env("DJANGO_CSRF_TRUSTED_ORIGINS", default="").split(",")
    if origin.strip()
]
for host in ALLOWED_HOSTS:
    if host in {"testserver"} or host.startswith("."):
        continue
    https_origin = f"https://{host}"
    http_origin = f"http://{host}"
    if https_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(https_origin)
    if host in {"127.0.0.1", "localhost"} and http_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(http_origin)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "knowledge",
    "qa",
    "dashboard",
    "botapp",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
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

WSGI_APPLICATION = "config.wsgi.application"

database_url = env("DATABASE_URL", default="")
if database_url:
    DATABASES = {"default": env.db("DATABASE_URL")}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
            "OPTIONS": {"timeout": 20},
        }
    }

if "sqlite" in DATABASES["default"]["ENGINE"]:
    DATABASES["default"].setdefault("OPTIONS", {})["timeout"] = 20
    DATABASES["default"]["CONN_MAX_AGE"] = 0
else:
    DATABASES["default"]["CONN_MAX_AGE"] = env.int("DJANGO_CONN_MAX_AGE", default=60)

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Asia/Almaty"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
WHITENOISE_USE_FINDERS = DEBUG
WHITENOISE_AUTOREFRESH = DEBUG

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "dashboard:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "dashboard:login"

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_AGE = 60 * 60 * 8
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

if BEHIND_PROXY:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True

if USE_HTTPS:
    SECURE_SSL_REDIRECT = SSL_REDIRECT
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=0)
    if SECURE_HSTS_SECONDS:
        SECURE_HSTS_INCLUDE_SUBDOMAINS = True
        SECURE_HSTS_PRELOAD = True

FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "app.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "django.request": {
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

TELEGRAM_TOKEN = _raw_env("TELEGRAM_TOKEN")
OPENAI_API_KEY = _raw_env("OPENAI_API_KEY")
EMBEDDING_MODEL = env("EMBEDDING_MODEL", default="text-embedding-3-small")
CHAT_MODEL = env("CHAT_MODEL", default="gpt-4o-mini")
FAISS_SCORE_THRESHOLD = env.float("FAISS_SCORE_THRESHOLD", default=1.35)
SUPPORT_WHATSAPP = env("SUPPORT_WHATSAPP", default="https://wa.me/77786926834")
FAISS_INDEX_DIR = BASE_DIR / "faiss_index"
CHAT_HISTORY_LIMIT = 12
