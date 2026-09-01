import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = "django-insecure-change-this-in-production"
DEBUG = True
ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = [
    "https://hanulstudy.kr",
    "https://www.hanulstudy.kr",
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.naver",
    "main",
    "exam",
    "accounts",
    "gisa",
    "bbs",
]

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "config.urls"

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
                "accounts.context_processors.pending_signup_count",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "knou_agriculture",
        "USER": "knou_user",
        "PASSWORD": "knou1234",
        "HOST": "localhost",
        "PORT": "5432",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# 실기 필답형 기능에서 쓰는 모델 (용도별 분리)
# - 채점: 채점 기준표를 프롬프트로 주므로 판단 여지가 좁다. 최신 stable flash로 충분.
# - 손글씨 판독: 이미지 판독 정확도가 중요하므로 상위 모델을 쓴다.
GEMINI_ESSAY_GRADE_MODEL = os.getenv('GEMINI_ESSAY_GRADE_MODEL', 'gemini-3.7-flash')
GEMINI_ESSAY_OCR_MODEL = os.getenv('GEMINI_ESSAY_OCR_MODEL', 'gemini-3.1-pro-preview')

# 사용자당 하루 LLM 호출 한도 (채점·판독 각각)
ESSAY_DAILY_GRADE_LIMIT = int(os.getenv('ESSAY_DAILY_GRADE_LIMIT', '20'))
ESSAY_DAILY_OCR_LIMIT = int(os.getenv('ESSAY_DAILY_OCR_LIMIT', '40'))

# Email Backend (SMTP)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
# 발신자: Gmail이 admin@hanulstudy.kr를 강제로 gocompu21@gmail.com으로 교체하므로
# 처음부터 발신 계정으로 통일하되, 표시 이름은 "한울회 A+ 학습시스템"으로 유지
DEFAULT_FROM_EMAIL = '"한울회 A+ 학습시스템" <gocompu21@gmail.com>'
SERVER_EMAIL = DEFAULT_FROM_EMAIL

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/mypage/"
LOGOUT_REDIRECT_URL = "/"

# django-allauth
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

SOCIALACCOUNT_PROVIDERS = {
    "naver": {
        "APP": {
            "client_id": "YjvInKImqYAvMD0Pczsh",
            "secret": "JMVgXgtgBL",
        },
    },
}

ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = True
ACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
