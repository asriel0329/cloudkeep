"""
Django settings for the Cloud Drive project.

app/ 這個資料夾同時是 Django 專案設定所在地，也是各功能模組
(auth, files, folders, shares, permissions, storage) 的容器。
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# 讀取 backend/.env（本機直接跑 python manage.py 時用得到；
# Docker Compose 則是透過 env_file 直接注入環境變數）
load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# 基本設定
# ---------------------------------------------------------------------------

SECRET_KEY = os.environ.get("SECRET_KEY", "insecure-dev-key-change-me")

DEBUG = os.environ.get("DEBUG", "True") == "True"

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")


# ---------------------------------------------------------------------------
# App 註冊
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 第三方套件
    "rest_framework",
    "corsheaders",
    # 專案內部模組（批次進度陸續打開）
    "app.auth",
    "app.folders",
    "app.files",
    "app.permissions",
    "app.shares",
    "app.auditlog",
]

# 告訴 Django：整個專案要用哪個 model 當「使用者」，
# 格式是 "app_label.ModelName"。因為 app/auth/apps.py 裡
# 把 app_label 設成了 "accounts"（避免跟內建 auth 撞名），
# 所以這裡要寫 "accounts.User"，不是 "auth.User"。
AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "app.wsgi.application"
ASGI_APPLICATION = "app.asgi.application"

# ---------------------------------------------------------------------------
# 資料庫（PostgreSQL，設定值來自 .env / docker-compose 注入的環境變數）
# ---------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "cloud_drive"),
        "USER": os.environ.get("POSTGRES_USER", "cloud_drive"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "changeme"),
        "HOST": os.environ.get("POSTGRES_HOST", "db"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

# ---------------------------------------------------------------------------
# 密碼驗證規則
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# 國際化
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "zh-hant"
TIME_ZONE = "Asia/Taipei"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Celery（P3-3 才會真正處理任務，這裡先讓連線設定就緒）
# ---------------------------------------------------------------------------

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# ---------------------------------------------------------------------------
# 靜態檔案 / 媒體檔案
# ---------------------------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = os.environ.get("MEDIA_ROOT", str(BASE_DIR / "media"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# ---------------------------------------------------------------------------
# CORS（開發階段先全開，正式環境要收緊）
# ---------------------------------------------------------------------------

CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS", "http://localhost:5666"
).split(",")

# 前後端是不同 port（不同 origin），Django 的 CSRF 保護需要明確知道
# 哪些外部來源是「可信任的」，才會接受帶著 CSRF token 的跨來源請求。
CSRF_TRUSTED_ORIGINS = os.environ.get(
    "CSRF_TRUSTED_ORIGINS", "http://localhost:5666"
).split(",")

# SessionAuthentication 預設會檢查 CSRF token，前端（React）要打帶
# cookie 的 API 時，記得也要一併處理 CSRF cookie，不然 POST 會被擋。
# 開發階段先允許帶 credentials 的跨來源請求：
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Storage backend 設定（批次 3 才會實際用到，先留欄位）
# ---------------------------------------------------------------------------

STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "local")

# S3 / MinIO 設定（STORAGE_BACKEND=s3 時才會用到）
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", "cloudkeep-files")
AWS_S3_ENDPOINT_URL = os.environ.get("AWS_S3_ENDPOINT_URL", "")