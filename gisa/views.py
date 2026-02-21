import os
import re
import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import Certification, GisaAttempt, GisaExam, GisaQuestion, GisaSubject


## ══════════ 교재 마크다운 파서 ══════════ ##

# 파싱 결과 캐시: {filepath: (mtime, parsed_data)}
_study_guide_cache = {}


def parse_study_guide(filepath):
    """마크다운 핵심정리 파일을 파싱하여 구조화된 데이터 반환 (mtime 기반 캐시)"""
    if not os.path.exists(filepath):
        return []

    mtime = os.path.getmtime(filepath)
    cached = _study_guide_cache.get(filepath)
    if cached and cached[0] == mtime:
        return cached[1]

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    chapters = []
    current_chapter = None
    current_section = None
    current_subsection = None
    content_lines = []

    def _flush_content():
        """축적된 content_lines를 현재 섹션에 저장"""
        nonlocal content_lines
        if not content_lines:
            return
        text = "\n".join(content_lines).strip()
        if not text:
            content_lines = []
            return

        # 관련 문제 추출: (2011-1-5) 또는 2011-1-5 형식 모두 인식
        questions = re.findall(r"(?<!\w)(\d{4}-\d+-\d+)(?!\w)", text)
        # 관련 문제 줄 제거 후 본문만 남김
        body = re.sub(r"\*\*관련 문제\*\*:.*", "", text, flags=re.DOTALL).strip()
        body = re.sub(r"\*\*관련 기출문제\*\*.*", "", body, flags=re.DOTALL).strip()
        # 마크다운 볼드/이탤릭을 HTML로 변환
        body = re.sub(r"\*\*핵심 정리\*\*", "", body)
        # bullet + table을 HTML로
        html_lines = []
        table_rows = []

        def _flush_table():
            nonlocal table_rows
            if not table_rows:
                return
            html_lines.append("<table class='tb-summary'>")
            for idx, row in enumerate(table_rows):
                tag = "th" if idx == 0 else "td"
                cells = [c.strip() for c in row.strip("|").split("|")]
                cells_html = "".join(f"<{tag}>{c}</{tag}>" for c in cells)
                html_lines.append(f"<tr>{cells_html}</tr>")
            html_lines.append("</table>")
            table_rows = []

        for line in body.split("\n"):
            line = line.strip()
            if not line:
                _flush_table()
                continue
            # 마크다운 테이블 행
            if line.startswith("|"):
                # 구분선(|---|---|) 건너뜀
                if re.match(r"^\|[\s\-:|]+\|$", line):
                    continue
                # 볼드 변환
                line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
                line = re.sub(r"\*(.+?)\*", r"<em>\1</em>", line)
                table_rows.append(line)
                continue
            _flush_table()
            if line.startswith("- "):
                line_content = line[2:]
                # 볼드 변환
                line_content = re.sub(
                    r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line_content
                )
                # 이탤릭 변환
                line_content = re.sub(r"\*(.+?)\*", r"<em>\1</em>", line_content)
                html_lines.append(f"<li>{line_content}</li>")
            elif line.startswith("  - "):
                line_content = line[4:]
                line_content = re.sub(
                    r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line_content
                )
                line_content = re.sub(r"\*(.+?)\*", r"<em>\1</em>", line_content)
                html_lines.append(f"<li class='sub-item'>{line_content}</li>")

        _flush_table()
        # bullet이 있으면 <ul>로 감싸고, table만 있으면 그대로
        has_li = any("<li>" in h or "<li " in h for h in html_lines)
        has_table = any("<table" in h for h in html_lines)
        if has_li and not has_table:
            content_html = "<ul>" + "".join(html_lines) + "</ul>"
        elif has_li and has_table:
            # 혼합: li는 ul로 감싸고 table은 별도
            parts = []
            li_buf = []
            for h in html_lines:
                if h.startswith("<li") :
                    li_buf.append(h)
                else:
                    if li_buf:
                        parts.append("<ul>" + "".join(li_buf) + "</ul>")
                        li_buf = []
                    parts.append(h)
            if li_buf:
                parts.append("<ul>" + "".join(li_buf) + "</ul>")
            content_html = "".join(parts)
        else:
            content_html = "".join(html_lines)

        target = current_subsection or current_section
        if target:
            target["content_html"] = content_html
            target["questions"] = questions
        content_lines = []

    for line in content.split("\n"):
        # 장 (## 제N장 또는 ## 부록)
        m = re.match(r"^## (제\d+장\..+|부록.+)", line)
        if m:
            _flush_content()
            current_chapter = {
                "id": f"ch{len(chapters)+1}",
                "title": m.group(1).strip(),
                "sections": [],
            }
            chapters.append(current_chapter)
            current_section = None
            current_subsection = None
            continue

        # 절 (### N.M)
        m = re.match(r"^### (.+)", line)
        if m and current_chapter is not None:
            _flush_content()
            section_title = m.group(1).strip()
            current_section = {
                "id": f"{current_chapter['id']}-s{len(current_chapter['sections'])+1}",
                "title": section_title,
                "content_html": "",
                "questions": [],
                "subsections": [],
            }
            current_chapter["sections"].append(current_section)
            current_subsection = None
            continue

        # 항 (#### N.M.K)
        m = re.match(r"^#### (.+)", line)
        if m and current_section is not None:
            _flush_content()
            sub_title = m.group(1).strip()
            current_subsection = {
                "id": f"{current_section['id']}-sub{len(current_section['subsections'])+1}",
                "title": sub_title,
                "content_html": "",
                "questions": [],
            }
            current_section["subsections"].append(current_subsection)
            continue

        # 일반 내용 줄
        if line.startswith("# ") or line.startswith("---") or line.startswith("> "):
            continue
        content_lines.append(line)

    _flush_content()

    # 각 section에 total_questions (자체 + subsection 합산, 중복 제거) 계산
    for ch in chapters:
        for sec in ch["sections"]:
            seen = set()
            unique_q = []
            for q in sec["questions"]:
                if q not in seen:
                    seen.add(q)
                    unique_q.append(q)
            for sub in sec["subsections"]:
                for q in sub["questions"]:
                    if q not in seen:
                        seen.add(q)
                        unique_q.append(q)
            sec["total_questions"] = len(unique_q)
            sec["all_questions"] = unique_q

    _study_guide_cache[filepath] = (mtime, chapters)
    return chapters


