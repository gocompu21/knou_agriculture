from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from main.models import Subject

from .forms import ExamForm
from .models import Attempt, Exam, Question


def staff_required(user):
    return user.is_staff


@login_required
def study_mode(request, subject_id, year):
    subject = get_object_or_404(Subject, pk=subject_id)
    questions = Question.objects.filter(
        subject=subject, year=year
    ).order_by("number")
    if not questions.exists():
        return redirect("main:subject_detail", pk=subject_id)
    return render(
        request,
        "exam/study_mode.html",
        {"subject": subject, "year": year, "questions": questions},
    )


@login_required
def exam_take(request, subject_id, year):
    subject = get_object_or_404(Subject, pk=subject_id)
    questions = Question.objects.filter(
        subject=subject, year=year
    ).order_by("number")
    if not questions.exists():
        return redirect("main:subject_detail", pk=subject_id)
    return render(
        request,
        "exam/exam_take.html",
        {"subject": subject, "year": year, "questions": questions},
    )


@login_required
@require_POST
def exam_submit(request, subject_id, year):
    subject = get_object_or_404(Subject, pk=subject_id)
    questions = Question.objects.filter(
        subject=subject, year=year
    ).order_by("number")

    attempt_ids = []
    for q in questions:
        selected = request.POST.get(f"question_{q.id}", "")
        if not selected:
            selected = "0"
        correct_answers = q.answer.split(",")
        is_correct = selected in correct_answers and selected != "0"
        attempt = Attempt.objects.create(
            user=request.user,
            question=q,
            selected=selected,
            is_correct=is_correct,
        )
        attempt_ids.append(attempt.pk)

    request.session["last_attempt_ids"] = attempt_ids
    return redirect("exam:exam_result", subject_id=subject_id, year=year)


@login_required
def exam_result(request, subject_id, year):
    subject = get_object_or_404(Subject, pk=subject_id)
    attempt_ids = request.session.get("last_attempt_ids", [])

    if attempt_ids:
        attempts = Attempt.objects.filter(
            pk__in=attempt_ids
        ).select_related("question").order_by("question__number")
    else:
        # fallback: 해당 과목/연도의 가장 최근 풀이
        latest = (
            Attempt.objects.filter(
                user=request.user, question__subject=subject, question__year=year
            )
            .order_by("-created_at")
            .first()
        )
        if latest:
            attempts = Attempt.objects.filter(
                user=request.user,
                question__subject=subject,
                question__year=year,
                created_at__gte=latest.created_at.replace(microsecond=0),
            ).select_related("question").order_by("question__number")
        else:
            attempts = Attempt.objects.none()

    total = attempts.count()
    correct = attempts.filter(is_correct=True).count()
    score = round(correct / total * 100) if total else 0

    # 템플릿에서 사용할 수 있도록 가공
    results = []
    for a in attempts:
        q = a.question
        correct_answers = q.answer.split(",")
        choices = []
        for i, (text, exp) in enumerate(
            [
                (q.choice_1, q.choice_1_exp),
                (q.choice_2, q.choice_2_exp),
                (q.choice_3, q.choice_3_exp),
                (q.choice_4, q.choice_4_exp),
            ],
            start=1,
        ):
            choices.append(
                {
                    "num": i,
                    "text": text,
                    "exp": exp,
                    "is_correct": str(i) in correct_answers,
                    "is_selected": str(i) == a.selected,
                    "user_correct": str(i) == a.selected
                    and str(i) in correct_answers,
                    "user_wrong": str(i) == a.selected
                    and str(i) not in correct_answers,
                }
            )
        results.append(
            {
                "attempt": a,
                "question": q,
                "choices": choices,
                "is_correct": a.is_correct,
                "skipped": a.selected == "0",
            }
        )

    return render(
        request,
        "exam/exam_result.html",
        {
            "subject": subject,
            "year": year,
            "results": results,
            "total": total,
            "correct": correct,
            "score": score,
        },
    )


@login_required
@user_passes_test(staff_required)
def exam_manage(request):
    exams = Exam.objects.all()
    return render(request, "exam/exam_manage.html", {"exams": exams})


@login_required
@user_passes_test(staff_required)
def exam_create(request):
    if request.method == "POST":
        form = ExamForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("exam:exam_manage")
    else:
        form = ExamForm()
    return render(request, "exam/exam_form.html", {"form": form, "is_edit": False})


@login_required
@user_passes_test(staff_required)
def exam_update(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    if request.method == "POST":
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            return redirect("exam:exam_manage")
    else:
        form = ExamForm(instance=exam)
    return render(request, "exam/exam_form.html", {"form": form, "is_edit": True})


@login_required
@user_passes_test(staff_required)
def exam_delete(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    if request.method == "POST":
        exam.delete()
        return redirect("exam:exam_manage")
    return redirect("exam:exam_manage")


@login_required
@user_passes_test(staff_required)
def question_manage(request):
    subjects = Subject.objects.all()
    selected_subject = None
    exams = []
    selected_exam = None
    questions = []

    subject_id = request.GET.get("subject")
    exam_id = request.GET.get("exam")

    if subject_id:
        selected_subject = get_object_or_404(Subject, pk=subject_id)
        # 해당 교과목에 문제가 존재하는 연도 추출 → 매칭되는 Exam 조회
        years = (
            Question.objects.filter(subject=selected_subject)
            .values_list("year", flat=True)
            .distinct()
        )
        exams = Exam.objects.filter(year__in=years).order_by("-year", "exam_type")

    if exam_id and selected_subject:
        selected_exam = get_object_or_404(Exam, pk=exam_id)
        questions = Question.objects.filter(
            subject=selected_subject, year=selected_exam.year
        ).order_by("number")

    return render(
        request,
        "exam/question_manage.html",
        {
            "subjects": subjects,
            "selected_subject": selected_subject,
            "exams": exams,
            "selected_exam": selected_exam,
            "questions": questions,
        },
    )


@login_required
@user_passes_test(staff_required)
def question_delete(request, pk):
    question = get_object_or_404(Question, pk=pk)
    subject_id = question.subject_id
    # exam_id 찾기: 같은 year의 Exam
    exam = Exam.objects.filter(year=question.year).first()
    if request.method == "POST":
        question.delete()
    redirect_url = f"?subject={subject_id}"
    if exam:
        redirect_url += f"&exam={exam.pk}"
    return redirect(f"/exam/manage/questions/{redirect_url}")
