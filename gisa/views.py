import os
import re
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Case, Count, IntegerField, Max, Min, Q, Value, When
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import Certification, GisaAttempt, GisaExam, GisaQuestion, GisaSubject, GisaTextbook


## ══════════ 교재 마크다운 파서 ══════════ ##

# 파싱 결과 캐시: {cache_key: (version, parsed_data)}
_study_guide_cache = {}


def parse_study_guide(filepath_or_content, cache_key=None, cache_version=None):
    """마크다운 핵심정리를 파싱하여 구조화된 데이터 반환.
    filepath_or_content: 파일 경로 또는 마크다운 문자열.
    cache_key/cache_version: DB 기반 캐시용 (key=subject_id, version=updated_at).
    """
    # 파일 경로인 경우 (하위 호환)
    if os.path.exists(filepath_or_content):
        mtime = os.path.getmtime(filepath_or_content)
        cached = _study_guide_cache.get(filepath_or_content)
        if cached and cached[0] == mtime:
            return cached[1]
        with open(filepath_or_content, "r", encoding="utf-8") as f:
            content = f.read()
        effective_key = filepath_or_content
        effective_version = mtime
    else:
        content = filepath_or_content
        effective_key = cache_key or id(content)
        effective_version = cache_version
        if effective_version is not None:
            cached = _study_guide_cache.get(effective_key)
            if cached and cached[0] == effective_version:
                return cached[1]

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
        # 마크다운 이미지 태그를 HTML로 변환
        body = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" class="tb-img">', body)
        # bullet + table + paragraph를 HTML로
        html_lines = []
        table_rows = []
        para_lines = []

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

        def _flush_para():
            nonlocal para_lines
            if not para_lines:
                return
            text = " ".join(para_lines)
            text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
            text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
            html_lines.append(f"<p>{text}</p>")
            para_lines = []

        for line in body.split("\n"):
            line = line.strip()
            if not line:
                _flush_table()
                _flush_para()
                continue
            # 마크다운 테이블 행
            if line.startswith("|"):
                _flush_para()
                # 구분선(|---|---|) 건너뜀
                if re.match(r"^\|[\s\-:|]+\|$", line):
                    continue
                # 볼드 변환
                line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
                line = re.sub(r"\*(.+?)\*", r"<em>\1</em>", line)
                table_rows.append(line)
                continue
            _flush_table()
            # 원번호(①~⑳) 항목 감지
            circled_match = re.match(r"^([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳])\s*(.*)", line)
            if circled_match:
                _flush_para()
                num = circled_match.group(1)
                line_content = circled_match.group(2)
                line_content = re.sub(
                    r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line_content
                )
                line_content = re.sub(r"\*(.+?)\*", r"<em>\1</em>", line_content)
                html_lines.append(f"<div class='num-item'><span class='num-marker'>{num}</span>{line_content}</div>")
            elif line.startswith("→ ") or line.startswith("  → "):
                _flush_para()
                line_content = line.lstrip().lstrip("→").strip()
                line_content = re.sub(
                    r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line_content
                )
                line_content = re.sub(r"\*(.+?)\*", r"<em>\1</em>", line_content)
                html_lines.append(f"<div class='num-item num-sub'>→ {line_content}</div>")
            elif line.startswith("- "):
                _flush_para()
                line_content = line[2:]
                # 볼드 변환
                line_content = re.sub(
                    r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line_content
                )
                # 이탤릭 변환
                line_content = re.sub(r"\*(.+?)\*", r"<em>\1</em>", line_content)
                html_lines.append(f"<li>{line_content}</li>")
            elif line.startswith("  - "):
                _flush_para()
                line_content = line[4:]
                line_content = re.sub(
                    r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line_content
                )
                line_content = re.sub(r"\*(.+?)\*", r"<em>\1</em>", line_content)
                html_lines.append(f"<li class='sub-item'>{line_content}</li>")
            elif "<img " in line:
                _flush_para()
                html_lines.append(line)
            else:
                para_lines.append(line)

        _flush_table()
        _flush_para()
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

    _study_guide_cache[effective_key] = (effective_version, chapters)
    return chapters