def build_results(attempts):
    """GisaAttempt 쿼리셋을 템플릿용 results 리스트로 변환"""
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
                    "user_correct": str(i) == a.selected and str(i) in correct_answers,
                    "user_wrong": str(i) == a.selected and str(i) not in correct_answers,
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


## ══════════ 자격증 목록/상세 ══════════ ##


@login_required
def certification_list(request):
    certifications = Certification.objects.annotate(
        exam_count=Count("gisaexam", distinct=True),
        question_count=Count("gisaexam__gisaquestion", distinct=True),
    )
    return render(
        request,
        "gisa/certification_list.html",
        {"certifications": certifications},
    )


@login_required
def certification_detail(request, cert_id):
    cert = get_object_or_404(Certification, pk=cert_id)
    exams = GisaExam.objects.filter(certification=cert)
    subjects = GisaSubject.objects.filter(certification=cert)

    active_tab = request.GET.get("tab", "textbook")
    total_questions = GisaQuestion.objects.filter(exam__certification=cert).count()

    # 교재 탭이 아닐 때만 시험/세션 데이터 로드 (switchTab은 페이지 리로드)
    exam_cards = []
    wrong_count = 0
    exam_sessions = []

    # 탭별 필요한 데이터만 로드 (switchTab은 페이지 리로드)
    if active_tab in ("study", "solve"):
        exam_cards = [
            {"exam": e, "count": e.q_count}
            for e in exams.annotate(q_count=Count("gisaquestion")).order_by("-year", "-round")
        ]

    if active_tab == "wrong" and request.user.is_authenticated:
        latest_ids = (
            GisaAttempt.objects.filter(
                user=request.user,
                question__exam__certification=cert,
            )
            .values("question")
            .annotate(latest_id=Max("id"))
            .values_list("latest_id", flat=True)
        )
        wrong_count = GisaAttempt.objects.filter(
            pk__in=latest_ids, is_correct=False
        ).count()

    if active_tab == "history" and request.user.is_authenticated:
        session_ids = (
            GisaAttempt.objects.filter(
                user=request.user,
                question__exam__certification=cert,
            )
            .exclude(session_id="")
            .values_list("session_id", flat=True)
            .distinct()
        )
        for sid in session_ids:
            s_attempts = GisaAttempt.objects.filter(
                user=request.user, session_id=sid
            )
            if not s_attempts.exists():
                continue
            first = s_attempts.order_by("created_at").first()
            total = s_attempts.count()
            correct = s_attempts.filter(is_correct=True).count()
            wrong = total - correct
            score = round(correct / total * 100) if total else 0
            mode = first.mode
            mode_labels = {"exam": "풀이", "mock": "모의고사", "wrong_retry": "오답재풀이"}
            exam_sessions.append(
                {
                    "session_id": sid,
                    "mode": mode,
                    "mode_label": mode_labels.get(mode, mode),
                    "total": total,
                    "correct": correct,
                    "wrong": wrong,
                    "score": score,
                    "date": first.created_at,
                }
            )
        exam_sessions.sort(key=lambda s: s["date"], reverse=True)

    # 교재 데이터 — 교재 탭일 때만 장 제목 전달 (섹션은 AJAX로 로드)
    textbook_chapters = []
    textbook_subject = request.GET.get("subject", "식물병리학")
    textbook_subjects = list(subjects.values_list("name", flat=True))
    if active_tab == "textbook":
        guide_path = os.path.join(
            settings.BASE_DIR, "data", f"{textbook_subject}_핵심정리.md"
        )
        if os.path.exists(guide_path):
            full = parse_study_guide(guide_path)  # mtime 캐시 히트
            textbook_chapters = [
                {"id": ch["id"], "title": ch["title"]} for ch in full
            ]

    return render(
        request,
        "gisa/certification_detail.html",
        {
            "cert": cert,
            "exams": exams,
            "subjects": subjects,
            "exam_cards": exam_cards,
            "wrong_count": wrong_count,
            "exam_sessions": exam_sessions,
            "active_tab": active_tab,
            "total_questions": total_questions,
            "textbook_chapters": textbook_chapters,
            "textbook_subject": textbook_subject,
            "textbook_subjects": textbook_subjects,
        },
    )


