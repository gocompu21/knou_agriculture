import random
import string

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import redirect, render

from .forms import LoginForm, SignUpForm


def user_signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("main:mypage")
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})


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
            return render(request, "main/index.html", {"login_error": "아이디 또는 비밀번호가 올바르지 않습니다."})
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

            send_mail(
                subject,
                message,
                "admin@hanulstudy.kr",
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