def build_results(attempts):
    """GisaAttempt 쿼리셋을 템플릿용 results 리스트로 변환"""
    results = []
    for a in attempts:
        q = a.question
        correct_answers = q.answer.split(",")
        choices = []
        for i, (text, exp, img) in enumerate(
            [
                (q.choice_1, q.choice_1_exp, q.choice_1_image),
                (q.choice_2, q.choice_2_exp, q.choice_2_image),
                (q.choice_3, q.choice_3_exp, q.choice_3_image),
                (q.choice_4, q.choice_4_exp, q.choice_4_image),
            ],
            start=1,
        ):
            choices.append(
                {
                    "num": i,
                    "text": text,
                    "exp": exp,
                    "image": img,
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
    exams = GisaExam.objects.filter(certification=cert).exclude(exam_type="최신")
    subjects = GisaSubject.objects.filter(certification=cert)

    active_tab = request.GET.get("tab", "textbook")
    total_questions = GisaQuestion.objects.filter(exam__certification=cert).exclude(exam__exam_type="최신").count()

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

    wrong_results = []
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
        wrong_attempts = (
            GisaAttempt.objects.filter(pk__in=latest_ids, is_correct=False)
            .select_related("question", "question__subject", "question__exam")
            .order_by("question__subject__order", "question__number")
        )
        wrong_results = build_results(wrong_attempts)
        wrong_count = len(wrong_results)

    # history 탭은 API로 무한 스크롤 로딩 (certification_detail에서 직접 로드하지 않음)

    # 최신기출 탭: exam_type='최신'인 GisaExam
    latest_year_cards = []
    latest_questions = []
    if active_tab == "latest":
        latest_exams = (
            GisaExam.objects.filter(certification=cert, exam_type="최신")
            .annotate(q_count=Count("gisaquestion"))
            .order_by("-year", "-round")
        )
        # 과목별 문항수 집계
        subject_counts = (
            GisaQuestion.objects.filter(exam__certification=cert, exam__exam_type="최신")
            .values("exam__pk", "subject__pk", "subject__name", "subject__order")
            .annotate(cnt=Count("pk"))
            .order_by("exam__pk", "subject__order")
        )
        exam_subject_map = {}
        for sc in subject_counts:
            exam_subject_map.setdefault(sc["exam__pk"], []).append({
                "pk": sc["subject__pk"],
                "name": sc["subject__name"],
                "count": sc["cnt"],
            })

        latest_year_cards = [
            {
                "year": e.year, "round": e.round, "count": e.q_count,
                "exam_id": e.pk, "subjects": exam_subject_map.get(e.pk, []),
            }
            for e in latest_exams if e.q_count > 0
        ]
        latest_questions = (
            GisaQuestion.objects.filter(exam__certification=cert, exam__exam_type="최신")
            .select_related("exam", "subject")
            .order_by("-exam__year", "-exam__round", "number")
        )

    # 교재 데이터 — 교재 탭일 때만 장 제목 전달 (섹션은 AJAX로 로드)
    textbook_chapters = []
    first_subject = subjects.first().name if subjects.exists() else ""
    textbook_subject = request.GET.get("subject", first_subject)
    textbook_subjects = list(subjects.values_list("name", flat=True))
    if active_tab == "textbook":
        textbook = GisaTextbook.objects.filter(
            certification=cert, subject__name=textbook_subject
        ).first()
        if textbook:
            full = parse_study_guide(
                textbook.content,
                cache_key=f"gisa_tb_{textbook.pk}",
                cache_version=textbook.updated_at,
            )
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
            "wrong_results": wrong_results,
            "exam_sessions": exam_sessions,
            "active_tab": active_tab,
            "total_questions": total_questions,
            "textbook_chapters": textbook_chapters,
            "textbook_subject": textbook_subject,
            "textbook_subjects": textbook_subjects,
            "latest_year_cards": latest_year_cards,
            "latest_questions": latest_questions,
        },
    )


## ══════════ 교재 AJAX API ══════════ ##


@login_required
def textbook_chapter_api(request, cert_id):
    """AJAX: 특정 장의 섹션 HTML을 JSON으로 반환"""
    cert = get_object_or_404(Certification, pk=cert_id)
    first_subj = GisaSubject.objects.filter(certification=cert).order_by("order").values_list("name", flat=True).first() or ""
    subject = request.GET.get("subject", first_subj)
    ch_idx = int(request.GET.get("ch", 0))

    textbook = GisaTextbook.objects.filter(
        certification=cert, subject__name=subject
    ).first()
    if not textbook:
        return JsonResponse({"html": ""})
    chapters = parse_study_guide(
        textbook.content,
        cache_key=f"gisa_tb_{textbook.pk}",
        cache_version=textbook.updated_at,
    )

    if ch_idx < 0 or ch_idx >= len(chapters):
        return JsonResponse({"html": ""})

    chapter = chapters[ch_idx]
    html = render_to_string(
        "gisa/_chapter_body.html", {"ch": chapter, "cert": cert}, request=request
    )
    return JsonResponse({"html": html})


## ══════════ 최신기출 CRUD ══════════ ##