## ══════════ 교재 AJAX API ══════════ ##


@login_required
def textbook_chapter_api(request, cert_id):
    """AJAX: 특정 장의 섹션 HTML을 JSON으로 반환"""
    cert = get_object_or_404(Certification, pk=cert_id)
    subject = request.GET.get("subject", "식물병리학")
    ch_idx = int(request.GET.get("ch", 0))

    guide_path = os.path.join(
        settings.BASE_DIR, "data", f"{subject}_핵심정리.md"
    )
    chapters = parse_study_guide(guide_path)  # mtime 캐시 히트

    if ch_idx < 0 or ch_idx >= len(chapters):
        return JsonResponse({"html": ""})

    chapter = chapters[ch_idx]
    html = render_to_string(
        "gisa/_chapter_body.html", {"ch": chapter, "cert": cert}, request=request
    )
    return JsonResponse({"html": html})


## ══════════ 학습모드 ══════════ ##


@login_required
def study_mode(request, cert_id, exam_id, subject_id):
    cert = get_object_or_404(Certification, pk=cert_id)
    exam = get_object_or_404(GisaExam, pk=exam_id, certification=cert)
    subject = get_object_or_404(GisaSubject, pk=subject_id, certification=cert)
    questions = GisaQuestion.objects.filter(
        exam=exam, subject=subject
    ).order_by("number")

    if not questions.exists():
        return redirect("gisa:certification_detail", cert_id=cert_id)

    return render(
        request,
        "gisa/study_mode.html",
        {
            "cert": cert,
            "exam": exam,
            "subject": subject,
            "questions": questions,
        },
    )


## ══════════ 풀이모드 ══════════ ##


@login_required
def exam_take(request, cert_id, exam_id):
    cert = get_object_or_404(Certification, pk=cert_id)
    exam = get_object_or_404(GisaExam, pk=exam_id, certification=cert)
    questions = GisaQuestion.objects.filter(exam=exam).order_by("number")
    subjects = GisaSubject.objects.filter(certification=cert)

    if not questions.exists():
        return redirect("gisa:certification_detail", cert_id=cert_id)

    return render(
        request,
        "gisa/exam_take.html",
        {
            "cert": cert,
            "exam": exam,
            "questions": questions,
            "subjects": subjects,
        },
    )


@login_required
@require_POST
def exam_submit(request, cert_id, exam_id):
    cert = get_object_or_404(Certification, pk=cert_id)
    exam = get_object_or_404(GisaExam, pk=exam_id, certification=cert)
    questions = GisaQuestion.objects.filter(exam=exam).order_by("number")

    session_id = str(uuid.uuid4())
    attempt_ids = []
    for q in questions:
        selected = request.POST.get(f"question_{q.id}", "")
        if not selected:
            selected = "0"
        correct_answers = q.answer.split(",")
        is_correct = selected in correct_answers and selected != "0"
        attempt = GisaAttempt.objects.create(
            user=request.user,
            question=q,
            selected=selected,
            is_correct=is_correct,
            mode="exam",
            session_id=session_id,
        )
        attempt_ids.append(attempt.pk)

    request.session["gisa_last_attempt_ids"] = attempt_ids
    return redirect("gisa:exam_result", cert_id=cert_id, exam_id=exam_id)


