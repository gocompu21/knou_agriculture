from collections import OrderedDict

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from django.db.models import Count, Max, Min, Q

from exam.models import Attempt, Question
from .forms import SubjectForm
from .models import Subject


def staff_required(user):
    return user.is_staff


def index(request):
    return render(request, "main/index.html")


@login_required
def subject_list(request):
    subjects = Subject.objects.all()
    grade_labels = {
        1: ("1학년 1학기", "기초 교양 + 전공 입문"),
        2: ("2학년 1학기", "전공 기초"),
        3: ("3학년 1학기", "전공 심화"),
        4: ("4학년 1학기", "실전 대비"),
    }
    grades = OrderedDict()
    for grade_num in range(1, 5):
        label, subtitle = grade_labels.get(grade_num, (f"{grade_num}학년", ""))
        grade_subjects = [s for s in subjects if s.grade == grade_num]
        if grade_subjects:
            grades[grade_num] = {
                "label": label,
                "subtitle": subtitle,
                "subjects": grade_subjects,
            }
    return render(request, "main/subject_list.html", {"grades": grades})


@login_required
def subject_detail(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    years = (
        Question.objects.filter(subject=subject)
        .values_list("year", flat=True)
        .distinct()
        .order_by("-year")
    )
    year_cards = []
    for year in years:
        count = Question.objects.filter(subject=subject, year=year).count()
        year_cards.append({"year": year, "count": count})

    total_questions = Question.objects.filter(subject=subject).count()

    # 오답 수: 문제별 최신 Attempt 중 틀린 것만
    latest_ids = (
        Attempt.objects.filter(
            user=request.user, question__subject=subject
        )
        .values("question")
        .annotate(latest_id=Max("id"))
        .values_list("latest_id", flat=True)
    )
    wrong_count = Attempt.objects.filter(
        pk__in=latest_ids, is_correct=False
    ).count()

    # 시험 이력: session_id별 통계
    sessions_qs = (
        Attempt.objects.filter(
            user=request.user, question__subject=subject
        )
        .exclude(session_id="")
        .exclude(mode="wrong_retry")
        .values("session_id", "mode")
        .annotate(
            total=Count("id"),
            correct_count=Count("id", filter=Q(is_correct=True)),
            wrong_count=Count("id", filter=Q(is_correct=False)),
            date=Max("created_at"),
            year=Min("question__year"),
        )
        .order_by("-date")
    )
    exam_sessions = []
    for s in sessions_qs:
        score = round(s["correct_count"] / s["total"] * 100) if s["total"] else 0
        exam_sessions.append(
            {
                "session_id": s["session_id"],
                "mode": s["mode"],
                "mode_label": "모의고사" if s["mode"] == "mock" else f"{s['year']}년 풀이",
                "total": s["total"],
                "correct": s["correct_count"],
                "wrong": s["wrong_count"],
                "score": score,
                "date": s["date"],
            }
        )

    active_tab = request.GET.get("tab", "study")

    return render(
        request,
        "main/subject_detail.html",
        {
            "subject": subject,
            "year_cards": year_cards,
            "total_questions": total_questions,
            "wrong_count": wrong_count,
            "exam_sessions": exam_sessions,
            "active_tab": active_tab,
        },
    )


@login_required
@user_passes_test(staff_required)
def subject_manage(request):
    subjects = Subject.objects.all()
    return render(request, "main/subject_manage.html", {"subjects": subjects})


@login_required
@user_passes_test(staff_required)
def subject_create(request):
    if request.method == "POST":
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("main:subject_manage")
    else:
        form = SubjectForm()
    return render(request, "main/subject_form.html", {"form": form, "is_edit": False})


@login_required
@user_passes_test(staff_required)
def subject_update(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == "POST":
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            return redirect("main:subject_manage")
    else:
        form = SubjectForm(instance=subject)
    return render(request, "main/subject_form.html", {"form": form, "is_edit": True})


@login_required
@user_passes_test(staff_required)
def subject_delete(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == "POST":
        subject.delete()
        return redirect("main:subject_manage")
    return redirect("main:subject_manage")
