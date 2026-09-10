"""아이디를 대소문자 구분 없이 받는 인증 백엔드.

모바일 키보드는 첫 글자를 자동으로 대문자로 바꾼다. `hong` 으로 가입한 회원이
폰에서 `Hong` 으로 입력하면 Django 기본 백엔드는 다른 사람으로 보고 로그인을
막는다. PC 에서는 되는데 폰에서만 안 되는 일이 여기서 생긴다.

아이디가 대소문자만 다른 회원이 둘 이상이면 판단할 수 없으므로 인증하지 않는다
(2026-09 현재 그런 중복은 없다).
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class CaseInsensitiveUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if username is None or password is None:
            return None

        try:
            user = User.objects.get(username__iexact=username.strip())
        except User.DoesNotExist:
            # 타이밍 공격을 막으려 존재하지 않는 경우에도 해시 계산을 한 번 돌린다
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
