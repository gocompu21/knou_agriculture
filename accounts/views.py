from django.contrib.auth import login, logout
from django.shortcuts import redirect, render

from .forms import LoginForm, SignUpForm


def user_signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("main:index")
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
            return redirect("main:index")
        else:
            return render(request, "main/index.html", {"login_error": "아이디 또는 비밀번호가 올바르지 않습니다."})
    return redirect("main:index")


def user_logout(request):
    logout(request)
    return redirect("main:index")