@login_required
def exam_result(request, cert_id, exam_id):
    cert = get_object_or_404(Certification, pk=cert_id)
    exam = get_object_or_404(GisaExam, pk=exam_id, certification=cert)
    attempt_ids = request.session.get("gisa_last_attempt_ids", [])

    if attempt_ids:
        attempts = (
            GisaAttempt.objects.filter(pk__in=attempt_ids)
            .select_related("question", "question__subject")
            .order_by("question__number")
        )
    else:
        latest = (
            GisaAttempt.objects.filter(
                user=request.user, question__exam=exam
            )
            .order_by("-created_at")
            .first()
        )
        if latest:
            attempts = (
                GisaAttempt.objects.filter(
                    user=request.user,
                    question__exam=exam,
                    session_id=latest.session_id,
                )
                .select_related("question", "question__subject")
                .order_by("question__number")
            )
        else:
            attempts = GisaAttempt.objects.none()

    total = attempts.count()
    correct = attempts.filter(is_correct=True).count()
    score = round(correct / total * 100) if total else 0
    results = build_results(attempts)

    # 과목별 점수 계산
    subject_scores = {}
    for a in attempts:
        subj_name = a.question.subject.name
        if subj_name not in subject_scores:
            subject_scores[subj_name] = {"total": 0, "correct": 0}
        subject_scores[subj_name]["total"] += 1
        if a.is_correct:
            subject_scores[subj_name]["correct"] += 1

    for v in subject_scores.values():
        v["score"] = round(v["correct"] / v["total"] * 100) if v["total"] else 0

    return render(
        request,
        "gisa/exam_result.html",
        {
            "cert": cert,
            "exam": exam,
            "results": results,
            "total": total,
            "correct": correct,
            "score": score,
            "subject_scores": subject_scores,
        },
    )


## ══════════ 모의고사 ══════════ ##


@login_required
def mock_exam_take(request, cert_id):
    cert = get_object_or_404(Certification, pk=cert_id)
    subjects = GisaSubject.objects.filter(certification=cert).order_by("order")

    # 과목별 20문제씩 랜덤 추출
    questions = []
    for subject in subjects:
        qs = list(
            GisaQuestion.objects.filter(
                exam__certification=cert, subject=subject
            ).order_by("?")[:20]
        )
        questions.extend(qs)

    if not questions:
        return redirect("gisa:certification_detail", cert_id=cert_id)

    # 과목순서 → 문제번호 정렬
    questions.sort(key=lambda q: (q.subject.order, q.number))

    session_id = str(uuid.uuid4())
    request.session[f"gisa_mock_{session_id}"] = [q.pk for q in questions]

    return render(
        request,
        "gisa/mock_exam_take.html",
        {
            "cert": cert,
            "questions": questions,
            "session_id": session_id,
            "subjects": subjects,
        },
    )


@login_required
@require_POST
def mock_exam_submit(request, cert_id):
    cert = get_object_or_404(Certification, pk=cert_id)
    session_id = request.POST.get("session_id", "")
    question_ids = request.session.get(f"gisa_mock_{session_id}", [])

    if not question_ids:
        return redirect("gisa:certification_detail", cert_id=cert_id)

    q_map = {q.pk: q for q in GisaQuestion.objects.filter(pk__in=question_ids)}
    ordered_questions = [q_map[pk] for pk in question_ids if pk in q_map]

    attempt_ids = []
    for q in ordered_questions:
        selected = request.POST.get(f"question_{q.id}", "0") or "0"
        correct_answers = q.answer.split(",")
        is_correct = selected in correct_answers and selected != "0"
        attempt = GisaAttempt.objects.create(
            user=request.user,
            question=q,
            selected=selected,
            is_correct=is_correct,
            mode="mock",
            session_id=session_id,
        )
        attempt_ids.append(attempt.pk)

    request.session.pop(f"gisa_mock_{session_id}", None)
    request.session["gisa_last_attempt_ids"] = attempt_ids
    return redirect(
        "gisa:mock_exam_result",
        cert_id=cert_id,
        session_id=session_id,
    )


