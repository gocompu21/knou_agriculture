import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


# 한글(자모 + 음절) 1자 이상 포함 여부 체크
_HANGUL_RE = re.compile(r"[가-힣ᄀ-ᇿ㄰-㆏]")


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="이메일 주소를 입력해주세요.")
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label="이름",
        help_text="한글 실명을 입력해주세요. (예: 홍길동)",
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "email", "password1", "password2")

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("사용자 이름이 이미 있습니다.")
        return username

    def clean_first_name(self):
        # 검증 규칙 (조용히, 통합 메시지로):
        # - 2자 이상
        # - 한글(자모/음절) 1자 이상 포함
        # - 한글/영문/공백/괄호 외 특수문자 금지
        # 봇이 어느 규칙을 어겼는지 알 수 없도록 동일한 일반 메시지 사용
        name = (self.cleaned_data.get("first_name") or "").strip()
        invalid = (
            len(name) < 2
            or not _HANGUL_RE.search(name)
            or bool(re.search(r"[^가-힣ᄀ-ᇿ㄰-㆏ a-zA-Z()]", name))
        )
        if invalid:
            raise forms.ValidationError("입력하신 정보를 확인해 주세요.")
        return name

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("이메일이 이미 있습니다.")
        return email


class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=254)
    password = forms.CharField(widget=forms.PasswordInput)
