import uuid

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from main.models import Subject

from .forms import ExamForm
from .models import Attempt, Exam, Question


def staff_required(user):
    return user.is_staff


def build_results(attempts):
    """Attempt 쿼리셋을 템플릿용 results 리스트로 변환"""
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
    return results


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

    session_id = str(uuid.uuid4())
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
            mode="exam",
            session_id=session_id,
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
    results = build_results(attempts)

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


## ══════════ 모의고사 ══════════ ##


@login_required
def mock_exam_take(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id)
    all_questions = Question.objects.filter(subject=subject, year__lt=2020)

    count = min(25, all_questions.count())
    if count == 0:
        return redirect("main:subject_detail", pk=subject_id)

    questions = list(all_questions.order_by("?")[:count])
    questions.sort(key=lambda q: (q.year, q.number))

    session_id = str(uuid.uuid4())
    request.session[f"mock_{session_id}"] = [q.pk for q in questions]

    return render(
        request,
        "exam/mock_exam_take.html",
        {"subject": subject, "questions": questions, "session_id": session_id},
    )


@login_required
@require_POST
def mock_exam_submit(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id)
    session_id = request.POST.get("session_id", "")
    question_ids = request.session.get(f"mock_{session_id}", [])

    if not question_ids:
        return redirect("main:subject_detail", pk=subject_id)

    q_map = {q.pk: q for q in Question.objects.filter(pk__in=question_ids)}
    ordered_questions = [q_map[pk] for pk in question_ids if pk in q_map]

    attempt_ids = []
    for q in ordered_questions:
        selected = request.POST.get(f"question_{q.id}", "0") or "0"
        correct_answers = q.answer.split(",")
        is_correct = selected in correct_answers and selected != "0"
        attempt = Attempt.objects.create(
            user=request.user,
            question=q,
            selected=selected,
            is_correct=is_correct,
            mode="mock",
            session_id=session_id,
        )
        attempt_ids.append(attempt.pk)

    request.session.pop(f"mock_{session_id}", None)
    request.session["last_attempt_ids"] = attempt_ids
    return redirect(
        "exam:mock_exam_result",
        subject_id=subject_id,
        session_id=session_id,
    )


@login_required
def mock_exam_result(request, subject_id, session_id):
    subject = get_object_or_404(Subject, pk=subject_id)
    attempt_ids = request.session.get("last_attempt_ids", [])

    if attempt_ids:
        attempts = (
            Attempt.objects.filter(pk__in=attempt_ids)
            .select_related("question")
            .order_by("question__year", "question__number")
        )
    else:
        attempts = (
            Attempt.objects.filter(
                user=request.user, session_id=session_id, mode="mock"
            )
            .select_related("question")
            .order_by("question__year", "question__number")
        )

    total = attempts.count()
    correct = attempts.filter(is_correct=True).count()
    score = round(correct / total * 100) if total else 0
    results = build_results(attempts)

    return render(
        request,
        "exam/exam_result.html",
        {
            "subject": subject,
            "year": "모의고사",
            "results": results,
            "total": total,
            "correct": correct,
            "score": score,
            "is_mock": True,
            "session_id": session_id,
        },
    )


## ══════════ 오답노트 ══════════ ##


def _get_wrong_question_ids(user, subject):
    """사용자의 최신 Attempt 중 오답인 문제 ID 리스트 반환"""
    latest_ids = (
        Attempt.objects.filter(user=user, question__subject=subject)
        .values("question")
        .annotate(latest_id=Max("id"))
        .values_list("latest_id", flat=True)
    )
    return list(
        Attempt.objects.filter(pk__in=latest_ids, is_correct=False)
        .values_list("question_id", flat=True)
    )


@login_required
def wrong_answers(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id)
    wrong_qids = _get_wrong_question_ids(request.user, subject)

    # 최신 오답 Attempt를 가져와서 build_results로 가공
    latest_ids = (
        Attempt.objects.filter(
            user=request.user, question__subject=subject
        )
        .values("question")
        .annotate(latest_id=Max("id"))
        .values_list("latest_id", flat=True)
    )
    wrong_attempts = (
        Attempt.objects.filter(pk__in=latest_ids, is_correct=False)
        .select_related("question")
        .order_by("question__year", "question__number")
    )
    results = build_results(wrong_attempts)

    return render(
        request,
        "exam/wrong_answers.html",
        {
            "subject": subject,
            "results": results,
            "total_wrong": len(wrong_qids),
        },
    )