@login_required
@require_POST
def gisa_latest_create(request, cert_id):
    cert = get_object_or_404(Certification, pk=cert_id)
    year = int(request.POST.get("year", 2025))
    round_num = int(request.POST.get("round", 1))

    subject_id = request.POST.get("subject")
    if subject_id:
        subject = get_object_or_404(GisaSubject, pk=subject_id, certification=cert)
    else:
        subject = GisaSubject.objects.filter(certification=cert).order_by("order").first()
    text = request.POST.get("text", "")
    exam, _ = GisaExam.objects.get_or_create(
        certification=cert, year=year, round=round_num, exam_type="최신",
    )

    if GisaQuestion.objects.filter(exam=exam, text=text).exists():
        messages.warning(request, f"{year}년 {round_num}회차에 동일한 문제가 이미 등록되어 있습니다.")
        return redirect(f"{reverse('gisa:certification_detail', args=[cert_id])}?tab=latest&last_year={year}&last_round={round_num}")

    max_num = GisaQuestion.objects.filter(exam=exam).aggregate(Max("number"))["number__max"] or 0
    GisaQuestion.objects.create(
        exam=exam,
        subject=subject,
        number=max_num + 1,
        text=text,
        choice_1=request.POST.get("choice_1", "") or "-",
        choice_2=request.POST.get("choice_2", "") or "-",
        choice_3=request.POST.get("choice_3", "") or "-",
        choice_4=request.POST.get("choice_4", "") or "-",
        answer=request.POST.get("answer", "0"),
        explanation=request.POST.get("explanation", ""),
        created_by_name=request.user.get_full_name() or request.user.username,
    )

    return redirect(f"{reverse('gisa:certification_detail', args=[cert_id])}?tab=latest&last_year={year}&last_round={round_num}")


@login_required
@require_POST
def gisa_latest_update(request, cert_id, question_id):
    cert = get_object_or_404(Certification, pk=cert_id)
    question = get_object_or_404(
        GisaQuestion, pk=question_id, exam__certification=cert, exam__exam_type="최신"
    )

    new_year = int(request.POST.get("year", question.exam.year))
    new_round = int(request.POST.get("round", question.exam.round))

    if new_year != question.exam.year or new_round != question.exam.round:
        old_exam = question.exam
        new_exam, _ = GisaExam.objects.get_or_create(
            certification=cert, year=new_year, round=new_round, exam_type="최신",
        )
        max_num = GisaQuestion.objects.filter(exam=new_exam).aggregate(Max("number"))["number__max"] or 0
        question.exam = new_exam
        question.number = max_num + 1
        # 이전 exam이 비면 삭제
        if not GisaQuestion.objects.filter(exam=old_exam).exclude(pk=question.pk).exists():
            old_exam.delete()

    new_subject_id = request.POST.get("subject")
    if new_subject_id:
        question.subject = get_object_or_404(GisaSubject, pk=new_subject_id, certification=cert)

    question.text = request.POST.get("text", question.text)
    question.choice_1 = request.POST.get("choice_1", question.choice_1) or "-"
    question.choice_2 = request.POST.get("choice_2", question.choice_2) or "-"
    question.choice_3 = request.POST.get("choice_3", question.choice_3) or "-"
    question.choice_4 = request.POST.get("choice_4", question.choice_4) or "-"
    question.answer = request.POST.get("answer", question.answer)
    question.explanation = request.POST.get("explanation", question.explanation)
    question.save()

    return redirect(f"{reverse('gisa:certification_detail', args=[cert_id])}?tab=latest&open_exam={new_year}-{new_round}")


@login_required
@require_POST
def gisa_latest_delete(request, cert_id, question_id):
    cert = get_object_or_404(Certification, pk=cert_id)
    question = get_object_or_404(
        GisaQuestion, pk=question_id, exam__certification=cert, exam__exam_type="최신"
    )
    exam = question.exam
    question.delete()

    if not GisaQuestion.objects.filter(exam=exam).exists():
        exam.delete()

    return redirect(f"{reverse('gisa:certification_detail', args=[cert_id])}?tab=latest")


@login_required
def gisa_latest_study(request, cert_id, year, round_num):
    cert = get_object_or_404(Certification, pk=cert_id)
    exam = GisaExam.objects.filter(certification=cert, year=year, round=round_num, exam_type="최신").first()
    if not exam:
        return redirect(f"{reverse('gisa:certification_detail', args=[cert_id])}?tab=latest")

    questions = GisaQuestion.objects.filter(exam=exam).order_by("number")
    if not questions.exists():
        return redirect(f"{reverse('gisa:certification_detail', args=[cert_id])}?tab=latest")

    return render(
        request,
        "gisa/study_mode.html",
        {
            "cert": cert,
            "exam": exam,
            "subject": None,
            "questions": questions,
            "from_tab": "latest",
        },
    )