@login_required
def mock_exam_result(request, cert_id, session_id):
    cert = get_object_or_404(Certification, pk=cert_id)
    attempt_ids = request.session.get("gisa_last_attempt_ids", [])

    if attempt_ids:
        attempts = (
            GisaAttempt.objects.filter(pk__in=attempt_ids)
            .select_related("question", "question__subject", "question__exam")
            .order_by("question__subject__order", "question__number")
        )
    else:
        attempts = (
            GisaAttempt.objects.filter(
                user=request.user, session_id=session_id, mode="mock"
            )
            .select_related("question", "question__subject", "question__exam")
            .order_by("question__subject__order", "question__number")
        )

    total = attempts.count()
    correct = attempts.filter(is_correct=True).count()
    score = round(correct / total * 100) if total else 0
    results = build_results(attempts)

    return render(
        request,
        "gisa/exam_result.html",
        {
            "cert": cert,
            "exam": None,
            "results": results,
            "total": total,
            "correct": correct,
            "score": score,
            "is_mock": True,
            "session_id": session_id,
        },
    )


## ══════════ 오답노트 ══════════ ##


def _get_wrong_question_ids(user, cert):
    """사용자의 최신 GisaAttempt 중 오답인 문제 ID 리스트 반환"""
    latest_ids = (
        GisaAttempt.objects.filter(
            user=user, question__exam__certification=cert
        )
        .values("question")
        .annotate(latest_id=Max("id"))
        .values_list("latest_id", flat=True)
    )
    return list(
        GisaAttempt.objects.filter(pk__in=latest_ids, is_correct=False)
        .values_list("question_id", flat=True)
    )


@login_required
def wrong_answers(request, cert_id):
    cert = get_object_or_404(Certification, pk=cert_id)
    wrong_qids = _get_wrong_question_ids(request.user, cert)

    latest_ids = (
        GisaAttempt.objects.filter(
            user=request.user, question__exam__certification=cert
        )
        .values("question")
        .annotate(latest_id=Max("id"))
        .values_list("latest_id", flat=True)
    )
    wrong_attempts = (
        GisaAttempt.objects.filter(pk__in=latest_ids, is_correct=False)
        .select_related("question", "question__subject", "question__exam")
        .order_by("question__subject__order", "question__number")
    )
    results = build_results(wrong_attempts)

    return render(
        request,
        "gisa/wrong_answers.html",
        {
            "cert": cert,
            "results": results,
            "total_wrong": len(wrong_qids),
        },
    )


@login_required
def wrong_answers_session(request, cert_id, session_id):
    cert = get_object_or_404(Certification, pk=cert_id)
    wrong_attempts = (
        GisaAttempt.objects.filter(
            user=request.user,
            session_id=session_id,
            is_correct=False,
        )
        .select_related("question", "question__subject", "question__exam")
        .order_by("question__number")
    )

    results = build_results(wrong_attempts)
    total_in_session = GisaAttempt.objects.filter(
        user=request.user, session_id=session_id
    ).count()
    mode = wrong_attempts.first().mode if wrong_attempts.exists() else "exam"

    return render(
        request,
        "gisa/wrong_answers.html",
        {
            "cert": cert,
            "results": results,
            "total_wrong": wrong_attempts.count(),
            "total_in_session": total_in_session,
            "session_id": session_id,
            "is_session": True,
            "mode": mode,
        },
    )


@login_required
def wrong_answers_retry(request, cert_id):
    cert = get_object_or_404(Certification, pk=cert_id)
    wrong_qids = _get_wrong_question_ids(request.user, cert)

    questions = list(
        GisaQuestion.objects.filter(pk__in=wrong_qids)
        .select_related("subject", "exam")
        .order_by("subject__order", "number")
    )

    if not questions:
        return redirect("gisa:certification_detail", cert_id=cert_id)

    session_id = str(uuid.uuid4())
    request.session[f"gisa_wrong_{session_id}"] = [q.pk for q in questions]

    return render(
        request,
        "gisa/study_mode.html",
        {
            "cert": cert,
            "exam": None,
            "subject": None,
            "questions": questions,
            "is_wrong_retry": True,
            "session_id": session_id,
        },
    )