@login_required
def wrong_answers_session(request, subject_id, session_id):
    """특정 시험 세션의 오답만 표시"""
    subject = get_object_or_404(Subject, pk=subject_id)
    wrong_attempts = (
        Attempt.objects.filter(
            user=request.user,
            session_id=session_id,
            is_correct=False,
        )
        .select_related("question")
        .order_by("question__year", "question__number")
    )

    results = build_results(wrong_attempts)
    total_in_session = Attempt.objects.filter(
        user=request.user, session_id=session_id
    ).count()
    mode = wrong_attempts.first().mode if wrong_attempts.exists() else "exam"

    return render(
        request,
        "exam/wrong_answers.html",
        {
            "subject": subject,
            "results": results,
            "total_wrong": wrong_attempts.count(),
            "total_in_session": total_in_session,
            "session_id": session_id,
            "is_session": True,
            "mode": mode,
        },
    )


@login_required
def wrong_answers_retry(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id)
    wrong_qids = _get_wrong_question_ids(request.user, subject)

    questions = list(
        Question.objects.filter(pk__in=wrong_qids).order_by("year", "number")
    )

    if not questions:
        return redirect("main:subject_detail", pk=subject_id)

    return render(
        request,
        "exam/study_mode.html",
        {
            "subject": subject,
            "questions": questions,
            "year": "오답 재풀이",
            "is_wrong_retry": True,
        },
    )


@login_required
@require_POST
def wrong_answers_submit(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id)
    session_id = request.POST.get("session_id", "")
    question_ids = request.session.get(f"wrong_{session_id}", [])

    if not question_ids:
        return redirect("main:subject_detail", pk=subject_id)

    q_map = {q.pk: q for q in Question.objects.filter(pk__in=question_ids)}
    ordered_questions = [q_map[pk] for pk in question_ids if pk in q_map]

    attempt_ids = []
    for q in ordered_questions:
        selected = request.POST.get(f"question_{q.id}", "0") or "0"
        correct_answers = q.answer.split(",")
        is_correct = selected in correct_answers and selected != "0"
        attempt = Attempt.objects.create(
            user=request.user,
            question=q,
            selected=selected,
            is_correct=is_correct,
            mode="wrong_retry",
            session_id=session_id,
        )
        attempt_ids.append(attempt.pk)

    request.session.pop(f"wrong_{session_id}", None)
    request.session["last_attempt_ids"] = attempt_ids
    return redirect(
        "exam:wrong_answers_result",
        subject_id=subject_id,
        session_id=session_id,
    )


@login_required
def wrong_answers_result(request, subject_id, session_id):
    subject = get_object_or_404(Subject, pk=subject_id)
    attempt_ids = request.session.get("last_attempt_ids", [])

    if attempt_ids:
        attempts = (
            Attempt.objects.filter(pk__in=attempt_ids)
            .select_related("question")
            .order_by("question__year", "question__number")
        )
    else:
        attempts = (
            Attempt.objects.filter(user=request.user, session_id=session_id)
            .select_related("question")
            .order_by("question__year", "question__number")
        )

    total = attempts.count()
    correct = attempts.filter(is_correct=True).count()
    score = round(correct / total * 100) if total else 0
    results = build_results(attempts)

    return render(
        request,
        "exam/exam_result.html",
        {
            "subject": subject,
            "year": "오답 재풀이",
            "results": results,
            "total": total,
            "correct": correct,
            "score": score,
            "is_wrong_retry": True,
        },
    )


@login_required
@require_POST
def wrong_dismiss(request, subject_id, question_id):
    question = get_object_or_404(Question, pk=question_id, subject_id=subject_id)
    Attempt.objects.create(
        user=request.user,
        question=question,
        selected=question.answer.split(",")[0],
        is_correct=True,
        mode="wrong_retry",
    )
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.content_type == "":
        return JsonResponse({"ok": True})
    referer = request.META.get("HTTP_REFERER", "")
    if referer:
        return redirect(referer)
    return redirect("exam:wrong_answers", subject_id=subject_id)


@login_required
@require_POST
def session_delete(request, subject_id, session_id):
    Attempt.objects.filter(
        user=request.user, session_id=session_id, question__subject_id=subject_id
    ).delete()
    return redirect(f"{reverse('main:subject_detail', args=[subject_id])}?tab=wrong")


@login_required
@require_POST
def session_delete_all(request, subject_id):
    Attempt.objects.filter(
        user=request.user, question__subject_id=subject_id
    ).delete()
    return redirect(f"{reverse('main:subject_detail', args=[subject_id])}?tab=wrong")


## ══════════ 관리자 ══════════ ##


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