@login_required
@require_POST
def gisa_latest_clone(request, cert_id):
    """기존 기출문제를 최신기출로 복사 등록"""
    cert = get_object_or_404(Certification, pk=cert_id)
    source_id = request.POST.get("source_id")
    target_year = int(request.POST.get("target_year", 2025))
    target_round = int(request.POST.get("target_round", 1))
    sub = request.POST.get("sub", "existing")

    source = get_object_or_404(GisaQuestion, pk=source_id, exam__certification=cert)

    exam, _ = GisaExam.objects.get_or_create(
        certification=cert, year=target_year, round=target_round, exam_type="최신",
    )

    if GisaQuestion.objects.filter(exam=exam, text=source.text).exists():
        messages.warning(request, f"{target_year}년 {target_round}회차에 동일한 문제가 이미 등록되어 있습니다.")
        return redirect(
            f"{reverse('gisa:certification_detail', args=[cert_id])}?tab=latest"
            f"&last_year={target_year}&last_round={target_round}&sub={sub}"
        )

    max_num = GisaQuestion.objects.filter(exam=exam).aggregate(Max("number"))["number__max"] or 0
    GisaQuestion.objects.create(
        exam=exam,
        subject=source.subject,
        number=max_num + 1,
        text=source.text,
        choice_1=source.choice_1,
        choice_2=source.choice_2,
        choice_3=source.choice_3,
        choice_4=source.choice_4,
        answer=source.answer,
        explanation=source.explanation,
        choice_1_exp=source.choice_1_exp,
        choice_2_exp=source.choice_2_exp,
        choice_3_exp=source.choice_3_exp,
        choice_4_exp=source.choice_4_exp,
        created_by_name=request.user.get_full_name() or request.user.username,
    )

    return redirect(
        f"{reverse('gisa:certification_detail', args=[cert_id])}?tab=latest"
        f"&last_year={target_year}&last_round={target_round}&sub={sub}"
    )


@login_required
def api_gisa_existing_exams(request, cert_id):
    """기존 기출 시험 목록 (최신기출 제외)"""
    cert = get_object_or_404(Certification, pk=cert_id)
    exams = (
        GisaExam.objects.filter(certification=cert)
        .exclude(exam_type="최신")
        .order_by("-year", "-round")
        .values_list("pk", "year", "round", "exam_type")
    )
    return JsonResponse({
        "exams": [
            {"id": pk, "year": y, "round": r, "exam_type": t,
             "label": f"{y}년 {r}회 {t}"}
            for pk, y, r, t in exams
        ]
    })


@login_required
def api_gisa_exam_questions(request, cert_id, exam_id):
    """특정 시험회차의 문제 목록"""
    cert = get_object_or_404(Certification, pk=cert_id)
    exam = get_object_or_404(GisaExam, pk=exam_id, certification=cert)
    questions = GisaQuestion.objects.filter(exam=exam).order_by("number")
    return JsonResponse({
        "questions": [
            {
                "id": q.pk, "number": q.number, "text": q.text,
                "choice_1": q.choice_1, "choice_2": q.choice_2,
                "choice_3": q.choice_3, "choice_4": q.choice_4,
                "answer": q.answer, "explanation": q.explanation,
                "subject": q.subject.name,
            }
            for q in questions
        ]
    })


