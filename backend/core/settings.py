from celery.schedules import crontab
from dotenv import load_dotenv
from datetime import timedelta
from pathlib import Path
import os, dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

DEBUG = str(os.getenv("DEBUG", "True")).lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY") or "dev-secret-for-local"
DEFAULT_ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
USER_ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "").split(",")
    if host.strip()
]
ALLOWED_HOSTS = list(dict.fromkeys(DEFAULT_ALLOWED_HOSTS + USER_ALLOWED_HOSTS))
HOST_DOMAIN_URL = os.getenv("HOST") or "http://127.0.0.1:8000"

if not DEBUG:
    SESSION_COOKIE_SECURE = str(os.getenv("SESSION_COOKIE_SECURE", "False")).lower() == "true"
    CSRF_COOKIE_SECURE = str(os.getenv("CSRF_COOKIE_SECURE", "False")).lower() == "true"
    SECURE_SSL_REDIRECT = str(os.getenv("SECURE_SSL_REDIRECT", "False")).lower() == "true"


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    # apps
    "accounts",  # This app is for user and admin accounts
    "audits",  # This app is for logging of audits to keep track of certain activities
    "docs",  # This app is for the documentation of the api endpoints
    "quizzes",  # This app is for the quiz section of the system
    "wallet",
    "premium",  # Hold all premium packages
    "payments",  # This app is the gateway integration
    "referral",  # This app is the referral system
    "notifications",  # In-app / email / sms notifications (email & sms on hold)
    # "wallet.apps.WalletConfig",
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

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "core.wsgi.application"


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

# DATABASES = {
#     "default": {
#         "ENGINE": os.getenv("DB_ENGINE"),
#         "NAME": BASE_DIR / os.getenv("DB_NAME"),
#         "USER": os.getenv("DB_USER"),
#         "PASSWORD": os.getenv("DB_PASSWORD"),
#         "HOST": os.getenv("DB_HOST"),
#         "PORT": os.getenv("DB_PORT"),
#     }
# }


db_url = os.getenv("DATABASE_URL")
if db_url:
    DATABASES = {
        "default": dj_database_url.config(
            default=db_url,
            conn_max_age=0,
            ssl_require=not db_url.startswith("sqlite://"),
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
            "NAME": os.getenv("DB_NAME", BASE_DIR / "db.sqlite3"),
            "USER": os.getenv("DB_USER", ""),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", ""),
            "PORT": os.getenv("DB_PORT", ""),
        }
    }

if DATABASES["default"]["ENGINE"].endswith("sqlite3"):
    DATABASES["default"]["OPTIONS"] = {"timeout": 20}
else:
    DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True

# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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

AUTH_USER_MODEL = "accounts.User"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "login_user": "10/min",
        "login_admin": "3/min",
        "register": "3/min",
        "resend_verification": "3/hour",
        "admin_register": "3/min",
        "delete_user": "3/min",
        "password_reset": "3/min",
        "token_refresh": "10/min",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}
TOKEN_VERIFICATION_DURATION = 1800  # Token is valid for 30min


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]


# Email Config
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend",
)

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = str(os.getenv("EMAIL_USE_TLS", "True")).lower() == "true"
EMAIL_USE_SSL = str(os.getenv("EMAIL_USE_SSL", "False")).lower() == "true"

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    "Security <no-reply@uptorps.com>",
)

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get(
    "CELERY_RESULT_BACKEND", "redis://localhost:6379/1"
)
CELERY_BEAT_SCHEDULE = {
    "reconcile-all-wallets": {
        "task": "wallet.tasks.reconcile_all_wallets",
        "schedule": crontab(hour=2, minute=0),  # runs every day at 2am
    },
}

# Payment / withdrawal simulation (Hubtel access pending).
# Keep enabled for manager demos; turn off once a real gateway is wired.
PAYMENT_SIMULATION_ENABLED = os.getenv("PAYMENT_SIMULATION_ENABLED", "True") == "True"
# success | failure | random — default success so demos are reliable
PAYMENT_SIMULATION_OUTCOME = os.getenv("PAYMENT_SIMULATION_OUTCOME", "success").lower()
SIMULATED_CHECKOUT_URL = os.getenv(
    "SIMULATED_CHECKOUT_URL",
    "https://checkout.simulation.uptorps.local/pay",
)
