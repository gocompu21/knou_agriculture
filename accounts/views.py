import random
import string

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse

from .forms import LoginForm, SignUpForm
from .models import EmailVerificationToken


def _send_verification_email(request, user, token):
    """가입 인증 메일 발송 (HTML)"""
    verify_path = reverse("accounts:verify_email", args=[str(token.token)])
    verify_url = request.build_absolute_uri(verify_path)
    html = render_to_string(
        "accounts/email/verify_email.html",
        {"user": user, "verify_url": verify_url},
    )
    msg = EmailMessage(
        "[한울회 A+] 회원가입 이메일 인증 안내",
        html,
        None,  # settings.DEFAULT_FROM_EMAIL 사용
        [user.email],
    )
    msg.content_subtype = "html"
    msg.send(fail_silently=False)


def _notify_admin_signup(user, request):
    """관리자에게 신규 가입 알림 메일 (백그라운드 발송)."""
    import threading

    def _send():
        try:
            ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() \
                or request.META.get("REMOTE_ADDR", "")
            ua = request.META.get("HTTP_USER_AGENT", "")[:200]
            body = (
                f"새 회원이 가입 신청했습니다. 관리자 승인이 필요합니다.\n\n"
                f"아이디  : {user.username}\n"
                f"이름    : {user.first_name}\n"
                f"이메일  : {user.email}\n"
                f"가입시각: {user.date_joined:%Y-%m-%d %H:%M:%S}\n"
                f"IP      : {ip}\n"
                f"User-Agent: {ua}\n\n"
                f"※ 승인하면 사용자에게 이메일 인증 메일이 발송됩니다.\n"
                f"※ 승인/거부: https://hanulstudy.kr/manage/members/?tab=pending\n"
            )
            EmailMessage(
                f"[한울회 A+] 신규 가입: {user.first_name}({user.username})",
                body,
                None,  # settings.DEFAULT_FROM_EMAIL 사용
                ["gocompu21@gmail.com"],
            ).send(fail_silently=True)
        except Exception:
            pass

    threading.Thread(target=_send, daemon=True).start()


def user_signup(request):
    if request.method == "POST":
        # honeypot: 사용자에게 보이지 않는 'website' 필드에 값이 들어오면 봇으로 간주
        if request.POST.get("website", "").strip():
            import logging
            logging.getLogger("django").warning(
                "Bot signup blocked (honeypot): username=%s ip=%s",
                request.POST.get("username", ""),
                request.META.get("REMOTE_ADDR", ""),
            )
            # 일반 에러처럼 보여 봇이 우회 학습 못 하게 함
            from django.contrib import messages as _msg
            _msg.error(request, "잠시 후 다시 시도해 주세요.")
            return render(request, "accounts/signup.html", {"form": SignUpForm()})

        # 비활성 상태로 이미 가입한 사용자가 같은 username/email로 다시 시도한 경우
        # → 승인 대기 안내 페이지로 다시 안내 (관리자에게 알림 재발송)
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        if username and email:
            existing = User.objects.filter(
                username=username, email=email, is_active=False
            ).first()
            if existing:
                _notify_admin_signup(existing, request)
                return render(
                    request,
                    "accounts/signup_pending.html",
                    {"email": existing.email, "resent": True},
                )

        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            # UserProfile.is_approved=False 명시 (기본값이 False이지만 가독성)
            from .models import UserProfile
            UserProfile.objects.get_or_create(user=user, defaults={'is_approved': False})
            # 관리자에게 가입 신청 알림 메일 (인증 메일은 승인 후 발송)
            _notify_admin_signup(user, request)
            return render(
                request,
                "accounts/signup_pending.html",
                {"email": user.email, "resent": False},
            )
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})


def verify_email(request, token):
    """이메일 인증 링크 처리: 토큰 검증 → 활성화 → 자동 로그인"""
    try:
        record = EmailVerificationToken.objects.select_related("user").get(token=token)
    except (EmailVerificationToken.DoesNotExist, ValueError):
        return render(request, "accounts/verify_failed.html", {"reason": "invalid"})

    if record.is_expired():
        return render(
            request,
            "accounts/verify_failed.html",
            {"reason": "expired", "username": record.user.username, "email": record.user.email},
        )

    user = record.user
    if user.is_active:
        record.delete()
        return render(request, "accounts/verify_failed.html", {"reason": "already_active"})

    user.is_active = True
    user.save(update_fields=["is_active"])
    record.delete()
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    messages.success(request, "이메일 인증이 완료되었습니다. 환영합니다!")
    return redirect("main:mypage")


def user_login(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.POST.get("next")
            if next_url:
                return redirect(next_url)
            return redirect("main:mypage")
        else:
            # 비활성 계정인지 별도 체크해 안내 메시지 차별화
            username = request.POST.get("username", "").strip()
            inactive = User.objects.filter(username=username, is_active=False).exists()
            if inactive:
                err = "이메일 인증이 완료되지 않은 계정입니다. 가입 시 받은 메일의 인증 링크를 확인해 주세요."
            else:
                err = "아이디 또는 비밀번호가 올바르지 않습니다."
            return render(request, "main/index.html", {"login_error": err})
    return redirect("main:index")


def user_logout(request):
    logout(request)
    return redirect("main:index")


def password_reset_request(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")

        try:
            user = User.objects.get(username=username, email=email)

            length = 8
            chars = string.ascii_letters + string.digits
            new_password = "".join(random.choice(chars) for _ in range(length))

            user.set_password(new_password)
            user.save()

            subject = "[한울회 A+] 비밀번호가 초기화되었습니다."
            message = (
                f"안녕하세요, {user.first_name}님.\n\n"
                f"요청하신 비밀번호 초기화가 완료되었습니다.\n"
                f"--------------------------------\n"
                f"아이디: {user.username}\n"
                f"임시 비밀번호: {new_password}\n"
                f"--------------------------------\n\n"
                f"로그인 후 반드시 비밀번호를 변경해 주세요."
            )

            from django.core.mail import send_mail
            send_mail(
                subject,
                message,
                None,  # settings.DEFAULT_FROM_EMAIL 사용
                [user.email],
                fail_silently=False,
            )

            messages.success(request, "입력하신 이메일로 임시 비밀번호를 전송했습니다.")
            return redirect("main:index")

        except User.DoesNotExist:
            messages.error(request, "일치하는 회원 정보를 찾을 수 없습니다.")
        except User.MultipleObjectsReturned:
            messages.error(request, "동일한 정보의 회원이 여러 명 존재합니다. 관리자에게 문의해 주세요.")

    return render(request, "accounts/password_reset.html")


@login_required
def password_change(request):
    if request.method == "POST":
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if not request.user.check_password(current_password):
            messages.error(request, "현재 비밀번호가 올바르지 않습니다.")
        elif new_password != confirm_password:
            messages.error(request, "새 비밀번호가 일치하지 않습니다.")
        elif len(new_password) < 8:
            messages.error(request, "비밀번호는 8자 이상이어야 합니다.")
        else:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "비밀번호가 변경되었습니다.")
            return redirect("main:mypage")

    return render(request, "accounts/password_change.html")