@login_required
def api_gisa_search_questions(request, cert_id):
    """기출문제 유사 검색 (최신기출 제외) — 문장 입력 시 단어별 OR 검색 + 매칭수 정렬"""
    cert = get_object_or_404(Certification, pk=cert_id)
    keyword = request.GET.get("q", "").strip()
    if len(keyword) < 2:
        return JsonResponse({"questions": [], "keywords": []})

    # 단어 분리 (1글자 제거, 최대 10개)
    words = [w for w in keyword.split() if len(w) >= 2][:10]
    if not words:
        words = [keyword]

    # 단어별 OR 조건
    combined_q = Q()
    for w in words:
        combined_q |= (
            Q(text__icontains=w)
            | Q(choice_1__icontains=w)
            | Q(choice_2__icontains=w)
            | Q(choice_3__icontains=w)
            | Q(choice_4__icontains=w)
        )

    # DB 레벨에서 매칭 단어 수 집계 → 상위 50개만 가져오기
    match_annotation = Value(0, output_field=IntegerField())
    for w in words:
        word_q = (
            Q(text__icontains=w)
            | Q(choice_1__icontains=w)
            | Q(choice_2__icontains=w)
            | Q(choice_3__icontains=w)
            | Q(choice_4__icontains=w)
        )
        match_annotation = match_annotation + Case(
            When(word_q, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )

    qs = (
        GisaQuestion.objects.filter(exam__certification=cert)
        .exclude(exam__exam_type="최신")
        .filter(combined_q)
        .annotate(match_count=match_annotation)
        .select_related("exam", "subject")
        .order_by("-match_count", "-exam__year", "-exam__round", "number")[:50]
    )

    return JsonResponse({
        "questions": [
            {
                "id": q.pk, "number": q.number, "text": q.text,
                "choice_1": q.choice_1, "choice_2": q.choice_2,
                "choice_3": q.choice_3, "choice_4": q.choice_4,
                "answer": q.answer, "year": q.exam.year,
                "round": q.exam.round, "subject": q.subject.name,
                "match_count": q.match_count,
            }
            for q in qs
        ],
        "keywords": words,
    })


## ══════════ 학습모드 ══════════ ##


@login_required
def study_mode(request, cert_id, exam_id, subject_id=None):
    cert = get_object_or_404(Certification, pk=cert_id)
    exam = get_object_or_404(GisaExam, pk=exam_id, certification=cert)

    if subject_id:
        subject = get_object_or_404(GisaSubject, pk=subject_id, certification=cert)
        questions = GisaQuestion.objects.filter(
            exam=exam, subject=subject
        ).order_by("number")
    else:
        subject = None
        questions = GisaQuestion.objects.filter(exam=exam).select_related("subject").order_by("number")

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
    results = build_results(attempts)

    # 과목별 점수 계산 (history_api와 동일 로직)
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

    # 과목별 평균 점수 (history_api와 동일)
    if subject_scores:
        score = round(sum(v["score"] for v in subject_scores.values()) / len(subject_scores))
        passed = score >= 60 and all(v["score"] >= 40 for v in subject_scores.values())
    else:
        score = 0
        passed = False

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
            "passed": passed,
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
            ).exclude(exam__exam_type="최신").order_by("?")[:20]
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
    results = build_results(attempts)

    # 과목별 평균 점수 (history_api와 동일)
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

    if subject_scores:
        score = round(sum(v["score"] for v in subject_scores.values()) / len(subject_scores))
        passed = score >= 60 and all(v["score"] >= 40 for v in subject_scores.values())
    else:
        score = 0
        passed = False

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
            "passed": passed,
            "subject_scores": subject_scores,
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

    qs = GisaQuestion.objects.filter(pk__in=wrong_qids).select_related("subject", "exam")
    subject_filter = request.GET.get("subject", "")
    if subject_filter:
        qs = qs.filter(subject__name=subject_filter)
    questions = list(qs.order_by("subject__order", "number"))

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
            "wrong_subject_filter": subject_filter,
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
            "passed": False,
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


## ══════════ 시험이력 API (무한 스크롤) ══════════ ##


@login_required
def history_api(request, cert_id):
    """시험이력 세션 목록을 페이지네이션하여 JSON 반환"""
    cert = get_object_or_404(Certification, pk=cert_id)
    page = int(request.GET.get("page", 1))
    per_page = 20

    session_rows = (
        GisaAttempt.objects.filter(
            user=request.user,
            question__exam__certification=cert,
        )
        .exclude(session_id="")
        .values("session_id")
        .annotate(
            total=Count("id"),
            correct=Count("id", filter=Q(is_correct=True)),
            date=Min("created_at"),
        )
        .order_by("-date")
    )
    total_count = session_rows.count()
    start = (page - 1) * per_page
    rows = list(session_rows[start : start + per_page])

    mode_labels = {"exam": "기출고사", "mock": "모의고사", "wrong_retry": "오답재풀이"}
    results = []
    for row in rows:
        sid = row["session_id"]
        s_attempts = GisaAttempt.objects.filter(user=request.user, session_id=sid).select_related("question__subject")
        first = s_attempts.order_by("created_at").first()
        total = row["total"]
        correct = row["correct"]
        wrong = total - correct
        mode = first.mode if first else "exam"

        # 과목별 점수 산정 (기출고사/모의고사)
        subjects_data = []
        if mode in ("exam", "mock"):
            subj_stats = (
                s_attempts.values("question__subject__name")
                .annotate(
                    s_total=Count("id"),
                    s_correct=Count("id", filter=Q(is_correct=True)),
                )
                .order_by("question__subject__order")
            )
            for ss in subj_stats:
                s_score = round(ss["s_correct"] / ss["s_total"] * 100) if ss["s_total"] else 0
                subjects_data.append({
                    "name": ss["question__subject__name"],
                    "correct": ss["s_correct"],
                    "total": ss["s_total"],
                    "score": s_score,
                })
            avg_score = round(sum(s["score"] for s in subjects_data) / len(subjects_data)) if subjects_data else 0
            passed = avg_score >= 60 and all(s["score"] >= 40 for s in subjects_data)
        else:
            avg_score = round(correct / total * 100) if total else 0
            passed = False

        results.append({
            "session_id": sid,
            "mode": mode,
            "mode_label": mode_labels.get(mode, mode),
            "total": total,
            "correct": correct,
            "wrong": wrong,
            "score": avg_score,
            "passed": passed,
            "subjects": subjects_data,
            "date": row["date"].strftime("%Y-%m-%d %H:%M"),
            "wrong_url": reverse("gisa:wrong_answers_session", args=[cert_id, sid]) if wrong > 0 else "",
            "delete_url": reverse("gisa:session_delete", args=[cert_id, sid]),
        })

    return JsonResponse({
        "sessions": results,
        "has_next": (start + per_page) < total_count,
        "total": total_count,
    })


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

    # 교재 과목/장/절 정보 추출 (뒤로가기 시 해당 위치로 이동)
    textbook_subject = ""
    chapter_idx = ""
    section_id = ""
    if questions:
        subj_name = questions[0].subject.name if questions[0].subject else ""
        textbook_subject = subj_name
        tb = GisaTextbook.objects.filter(certification=cert, subject__name=subj_name).first()
        if tb:
            chapters = parse_study_guide(
                tb.content,
                cache_key=f"gisa_tb_{tb.pk}",
                cache_version=tb.updated_at,
            )
            for ci, ch in enumerate(chapters):
                for sec in ch.get("sections", []):
                    if sec["title"] == section_title:
                        chapter_idx = str(ci)
                        section_id = sec["id"]
                        break
                    for sub in sec.get("subsections", []):
                        if sub["title"] == section_title:
                            chapter_idx = str(ci)
                            section_id = sec["id"]
                            break
                    if section_id:
                        break
                if section_id:
                    break

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
            "textbook_subject": textbook_subject,
            "chapter_idx": chapter_idx,
            "section_id": section_id,
        },
    )