@login_required
@require_POST
def wrong_answers_submit(request, cert_id):
    cert = get_object_or_404(Certification, pk=cert_id)
    session_id = request.POST.get("session_id", "")
    question_ids = request.session.get(f"gisa_wrong_{session_id}", [])

    if not question_ids:
        return redirect("gisa:certification_detail", cert_id=cert_id)

    q_map = {q.pk: q for q in GisaQuestion.objects.filter(pk__in=question_ids)}
    ordered_questions = [q_map[pk] for pk in question_ids if pk in q_map]

    attempt_ids = []
    for q in ordered_questions:
        selected = request.POST.get(f"question_{q.id}", "0") or "0"
        correct_answers = q.answer.split(",")
        is_correct = selected in correct_answers and selected != "0"
        attempt = GisaAttempt.objects.create(
            user=request.user,
            question=q,
            selected=selected,
            is_correct=is_correct,
            mode="wrong_retry",
            session_id=session_id,
        )
        attempt_ids.append(attempt.pk)

    request.session.pop(f"gisa_wrong_{session_id}", None)
    request.session["gisa_last_attempt_ids"] = attempt_ids
    return redirect(
        "gisa:wrong_answers_result",
        cert_id=cert_id,
        session_id=session_id,
    )


@login_required
def wrong_answers_result(request, cert_id, session_id):
    cert = get_object_or_404(Certification, pk=cert_id)
    attempt_ids = request.session.get("gisa_last_attempt_ids", [])

    if attempt_ids:
        attempts = (
            GisaAttempt.objects.filter(pk__in=attempt_ids)
            .select_related("question", "question__subject")
            .order_by("question__number")
        )
    else:
        attempts = (
            GisaAttempt.objects.filter(user=request.user, session_id=session_id)
            .select_related("question", "question__subject")
            .order_by("question__number")
        )

    total = attempts.count()
    correct = attempts.filter(is_correct=True).count()
    score = round(correct / total * 100) if total else 0
    results = build_results(attempts)

    return render(
        request,
        "gisa/exam_result.html",
        {
            "cert": cert,
            "exam": None,
            "results": results,
            "total": total,
            "correct": correct,
            "score": score,
            "is_wrong_retry": True,
        },
    )


@login_required
@require_POST
def wrong_dismiss(request, cert_id, question_id):
    cert = get_object_or_404(Certification, pk=cert_id)
    question = get_object_or_404(
        GisaQuestion, pk=question_id, exam__certification=cert
    )
    GisaAttempt.objects.create(
        user=request.user,
        question=question,
        selected=question.answer.split(",")[0],
        is_correct=True,
        mode="wrong_retry",
    )
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True})
    referer = request.META.get("HTTP_REFERER", "")
    if referer:
        return redirect(referer)
    return redirect("gisa:wrong_answers", cert_id=cert_id)


@login_required
@require_POST
def session_delete(request, cert_id, session_id):
    GisaAttempt.objects.filter(
        user=request.user,
        session_id=session_id,
        question__exam__certification_id=cert_id,
    ).delete()
    return redirect(
        f"{reverse('gisa:certification_detail', args=[cert_id])}?tab=wrong"
    )


@login_required
@require_POST
def session_delete_all(request, cert_id):
    GisaAttempt.objects.filter(
        user=request.user,
        question__exam__certification_id=cert_id,
    ).delete()
    return redirect(
        f"{reverse('gisa:certification_detail', args=[cert_id])}?tab=wrong"
    )


## ══════════ 교재 학습 ══════════ ##


@login_required
def textbook_study(request, cert_id):
    """교재 관련 문제 학습모드 - question refs로 문제 조회"""
    cert = get_object_or_404(Certification, pk=cert_id)
    refs = request.GET.getlist("ref")
    if not refs and request.method == "POST":
        refs = request.POST.getlist("ref")

    if not refs:
        return redirect("gisa:certification_detail", cert_id=cert_id)

    # refs: ["2011-1-5", "2012-2-2", ...] → year, round, number로 매핑
    q_filters = Q()
    for ref in refs:
        parts = ref.split("-")
        if len(parts) == 3:
            year, round_num, number = parts
            q_filters |= Q(
                exam__year=int(year),
                exam__round=int(round_num),
                number=int(number),
                exam__certification=cert,
            )

    if not q_filters:
        return redirect("gisa:certification_detail", cert_id=cert_id)

    questions = list(
        GisaQuestion.objects.filter(q_filters)
        .select_related("subject", "exam")
        .order_by("exam__year", "exam__round", "number")
    )

    section_title = request.GET.get("title", request.POST.get("title", "교재 학습"))

    return render(
        request,
        "gisa/study_mode.html",
        {
            "cert": cert,
            "exam": None,
            "subject": None,
            "questions": questions,
            "is_textbook_study": True,
            "section_title": section_title,
        },
    )
