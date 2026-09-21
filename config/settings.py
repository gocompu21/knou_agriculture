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

# 쪽집게 노트 인포그래픽 생성용. 한글이 많이 들어가 정확도가 중요하므로
# 속도(flare)가 아니라 품질(sunburst) 쪽을 쓴다.
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_IMAGE_MODEL = os.getenv('OPENAI_IMAGE_MODEL', 'gpt-image-2.5-sunburst')

# 잡초 카드 등록 때 사진 후보를 가져올 곳.
# 위키미디어 공용은 키가 필요 없다. 국립수목원(국가생물종지식정보시스템)은
# 공공데이터포털에서 키를 받아 넣으면 한국 자생종 사진이 함께 나온다.
NATURE_API_KEY = os.getenv('NATURE_API_KEY', '')

# 실기 필답형 기능에서 쓰는 모델 (용도별 분리)
# - 채점: 채점 기준표를 프롬프트로 주므로 판단 여지가 좁다. 최신 stable flash로 충분.
# - 손글씨 판독: 정확도가 중요해 Pro 를 쓴다. 3세대 Pro 는 preview 뿐이라 종료되면
#   사진 제출이 멈추니 그때는 flash 로 바꾼다. 비용은 차이가 없다 — 2026-09 에 같은
#   시험지 1쪽을 재 보니 pro 11원, 3.8-flash 7원(생각 토큰 531 이 출력으로 청구)이고
#   flash 는 2027-01 부터 두 배가 되어 pro 보다 비싸진다.
GEMINI_ESSAY_GRADE_MODEL = os.getenv('GEMINI_ESSAY_GRADE_MODEL', 'gemini-3.8-flash')
GEMINI_ESSAY_OCR_MODEL = os.getenv('GEMINI_ESSAY_OCR_MODEL', 'gemini-3.1-pro-preview')

# 객관식(필기) 선지별 해설 생성. **preview 를 쓰지 않는다** — 예고 없이 종료되는데,
# 학습모드의 '설명 가져오기'는 관리자가 지금도 누르는 버튼이라 그날로 깨진다.
# 대량 생성은 이미 끝났고(방송대 8,940 · 기사 6,800여 문항) 지금은 문항을 새로
# 넣을 때만 돈다. 각 명령의 --model 로 그때그때 바꿀 수 있다.
GEMINI_EXPLAIN_MODEL = os.getenv('GEMINI_EXPLAIN_MODEL', 'gemini-3.8-flash')

# 그 밖의 일반 호출 — 최신기출 텍스트 파싱(api_parse_text), 잡초 카드 종 정보
# 조회(api_weed_name_check). 구조화 추출이라 flash 로 충분하다.
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-3.8-flash')

# 질의응답(main/qna.py). 회원이 쓰는 기능이라 답변 품질이 곧 체감이다.
GEMINI_QNA_MODEL = os.getenv('GEMINI_QNA_MODEL', 'gemini-3.8-flash')

# 동영상 요약(gisa/video_summary.py). 유튜브 주소를 그대로 넘겨 영상을 보게 한다.
# 관리자만 쓰고 영상 한 편에 한 번이라 flash 로 충분하다.
GEMINI_VIDEO_MODEL = os.getenv('GEMINI_VIDEO_MODEL', 'gemini-3.8-flash')

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
    # 모바일 키보드가 아이디 첫 글자를 대문자로 바꿔 폰에서만 로그인이 안 되는
    # 일이 있었다. 대소문자를 무시하는 백엔드를 앞에 둔다.
    "accounts.backends.CaseInsensitiveUsernameBackend",
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