## ══════════ 기사문제 관리 ══════════ ##


def _gisa_staff_required(user):
    return user.is_active and user.is_staff


@login_required
@user_passes_test(_gisa_staff_required)
def gisa_question_manage(request):
    import json as _json

    certs = Certification.objects.all().order_by("name")
    # 자격증별 과목 목록 JSON
    subjects_map = {}
    for s in GisaSubject.objects.select_related("certification").order_by("order"):
        subjects_map.setdefault(s.certification_id, []).append(
            {"id": s.pk, "name": s.name}
        )

    return render(
        request,
        "gisa/gisa_question_manage.html",
        {
            "certs": certs,
            "subjects_json": _json.dumps(subjects_map, ensure_ascii=False),
        },
    )


@login_required
@user_passes_test(_gisa_staff_required)
@require_POST
def manage_nouns(request):
    """문제 텍스트에서 명사 추출 (kiwipiepy)"""
    import json as _json

    try:
        data = _json.loads(request.body)
    except _json.JSONDecodeError:
        return JsonResponse({"nouns": []})

    text = data.get("text", "").strip()
    if not text:
        return JsonResponse({"nouns": []})

    from kiwipiepy import Kiwi
    kiwi = Kiwi()
    tokens = kiwi.tokenize(text)
    # NN*: 일반명사(NNG), 고유명사(NNP), 의존명사(NNB) 등
    seen = set()
    nouns = []
    for t in tokens:
        if t.tag.startswith("NN") and len(t.form) >= 2 and t.form not in seen:
            seen.add(t.form)
            nouns.append(t.form)

    return JsonResponse({"nouns": nouns})


@login_required
@user_passes_test(_gisa_staff_required)
@require_POST
def manage_search(request):
    """문제 텍스트 검색 — 선택된 키워드 AND 검색 + 과목 필터"""
    import json as _json

    try:
        data = _json.loads(request.body)
    except _json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "잘못된 요청"}, status=400)

    words = data.get("keywords", [])
    subject_id = data.get("subject_id")

    if not words:
        return JsonResponse({"questions": []})

    # 과목 필터
    qs = GisaQuestion.objects.all()
    if subject_id:
        qs = qs.filter(subject_id=subject_id)

    # 키워드별 AND 조건 (각 키워드는 text OR choice 에 포함)
    for w in words[:10]:
        w = w.strip()
        if len(w) < 2:
            continue
        qs = qs.filter(
            Q(text__icontains=w)
            | Q(choice_1__icontains=w)
            | Q(choice_2__icontains=w)
            | Q(choice_3__icontains=w)
            | Q(choice_4__icontains=w)
        )

    # 매칭 단어 수로 정렬
    match_annotation = Value(0, output_field=IntegerField())
    for w in words[:10]:
        w = w.strip()
        if len(w) < 2:
            continue
        word_q = (
            Q(text__icontains=w)
            | Q(choice_1__icontains=w)
            | Q(choice_2__icontains=w)
            | Q(choice_3__icontains=w)
            | Q(choice_4__icontains=w)
        )
        match_annotation = match_annotation + Case(
            When(word_q, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )

    qs = (
        qs.annotate(match_count=match_annotation)
        .select_related("exam", "exam__certification", "subject")
        .order_by("-match_count", "-exam__year", "-exam__round", "number")[:30]
    )

    return JsonResponse({
        "questions": [
            {
                "id": q.pk,
                "number": q.number,
                "text": q.text,
                "choice_1": q.choice_1,
                "choice_2": q.choice_2,
                "choice_3": q.choice_3,
                "choice_4": q.choice_4,
                "answer": q.answer,
                "explanation": q.explanation or "",
                "year": q.exam.year,
                "round": q.exam.round,
                "subject": q.subject.name,
                "subject_id": q.subject_id,
                "cert_name": q.exam.certification.name,
                "match_count": q.match_count,
            }
            for q in qs
        ],
    })


@login_required
@user_passes_test(_gisa_staff_required)
@require_POST
def manage_register(request):
    """문제 등록 — copy(기존 복사) 또는 new(직접 등록)"""
    import json as _json

    try:
        data = _json.loads(request.body)
    except _json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "잘못된 요청"}, status=400)

    mode = data.get("mode")
    cert_id = data.get("cert_id")
    year = data.get("year")
    round_num = data.get("round")
    subject_id = data.get("subject_id")
    number = data.get("number")

    if not all([cert_id, year, round_num, subject_id, number]):
        return JsonResponse({"ok": False, "error": "필수 항목 누락"}, status=400)

    cert = get_object_or_404(Certification, pk=cert_id)
    subject = get_object_or_404(GisaSubject, pk=subject_id)
    exam, _ = GisaExam.objects.get_or_create(
        certification=cert, year=year, round=round_num, exam_type="최신",
    )

    # 등록할 텍스트 결정
    if mode == "copy":
        source = get_object_or_404(GisaQuestion, pk=data.get("source_id"))
        q_text = source.text
    elif mode == "new":
        q_text = data.get("text", "")
    else:
        return JsonResponse({"ok": False, "error": "mode는 copy 또는 new"}, status=400)

    # 중복 체크: 같은 시험에 동일한 문제 텍스트가 있으면 중복
    if GisaQuestion.objects.filter(exam=exam, text=q_text).exists():
        return JsonResponse({"ok": False, "error": "동일한 문제가 이미 존재합니다"}, status=409)

    # 번호 충돌 시 연속으로 빈 번호 탐색
    existing = set(GisaQuestion.objects.filter(exam=exam).values_list("number", flat=True))
    while number in existing:
        number += 1

    # 등록자명: 로그인 사용자
    by_name = ""
    if request.user.is_authenticated:
        by_name = request.user.get_full_name() or request.user.username

    if mode == "copy":
        GisaQuestion.objects.create(
            exam=exam, subject=subject, number=number,
            text=source.text,
            choice_1=source.choice_1, choice_2=source.choice_2,
            choice_3=source.choice_3, choice_4=source.choice_4,
            answer=source.answer, explanation=source.explanation,
            choice_1_exp=source.choice_1_exp, choice_2_exp=source.choice_2_exp,
            choice_3_exp=source.choice_3_exp, choice_4_exp=source.choice_4_exp,
            created_by_name=by_name,
        )
    elif mode == "new":
        GisaQuestion.objects.create(
            exam=exam, subject=subject, number=number,
            text=q_text,
            choice_1=data.get("choice_1", ""),
            choice_2=data.get("choice_2", ""),
            choice_3=data.get("choice_3", ""),
            choice_4=data.get("choice_4", ""),
            answer=data.get("answer", "0"),
            created_by_name=by_name,
        )
    else:
        return JsonResponse({"ok": False, "error": "mode는 copy 또는 new"}, status=400)

    return JsonResponse({"ok": True})


@login_required
@user_passes_test(_gisa_staff_required)
@require_POST
def gisa_question_delete(request, pk):
    question = get_object_or_404(GisaQuestion, pk=pk)
    cert_id = question.exam.certification_id
    exam_id = question.exam_id
    question.delete()
    return redirect(f"/gisa/manage/?cert={cert_id}&exam={exam_id}")


@login_required
@user_passes_test(_gisa_staff_required)
@require_POST
def gisa_question_update(request, pk):
    import json
    question = get_object_or_404(GisaQuestion, pk=pk)

    # multipart/form-data (이미지 업로드 포함)
    if request.content_type and "multipart" in request.content_type:
        data = request.POST
        files = request.FILES
        # 이미지 필드 처리
        img_fields = ["text_image", "choice_1_image", "choice_2_image", "choice_3_image", "choice_4_image"]
        for field in img_fields:
            if field in files:
                setattr(question, field, files[field])
            elif data.get(f"{field}_clear") == "1":
                setattr(question, field, "")
    else:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"ok": False, "error": "잘못된 요청"}, status=400)

    question.text = data.get("text", question.text)
    question.choice_1 = data.get("choice_1", question.choice_1)
    question.choice_2 = data.get("choice_2", question.choice_2)
    question.choice_3 = data.get("choice_3", question.choice_3)
    question.choice_4 = data.get("choice_4", question.choice_4)
    question.answer = data.get("answer", question.answer)
    if "explanation" in data:
        question.explanation = data["explanation"]
    if "choice_1_exp" in data:
        question.choice_1_exp = data["choice_1_exp"]
    if "choice_2_exp" in data:
        question.choice_2_exp = data["choice_2_exp"]
    if "choice_3_exp" in data:
        question.choice_3_exp = data["choice_3_exp"]
    if "choice_4_exp" in data:
        question.choice_4_exp = data["choice_4_exp"]
    question.save()
    return JsonResponse({"ok": True})


@login_required
@user_passes_test(_gisa_staff_required)
@require_POST
def gisa_question_generate_exp(request, pk):
    """Gemini API로 문제 해설 생성"""
    import json
    from django.conf import settings as djsettings

    question = get_object_or_404(GisaQuestion, pk=pk)

    api_key = djsettings.GEMINI_API_KEY
    if not api_key:
        return JsonResponse({"ok": False, "error": "GEMINI_API_KEY 미설정"}, status=500)

    try:
        from google import genai
        from pydantic import BaseModel, Field

        class ExpResult(BaseModel):
            explanation: str = Field(description="정답에 대한 설명")
            choice_1_exp: str = Field(description="보기 ①에 대한 해설")
            choice_2_exp: str = Field(description="보기 ②에 대한 해설")
            choice_3_exp: str = Field(description="보기 ③에 대한 해설")
            choice_4_exp: str = Field(description="보기 ④에 대한 해설")

        circles = {"1": "①", "2": "②", "3": "③", "4": "④"}
        answer_circle = circles.get(question.answer, "?")
        cert = question.exam.certification
        cert_full = cert.name if cert.category in cert.name else f"{cert.name}{cert.category}"
        prompt_text = (
            f"당신은 {cert_full} 시험 전문가이다.\n"
            f"다음은 {cert_full} {question.subject.name} 기출문제이다.\n\n"
            f"{question.number}. {question.text}\n"
            f"① {question.choice_1}\n② {question.choice_2}\n"
            f"③ {question.choice_3}\n④ {question.choice_4}\n\n"
            f"정답은 {answer_circle}\n\n"
            f"해당 문제에 대해 [정답설명]과 [선지별 해설]을 해줘.\n"
            f"화학식은 유니코드 아래첨자/위첨자를 사용해서 표기해라. 예: H₂O, Ca²⁺, NO₃⁻, CO₂, C₂H₅OH, PO₄³⁻\n"
            f"공부팁이나 인사말 기타 내용은 넣지마"
        )

        # 이미지 필드가 있으면 멀티모달로 전송
        from google.genai import types
        import pathlib
        contents = []
        image_fields = [
            ("text_image", "문제 이미지:"),
            ("choice_1_image", "보기 ① 이미지:"),
            ("choice_2_image", "보기 ② 이미지:"),
            ("choice_3_image", "보기 ③ 이미지:"),
            ("choice_4_image", "보기 ④ 이미지:"),
        ]
        for field_name, label in image_fields:
            img_field = getattr(question, field_name)
            if img_field and img_field.name:
                img_path = img_field.path
                if pathlib.Path(img_path).exists():
                    contents.append(label)
                    contents.append(types.Part.from_bytes(
                        data=pathlib.Path(img_path).read_bytes(),
                        mime_type="image/png",
                    ))
        contents.append(prompt_text)

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=contents,
            config={
                "response_mime_type": "application/json",
                "response_schema": ExpResult,
            },
        )
        result = ExpResult.model_validate_json(response.text)

        question.explanation = result.explanation
        question.choice_1_exp = result.choice_1_exp
        question.choice_2_exp = result.choice_2_exp
        question.choice_3_exp = result.choice_3_exp
        question.choice_4_exp = result.choice_4_exp
        if question.answer in ("1", "2", "3", "4"):
            setattr(question, f"choice_{question.answer}_exp", result.explanation)
        question.save()

        return JsonResponse({
            "ok": True,
            "explanation": question.explanation,
            "choice_1_exp": question.choice_1_exp,
            "choice_2_exp": question.choice_2_exp,
            "choice_3_exp": question.choice_3_exp,
            "choice_4_exp": question.choice_4_exp,
        })
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
