from collections import OrderedDict
from datetime import date, datetime, time, timedelta

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST

import json
import logging
import markdown
import re

from django.conf import settings
from django.db.models import Case, Count, F, IntegerField, Max, Min, Q, Sum, Value, When
from django.db.models.functions import TruncDate

from django.contrib.auth.models import User
from google import genai
from pydantic import BaseModel, Field

from accounts.models import LoginLog
from exam.models import Attempt, Question, StudyNote
from gisa.models import GisaAttempt, GisaQuestion
from .forms import SubjectForm
from .models import FavoriteSubject, Subject, SubjectMaterial

logger = logging.getLogger(__name__)


_note_chapters_cache = {}


def parse_note_chapters(content, subject_pk, cache_version=None):
    """StudyNote 마크다운을 장/절/항 구조로 파싱 (기사시험 parse_study_guide 동일 구조).
    ref 형식: YYYY-기말-N → hidden input에는 YYYY-N으로 변환하여 전달.
    """
    cache_key = f"note_{subject_pk}"
    if cache_version is not None:
        cached = _note_chapters_cache.get(cache_key)
        if cached and cached[0] == cache_version:
            return cached[1]

    chapters = []
    current_chapter = None
    current_section = None
    current_subsection = None
    content_lines = []

    def _flush_content():
        nonlocal content_lines
        if not content_lines:
            return
        text = "\n".join(content_lines).strip()
        if not text:
            content_lines = []
            return

        # 관련 문제 추출: YYYY-기말-N 또는 YYYY-N 형식
        raw_refs = re.findall(r"(\d{4})-(?:기말|중간|계절)-(\d+)", text)
        questions = [f"{y}-{n}" for y, n in raw_refs]
        if not questions:
            questions = re.findall(r"(?<!\w)(\d{4}-\d+)(?!\w)", text)

        # 관련 문제 줄 제거
        body = re.sub(r"\*\*관련 문제\*\*:.*", "", text, flags=re.DOTALL).strip()
        body = re.sub(r"\*\*관련 기출문제\*\*.*", "", body, flags=re.DOTALL).strip()
        body = re.sub(r"\*\*핵심 정리\*\*", "", body)

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
            joined = " ".join(para_lines)
            joined = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", joined)
            joined = re.sub(r"\*(.+?)\*", r"<em>\1</em>", joined)
            html_lines.append(f"<p>{joined}</p>")
            para_lines = []

        for line in body.split("\n"):
            line = line.strip()
            if not line:
                _flush_table()
                _flush_para()
                continue
            if line.startswith("|"):
                _flush_para()
                if re.match(r"^\|[\s\-:|]+\|$", line):
                    continue
                line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
                line = re.sub(r"\*(.+?)\*", r"<em>\1</em>", line)
                table_rows.append(line)
                continue
            _flush_table()
            circled = re.match(r"^([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳])\s*(.*)", line)
            if circled:
                _flush_para()
                num, lc = circled.group(1), circled.group(2)
                lc = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", lc)
                lc = re.sub(r"\*(.+?)\*", r"<em>\1</em>", lc)
                html_lines.append(f"<div class='num-item'><span class='num-marker'>{num}</span>{lc}</div>")
            elif line.startswith("→ ") or line.startswith("  → "):
                _flush_para()
                lc = line.lstrip().lstrip("→").strip()
                lc = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", lc)
                lc = re.sub(r"\*(.+?)\*", r"<em>\1</em>", lc)
                html_lines.append(f"<div class='num-item num-sub'>→ {lc}</div>")
            elif line.startswith("- "):
                _flush_para()
                lc = line[2:]
                lc = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", lc)
                lc = re.sub(r"\*(.+?)\*", r"<em>\1</em>", lc)
                html_lines.append(f"<li>{lc}</li>")
            elif line.startswith("  - "):
                _flush_para()
                lc = line[4:]
                lc = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", lc)
                lc = re.sub(r"\*(.+?)\*", r"<em>\1</em>", lc)
                html_lines.append(f"<li class='sub-item'>{lc}</li>")
            else:
                para_lines.append(line)

        _flush_table()
        _flush_para()

        has_li = any("<li>" in h or "<li " in h for h in html_lines)
        has_table = any("<table" in h for h in html_lines)
        if has_li and not has_table:
            content_html = "<ul>" + "".join(html_lines) + "</ul>"
        elif has_li and has_table:
            parts = []
            li_buf = []
            for h in html_lines:
                if h.startswith("<li"):
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

        m = re.match(r"^### (.+)", line)
        if m and current_chapter is not None:
            _flush_content()
            sec_title = m.group(1).strip()
            current_section = {
                "id": f"{current_chapter['id']}-s{len(current_chapter['sections'])+1}",
                "title": sec_title,
                "content_html": "",
                "questions": [],
                "subsections": [],
            }
            current_chapter["sections"].append(current_section)
            current_subsection = None
            continue

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

        if line.startswith("# ") or line.startswith("---") or line.startswith("> "):
            continue
        content_lines.append(line)

    _flush_content()

    # total_questions 계산
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

    if cache_version is not None:
        _note_chapters_cache[cache_key] = (cache_version, chapters)
    return chapters


def staff_required(user):
    return user.is_staff


def index(request):
    from bbs.models import Notice

    latest_notices = Notice.objects.all()[:5]
    return render(request, "main/index.html", {"latest_notices": latest_notices})


@login_required
def mypage(request):
    favorite_ids = FavoriteSubject.objects.filter(user=request.user).values_list(
        "subject_id", flat=True
    )
    favorites = Subject.objects.filter(pk__in=favorite_ids)

    # 각 관심과목의 오답 수 계산
    fav_data = []
    for subj in favorites:
        latest_ids = (
            Attempt.objects.filter(user=request.user, question__subject=subj)
            .values("question")
            .annotate(latest_id=Max("id"))
            .values_list("latest_id", flat=True)
        )
        wrong_count = Attempt.objects.filter(pk__in=latest_ids, is_correct=False).count()
        total_questions = Question.objects.filter(subject=subj).count()
        fav_data.append({
            "subject": subj,
            "wrong_count": wrong_count,
            "total_questions": total_questions,
        })

    # 전체 과목 (관심과목 추가용) - 학년별 분류
    all_subjects = Subject.objects.all().order_by("grade", "name")
    subjects_by_grade = OrderedDict()
    for grade_num in range(1, 5):
        grade_subjects = [s for s in all_subjects if s.grade == grade_num]
        if grade_subjects:
            subjects_by_grade[grade_num] = grade_subjects

    return render(
        request,
        "main/mypage.html",
        {
            "fav_data": fav_data,
            "favorite_ids": list(favorite_ids),
            "subjects_by_grade": subjects_by_grade,
        },
    )


@login_required
@require_POST
def favorite_toggle(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id)
    fav, created = FavoriteSubject.objects.get_or_create(
        user=request.user, subject=subject
    )
    if not created:
        fav.delete()
        added = False
    else:
        added = True

    return JsonResponse({"added": added})


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
    favorite_ids = list(
        FavoriteSubject.objects.filter(user=request.user).values_list("subject_id", flat=True)
    )
    return render(request, "main/subject_list.html", {"grades": grades, "favorite_ids": favorite_ids})


@login_required
def subject_detail(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    # 학습/풀이 탭: 2020 이전만
    years = (
        Question.objects.filter(subject=subject, year__lt=2020)
        .values_list("year", flat=True)
        .distinct()
        .order_by("-year")
    )
    year_cards = []
    for year in years:
        count = Question.objects.filter(subject=subject, year=year).count()
        year_cards.append({"year": year, "count": count})

    total_questions = Question.objects.filter(subject=subject, year__lt=2020).count()

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

    active_tab = request.GET.get("tab", "notes")

    # 페이지 진입 로그 저장 (실패해도 페이지 표시는 계속)
    try:
        from .models import SubjectViewLog
        ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() \
            or request.META.get('REMOTE_ADDR')
        ua = request.META.get('HTTP_USER_AGENT', '')[:300]
        SubjectViewLog.objects.create(
            subject=subject,
            user=request.user,
            tab=active_tab[:20],
            ip=ip or None,
            user_agent=ua,
        )
    except Exception:
        pass

    # 정리노트 (구조화된 장/절/항 파싱)
    notes_qs = StudyNote.objects.filter(subject=subject).order_by("order")
    study_notes_count = notes_qs.count()
    note_chapters = []
    if active_tab == "notes" and study_notes_count:
        # 모든 노트의 content를 합쳐서 파싱 (장별 개별 레코드일 수 있음)
        combined = "\n\n".join(n.content for n in notes_qs if n.content)
        if combined.strip():
            latest_updated = max(
                (n.updated_at for n in notes_qs if hasattr(n, 'updated_at') and n.updated_at),
                default=None,
            )
            note_chapters = parse_note_chapters(
                combined, subject.pk,
                cache_version=str(latest_updated) if latest_updated else None,
            )

    # 최신기출: 2020년 이후 연도별 카드
    latest_years = (
        Question.objects.filter(subject=subject, year__gte=2020)
        .values_list("year", flat=True)
        .distinct()
        .order_by("-year")
    )
    latest_year_cards = []
    for year in latest_years:
        count = Question.objects.filter(subject=subject, year=year).count()
        latest_year_cards.append({"year": year, "count": count})

    latest_questions = Question.objects.filter(
        subject=subject, year__gte=2020
    ).order_by("-year", "number")

    # 자료실: PDF 등 첨부 자료 목록
    materials = SubjectMaterial.objects.filter(subject=subject).order_by('-created_at')
    materials_count = materials.count()

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
            "note_chapters": note_chapters,
            "study_notes_count": study_notes_count,
            "latest_year_cards": latest_year_cards,
            "latest_questions": latest_questions,
            "materials": materials,
            "materials_count": materials_count,
        },
    )


@login_required
@require_POST
def latest_question_create(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    year = int(request.POST.get("year", 2024))
    # 해당 과목/연도의 다음 문항번호 자동 부여
    last_num = (
        Question.objects.filter(subject=subject, year=year)
        .order_by("-number")
        .values_list("number", flat=True)
        .first()
    ) or 0
    Question.objects.create(
        subject=subject,
        year=year,
        number=last_num + 1,
        text=request.POST.get("text", ""),
        choice_1=request.POST.get("choice_1", "").strip() or "-",
        choice_2=request.POST.get("choice_2", "").strip() or "-",
        choice_3=request.POST.get("choice_3", "").strip() or "-",
        choice_4=request.POST.get("choice_4", "").strip() or "-",
        answer=request.POST.get("answer", "0"),
        explanation=request.POST.get("explanation", ""),
        created_by_name=request.user.first_name or request.user.username,
    )
    return redirect(f"/subjects/{subject.pk}/?tab=latest&last_year={year}")


@login_required
@require_POST
def latest_question_update(request, question_pk):
    question = get_object_or_404(Question, pk=question_pk)
    subject = question.subject
    new_year = int(request.POST.get("year", question.year))
    if new_year != question.year:
        last_num = (
            Question.objects.filter(subject=subject, year=new_year)
            .order_by("-number")
            .values_list("number", flat=True)
            .first()
        ) or 0
        question.year = new_year
        question.number = last_num + 1
    question.text = request.POST.get("text", question.text)
    question.choice_1 = request.POST.get("choice_1", "").strip() or "-"
    question.choice_2 = request.POST.get("choice_2", "").strip() or "-"
    question.choice_3 = request.POST.get("choice_3", "").strip() or "-"
    question.choice_4 = request.POST.get("choice_4", "").strip() or "-"
    question.answer = request.POST.get("answer", question.answer)
    question.explanation = request.POST.get("explanation", "")
    question.save()
    return redirect(f"/subjects/{subject.pk}/?tab=latest&open_year={question.year}")


@login_required
@require_POST
def latest_question_delete(request, question_pk):
    question = get_object_or_404(Question, pk=question_pk)
    subject = question.subject
    year = question.year
    question.delete()
    return redirect(f"/subjects/{subject.pk}/?tab=latest&open_year={year}")


@login_required
def api_existing_years(request, pk):
    """해당 과목의 기존 기출 연도 목록 (2020 미만)"""
    subject = get_object_or_404(Subject, pk=pk)
    years = list(
        Question.objects.filter(subject=subject, year__lt=2020)
        .values_list("year", flat=True)
        .distinct()
        .order_by("-year")
    )
    return JsonResponse({"years": years})


@login_required
def api_existing_questions(request, pk, year):
    """해당 과목/연도의 기출 문제 목록"""
    subject = get_object_or_404(Subject, pk=pk)
    questions = (
        Question.objects.filter(subject=subject, year=year)
        .order_by("number")
        .values("id", "number", "text", "choice_1", "choice_2", "choice_3", "choice_4", "answer", "explanation",
                "choice_1_exp", "choice_2_exp", "choice_3_exp", "choice_4_exp")
    )
    return JsonResponse({"questions": list(questions)})


@login_required
def api_search_questions(request, pk):
    """해당 과목의 전체 문제에서 유사 검색 (문장 → 단어 분리 → 매칭 수 정렬)"""
    subject = get_object_or_404(Subject, pk=pk)
    keyword = request.GET.get("q", "").strip()
    if not keyword or len(keyword) < 2:
        return JsonResponse({"questions": [], "keywords": [], "error": "2글자 이상 입력하세요."})

    # 불용어 제거 + 2글자 이상 단어만
    stopwords = {"은", "는", "이", "가", "을", "를", "의", "에", "로", "와", "과", "한", "할", "하는", "된", "인", "것은", "대한", "중", "수", "등", "및", "또는", "있는", "없는", "아닌", "않은", "대해", "통해", "위한", "것이", "하여", "에서", "으로", "부터", "까지", "에게", "처럼", "같은", "보다", "만큼"}
    raw_words = re.split(r"[,\s?!.()\-–—·:;/]+", keyword)
    words = [w for w in raw_words if len(w) >= 2 and w not in stopwords]

    if not words:
        return JsonResponse({"questions": [], "keywords": [], "error": "검색 가능한 키워드가 없습니다."})

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

    # DB 레벨에서 매칭 단어 수 집계 → 상위 50개
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
        Question.objects.filter(subject=subject)
        .filter(combined_q)
        .annotate(match_count=match_annotation)
        .order_by("-match_count", "-year", "number")[:50]
    )

    return JsonResponse({
        "questions": [
            {
                "id": q.pk, "year": q.year, "number": q.number,
                "text": q.text, "choice_1": q.choice_1, "choice_2": q.choice_2,
                "choice_3": q.choice_3, "choice_4": q.choice_4, "answer": q.answer,
                "match_count": q.match_count,
            }
            for q in qs
        ],
        "keywords": words,
    })


class ParsedQuestion(BaseModel):
    number: int = Field(description="문제 번호")
    text: str = Field(description="문제 본문")
    choice_1: str = Field(description="보기 ①")
    choice_2: str = Field(description="보기 ②")
    choice_3: str = Field(description="보기 ③")
    choice_4: str = Field(description="보기 ④")
    answer: str = Field(description="정답 번호 (예: '1', '2', '1,3', 미확인이면 '0')")


class ParsedQuestionList(BaseModel):
    questions: list[ParsedQuestion] = Field(description="파싱된 문제 목록")


PARSE_PROMPT = """너는 대학교 기출문제 텍스트를 분석하는 파서이다.

사용자가 붙여넣은 텍스트에서 객관식 문제를 추출하라.

## 규칙

1. number: 문제 번호 (1부터 순서대로)
2. text: 문제 본문. 보기 번호(①②③④)나 정답 표시는 포함하지 말 것
3. choice_1~4: 4지선다 보기. 보기 기호(①②③④, 1.2.3.4., 가나다라) 제거 후 내용만
4. answer: 정답 번호를 문자열로. 단일 정답이면 "1"~"4", 복수 정답이면 "1,3" 형태. 정답을 알 수 없으면 "0"
5. 보기가 없는 문항은 choice에 "-" 입력
6. 보기 없이 답이 바로 제시된 문제는 그 답을 choice_1에 넣고 choice_2~4는 "-", answer는 "1"로 처리. 예시:
   - "1.곤충의 번성에 기여한 주요특징-무변태" → text: "곤충의 번성에 기여한 주요특징", choice_1: "무변태"
   - "2.토양수분의 종류 - 중력수, 모관수, 흡습수" → text: "토양수분의 종류", choice_1: "중력수, 모관수, 흡습수"
   - "답: 토양수분" 형태도 동일하게 처리
7. 문제 본문에 <보기>나 표, 조건문 등이 포함된 경우 text에 그대로 포함
7. 정답이 텍스트 하단에 별도 정답표로 제공된 경우에도 각 문제의 answer에 매핑

## 입력 텍스트

{text}"""

PARSE_PROMPT_IMAGE = """너는 대학교 기출문제 이미지를 분석하는 파서이다.

첨부된 이미지에서 객관식 문제를 추출하라.

## 규칙

1. number: 문제 번호 (1부터 순서대로)
2. text: 문제 본문. 보기 번호(①②③④)나 정답 표시는 포함하지 말 것
3. choice_1~4: 4지선다 보기. 보기 기호(①②③④, 1.2.3.4., 가나다라) 제거 후 내용만
4. answer: 정답 번호를 문자열로. 단일 정답이면 "1"~"4", 복수 정답이면 "1,3" 형태. 정답을 알 수 없으면 "0"
5. 보기가 없는 문항은 choice에 "-" 입력
6. 보기 없이 답이 바로 제시된 문제는 그 답을 choice_1에 넣고 choice_2~4는 "-", answer는 "1"로 처리
7. 문제 본문에 <보기>나 표, 조건문 등이 포함된 경우 text에 그대로 포함
8. 정답이 이미지 하단에 별도 정답표로 제공된 경우에도 각 문제의 answer에 매핑
9. 이미지의 텍스트를 정확히 읽어서 오탈자 없이 추출할 것"""


@login_required
@require_POST
def api_parse_text(request, pk):
    """붙여넣은 텍스트 또는 이미지를 Gemini API로 파싱하여 문제 목록 반환"""
    raw_text = request.POST.get("text", "").strip()
    image_files = request.FILES.getlist("image")

    if not raw_text and not image_files:
        return JsonResponse({"questions": [], "error": "텍스트를 입력하거나 이미지를 첨부하세요."})

    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return JsonResponse({"questions": [], "error": "GEMINI_API_KEY가 설정되지 않았습니다."})

    try:
        client = genai.Client(api_key=api_key)

        if image_files:
            contents = []
            for img in image_files:
                contents.append(genai.types.Part.from_bytes(
                    data=img.read(),
                    mime_type=img.content_type or "image/png",
                ))
            if raw_text:
                contents.append(PARSE_PROMPT.replace("{text}", raw_text))
            else:
                contents.append(PARSE_PROMPT_IMAGE)
        else:
            contents = PARSE_PROMPT.replace("{text}", raw_text)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config={
                "response_mime_type": "application/json",
                "response_schema": ParsedQuestionList,
            },
        )
        result = ParsedQuestionList.model_validate_json(response.text)
        questions = [q.model_dump() for q in result.questions]
    except Exception as e:
        logger.exception("Gemini API 파싱 오류")
        return JsonResponse({"questions": [], "error": f"AI 분석 중 오류: {str(e)}"})

    if not questions:
        return JsonResponse({"questions": [], "error": "문제를 인식하지 못했습니다. 형식을 확인하세요."})
    return JsonResponse({"questions": questions, "count": len(questions)})


@login_required
@require_POST
def api_bulk_create(request, pk):
    """파싱된 문제를 일괄 등록"""
    subject = get_object_or_404(Subject, pk=pk)
    data = json.loads(request.body)
    target_year = int(data.get("year", 2025))
    items = data.get("questions", [])
    if not items:
        return JsonResponse({"error": "등록할 문제가 없습니다."}, status=400)

    last_num = (
        Question.objects.filter(subject=subject, year=target_year)
        .order_by("-number")
        .values_list("number", flat=True)
        .first()
    ) or 0

    created = 0
    for item in items:
        last_num += 1
        Question.objects.create(
            subject=subject,
            year=target_year,
            number=last_num,
            text=item.get("text", ""),
            choice_1=item.get("choice_1", "-"),
            choice_2=item.get("choice_2", "-"),
            choice_3=item.get("choice_3", "-"),
            choice_4=item.get("choice_4", "-"),
            answer=item.get("answer", "0"),
        )
        created += 1

    return JsonResponse({"ok": True, "created": created, "year": target_year})


@login_required
@require_POST
def latest_question_clone(request, pk):
    """기존 기출 문제를 최신기출로 복사 등록"""
    subject = get_object_or_404(Subject, pk=pk)
    source_id = int(request.POST.get("source_id", 0))
    target_year = int(request.POST.get("target_year", 2025))
    source = get_object_or_404(Question, pk=source_id)

    last_num = (
        Question.objects.filter(subject=subject, year=target_year)
        .order_by("-number")
        .values_list("number", flat=True)
        .first()
    ) or 0

    Question.objects.create(
        subject=subject,
        year=target_year,
        number=last_num + 1,
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
        created_by_name=request.user.first_name or request.user.username,
    )
    sub = request.POST.get("sub", "existing")
    return redirect(f"/subjects/{subject.pk}/?tab=latest&last_year={target_year}&sub={sub}")


@login_required
def notes_study(request, pk):
    """쪽집게 노트 관련 문제 학습모드"""
    subject = get_object_or_404(Subject, pk=pk)
    refs = request.GET.getlist("ref")
    if not refs:
        return redirect("main:subject_detail", pk=pk)

    q_filters = Q()
    for ref in refs:
        parts = ref.split("-")
        if len(parts) == 2:
            year, number = int(parts[0]), int(parts[1])
            q_filters |= Q(subject=subject, year=year, number=number)
        elif len(parts) == 3:
            # YYYY-기말-N 형식
            year, number = int(parts[0]), int(parts[2])
            q_filters |= Q(subject=subject, year=year, number=number)

    questions = list(
        Question.objects.filter(q_filters).order_by("year", "number")
    )

    # 관련 절 제목 및 절 번호 찾기
    section_title = ""
    section_id = ""
    note_order = None
    ref_set = set(refs)
    for note in StudyNote.objects.filter(subject=subject).order_by("order"):
        lines = note.content.split('\n')
        current_section = ""
        current_sec_num = ""
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('### ') and not stripped.startswith('### 핵심'):
                current_section = stripped[4:]
                sec_m = re.match(r'(\d+\.\d+)', current_section)
                current_sec_num = sec_m.group(1) if sec_m else ""
            if '**관련 문제**' in stripped:
                found_refs = set(re.findall(r'\((\d{4}-\d+)\)', stripped))
                if found_refs & ref_set:
                    section_title = current_section
                    section_id = current_sec_num
                    note_order = note.order
                    break
        if section_title:
            break

    return render(request, "exam/study_mode.html", {
        "subject": subject,
        "questions": questions,
        "year": "쪽집게 노트",
        "is_notes_study": True,
        "section_title": section_title,
        "section_id": section_id,
        "note_order": note_order,
    })


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


@login_required
@user_passes_test(staff_required)
def member_manage(request):
    members = (
        User.objects.annotate(login_count=Count("login_logs"))
        .all()
        .order_by("-date_joined")
    )

    # 사용시간: 세션별 (첫 풀이 ~ 마지막 풀이) 합산
    from django.db.models import ExpressionWrapper, DurationField
    from datetime import timedelta

    usage_map = {}
    for m in members:
        total = timedelta()
        # exam 앱 세션
        exam_sessions = (
            Attempt.objects.filter(user=m)
            .exclude(session_id="")
            .values("session_id")
            .annotate(start=Min("created_at"), end=Max("created_at"))
        )
        for s in exam_sessions:
            dur = s["end"] - s["start"]
            total += dur if dur > timedelta() else timedelta(minutes=1)

        # gisa 앱 세션
        gisa_sessions = (
            GisaAttempt.objects.filter(user=m)
            .exclude(session_id="")
            .values("session_id")
            .annotate(start=Min("created_at"), end=Max("created_at"))
        )
        for s in gisa_sessions:
            dur = s["end"] - s["start"]
            total += dur if dur > timedelta() else timedelta(minutes=1)

        usage_map[m.pk] = total

    # 최종작업: exam/gisa 각각의 마지막 풀이 기록
    from itertools import chain

    last_exam = dict(
        Attempt.objects.values("user_id")
        .annotate(last=Max("created_at"))
        .values_list("user_id", "last")
    )
    last_gisa = dict(
        GisaAttempt.objects.values("user_id")
        .annotate(last=Max("created_at"))
        .values_list("user_id", "last")
    )

    for m in members:
        td = usage_map.get(m.pk, timedelta())
        total_sec = int(td.total_seconds())
        m.usage_seconds = total_sec          # 표 정렬용 (표시값은 "3시간 20분")
        if total_sec < 60:
            m.usage_display = "-"
        else:
            hours, rem = divmod(total_sec, 3600)
            minutes = rem // 60
            if hours > 0:
                m.usage_display = f"{hours}시간 {minutes}분"
            else:
                m.usage_display = f"{minutes}분"

        # 최종작업 & 작업시간
        e_last = last_exam.get(m.pk)
        g_last = last_gisa.get(m.pk)
        if e_last and g_last:
            m.last_activity_at = max(e_last, g_last)
            m.last_activity_source = "기사" if g_last > e_last else "방송대"
        elif g_last:
            m.last_activity_at = g_last
            m.last_activity_source = "기사"
        elif e_last:
            m.last_activity_at = e_last
            m.last_activity_source = "방송대"
        else:
            m.last_activity_at = None
            m.last_activity_source = None

        # 최종작업의 mode 조회
        m.last_activity_mode = None
        if m.last_activity_at:
            if m.last_activity_source == "기사":
                rec = GisaAttempt.objects.filter(user=m, created_at=m.last_activity_at).first()
            else:
                rec = Attempt.objects.filter(user=m, created_at=m.last_activity_at).first()
            if rec:
                mode_map = {"exam": "기출풀이", "mock": "모의고사", "wrong_retry": "오답재풀이"}
                m.last_activity_mode = mode_map.get(rec.mode, rec.mode)

    # 이메일 수신 여부 + 비밀번호 변경 시각
    from accounts.models import UserProfile
    profiles = {p.user_id: p for p in UserProfile.objects.all()}
    for m in members:
        prof = profiles.get(m.pk)
        m.receive_email = prof.receive_email if prof else True
        m.password_changed_at = prof.password_changed_at if prof else None
        m.cohort = prof.cohort if prof else None

    newest_cohort = max((m.cohort for m in members if m.cohort), default=None)
    for m in members:
        m.cohort_color = _cohort_color(m.cohort, newest_cohort)

    # 회원별 최근 메일 열람 시각
    from bbs.models import NoticeOpenLog
    last_opens = {
        r["user_id"]: r["last"]
        for r in NoticeOpenLog.objects.values("user_id").annotate(last=Max("opened_at"))
    }
    for m in members:
        m.last_mail_open = last_opens.get(m.pk)

    # 회원별 PDF 자료 열람 (최근 시각 + 총 횟수)
    from .models import MaterialOpenLog
    pdf_stats = {
        r["user_id"]: (r["last"], r["c"])
        for r in MaterialOpenLog.objects.values("user_id").annotate(last=Max("opened_at"), c=Count("id"))
    }
    for m in members:
        last, cnt = pdf_stats.get(m.pk, (None, 0))
        m.last_pdf_open = last
        m.pdf_open_count = cnt

    # 승인 대기 신청자 (is_active=False AND profile.is_approved=False)
    pending_members = (
        User.objects.filter(is_active=False, profile__is_approved=False)
        .select_related("profile")
        .order_by("-date_joined")
    )

    return render(request, "main/member_manage.html", {
        "members": members,
        "pending_members": pending_members,
        "active_tab": request.GET.get("tab", "members"),
    })


# 기수 배지 색 — 최신 기수일수록 진하게. 회원 목록에서 기수를 눈으로
# 훑을 때 세대가 한눈에 갈리도록, 숫자를 읽지 않아도 구분되게 한다.
_COHORT_TONES = [
    ("#1b4332", "#ffffff", "#1b4332"),   # 최신
    ("#2d6a4f", "#ffffff", "#2d6a4f"),
    ("#40806b", "#ffffff", "#40806b"),
    ("#74a892", "#ffffff", "#74a892"),
    ("#dbe9e0", "#1f4d3a", "#bcd6c7"),
    ("#eef3ef", "#40624f", "#d5e2da"),
    ("#f6f7f6", "#7d8f83", "#e2e6e3"),   # 가장 오래된 기수
]


def _cohort_color(cohort, newest):
    """기수 → (배경, 글자, 테두리). 최신 기수부터 순서대로 옅어진다."""
    if not cohort or not newest:
        return None
    gap = newest - cohort
    idx = min(gap, len(_COHORT_TONES) - 1)
    return _COHORT_TONES[idx]


def _usage_range(period, start_raw, end_raw):
    """기간 선택값 → (시작, 끝, 라벨). 끝은 그날 24시까지 포함한다."""
    from django.utils import timezone as _tz

    now = _tz.localtime()
    today = now.date()
    if period == "today":
        return today, today, "오늘"
    if period == "7d":
        return today - timedelta(days=6), today, "최근 7일"
    if period == "month":
        return today.replace(day=1), today, f"{today.month}월"
    if period == "custom":
        try:
            s = date.fromisoformat(start_raw)
            e = date.fromisoformat(end_raw)
        except (TypeError, ValueError):
            return today - timedelta(days=6), today, "최근 7일"
        if s > e:
            s, e = e, s
        return s, e, f"{s.isoformat()} ~ {e.isoformat()}"
    if period == "all":
        return None, None, "전체"
    return today - timedelta(days=6), today, "최근 7일"


@login_required
@user_passes_test(staff_required)
def usage_stats(request):
    """사용현황 — 기간을 골라 회원별 활동을 본다.

    풀이 수만 보면 학습모드로 답을 보며 넘긴 기록과 실제 시험 응시가
    한 덩어리가 된다. 그래서 모드별(학습/기출/모의/오답)로 나눠 센다.
    """
    from django.utils import timezone as _tz
    from accounts.models import UserProfile
    from gisa.models import GisaStudyLog
    from .models import MaterialOpenLog

    period = request.GET.get("period", "7d")
    start, end, label = _usage_range(
        period, request.GET.get("start"), request.GET.get("end")
    )

    # 방송대(exam 앱) / 기사(gisa 앱) 가르기. 한쪽만 고르면 정답률·세션·
    # 모드별 수치가 모두 그쪽 기준이 된다 — 두 시험은 성격이 달라 섞으면
    # 누가 무엇을 하고 있는지 흐려진다.
    app = request.GET.get("app", "")
    if app not in ("knou", "gisa"):
        app = ""
    sources = [(Attempt, "knou"), (GisaAttempt, "gisa")]
    if app:
        sources = [s for s in sources if s[1] == app]
    app_label = {"knou": "방송대", "gisa": "기사"}.get(app, "")

    def span(qs, field="created_at"):
        if start is None:
            return qs
        tz = _tz.get_current_timezone()
        lo = datetime.combine(start, time.min).replace(tzinfo=tz)
        hi = datetime.combine(end, time.max).replace(tzinfo=tz)
        return qs.filter(**{f"{field}__range": (lo, hi)})

    # 모드별 풀이 수 — exam 앱과 gisa 앱을 합산한다
    MODES = ("study", "exam", "mock", "wrong_retry")
    agg = {}

    def bump(uid, key, n):
        row = agg.setdefault(uid, {m: 0 for m in MODES})
        row.setdefault(key, 0)
        row[key] += n

    for model, tag in sources:
        rows = (
            span(model.objects.all())
            .values("user_id", "mode")
            .annotate(n=Count("id"), c=Count("id", filter=Q(is_correct=True)))
        )
        for r in rows:
            uid, mode = r["user_id"], (r["mode"] or "exam")
            bump(uid, mode if mode in MODES else "exam", r["n"])
            bump(uid, tag, r["n"])
            bump(uid, "solved", r["n"])
            bump(uid, "correct", r["c"])

    # 세션 수 (한 번 앉은 횟수)
    #
    # 사용시간은 내지 않는다 — 기사 앱은 제출 시점에 답안을 일괄 저장해
    # 한 세션의 모든 문항이 같은 created_at 을 가진다. (첫 풀이~마지막
    # 풀이)로 재면 늘 0초가 나오므로, 채워 넣으면 실제로 잰 값처럼
    # 보이지만 근거가 없다. 대신 세션 수와 문항 수로 활동량을 본다.
    # values_list 로 짝을 뽑아 set 으로 센다 — values().distinct() 를 그대로
    # 순회하면 Meta.ordering 필드가 SELECT 에 끼어들어 중복 제거가 풀린다.
    for model, _tag in sources:
        pairs = set(
            span(model.objects.exclude(session_id=""))
            .values_list("user_id", "session_id")
        )
        for uid, _sid in pairs:
            bump(uid, "sessions", 1)

    # 기출학습 진도 기록·자료 열람·로그인
    if app != "knou":          # 진도기록은 기사 앱에만 있다
        for r in span(GisaStudyLog.objects.all()).values("user_id").annotate(
            n=Count("id")
        ):
            bump(r["user_id"], "studylog", r["n"])
    for r in span(MaterialOpenLog.objects.all(), "opened_at").values(
        "user_id"
    ).annotate(n=Count("id")):
        bump(r["user_id"], "pdf", r["n"])
    for r in span(LoginLog.objects.all(), "logged_in_at").values("user_id").annotate(
        n=Count("id")
    ):
        bump(r["user_id"], "login", r["n"])

    # 마지막 활동 시각 (기간 안에서)
    last = {}
    act_models = [(m, "created_at") for m, _ in sources]
    if app != "knou":
        act_models.append((GisaStudyLog, "created_at"))
    act_models.append((LoginLog, "logged_in_at"))
    for model, field in act_models:
        for r in span(model.objects.all(), field).values("user_id").annotate(
            m=Max(field)
        ):
            cur = last.get(r["user_id"])
            if cur is None or (r["m"] and r["m"] > cur):
                last[r["user_id"]] = r["m"]

    cohorts = {p.user_id: p.cohort for p in UserProfile.objects.all()}
    newest_cohort = max((c for c in cohorts.values() if c), default=None)
    rows = []
    for u in User.objects.all():
        a = agg.get(u.pk)
        if not a:
            continue
        solved = a.get("solved", 0)
        # 앱을 골랐으면 그 앱을 실제로 푼 회원만 남긴다 — 로그인 기록은
        # 앱을 가리지 않으므로, 그냥 두면 방송대를 골라도 로그인만 한
        # 회원까지 표에 남아 활동 회원 수가 부풀려진다.
        if app and not solved:
            continue
        rows.append({
            "pk": u.pk,
            "name": (u.first_name or u.username),
            "cohort": cohorts.get(u.pk),
            "cohort_color": _cohort_color(cohorts.get(u.pk), newest_cohort),
            "solved": solved,
            "correct": a.get("correct", 0),
            "rate": round(a.get("correct", 0) / solved * 100) if solved else None,
            "knou": a.get("knou", 0),
            "gisa": a.get("gisa", 0),
            "study": a.get("study", 0),
            "exam": a.get("exam", 0),
            "mock": a.get("mock", 0),
            "wrong": a.get("wrong_retry", 0),
            "sessions": a.get("sessions", 0),
            "studylog": a.get("studylog", 0),
            "pdf": a.get("pdf", 0),
            "login": a.get("login", 0),
            "last": last.get(u.pk),
        })
    rows.sort(key=lambda r: (-r["solved"], -r["sessions"]))

    total = {
        k: sum(r[k] for r in rows)
        for k in ("solved", "correct", "knou", "gisa", "study", "exam",
                  "mock", "wrong", "sessions", "studylog", "pdf", "login")
    }
    total["users"] = len(rows)
    total["rate"] = (
        round(total["correct"] / total["solved"] * 100) if total["solved"] else None
    )

    return render(request, "main/usage_stats.html", {
        "rows": rows,
        "total": total,
        # 막대는 회원끼리 견줘 봐야 뜻이 있으므로 최다 풀이자를 기준으로 잡는다
        "max_solved": max((r["solved"] for r in rows), default=1) or 1,
        "period": period,
        "label": label,
        "app": app,
        "app_label": app_label,
        "start": start.isoformat() if start else "",
        "end": end.isoformat() if end else "",
    })


@login_required
@user_passes_test(staff_required)
def restore_stats(request):
    """복원통계 페이지"""
    restore_total = (
        Question.objects.filter(year__gte=2020).count()
        + GisaQuestion.objects.filter(exam__exam_type="최신").count()
    )
    return render(request, "main/restore_stats.html", {
        "restore_total": restore_total,
    })


@login_required
@user_passes_test(staff_required)
def restore_stats_api(request):
    """복원통계 API: 페이지네이션된 JSON 반환"""
    page = int(request.GET.get("page", 1))
    per_page = 20

    exam_stats = (
        Question.objects.filter(year__gte=2020)
        .annotate(reg_date=TruncDate("created_at"))
        .values("created_by_name", "subject__name", "reg_date")
        .annotate(cnt=Count("pk"))
    )
    gisa_stats = (
        GisaQuestion.objects.filter(exam__exam_type="최신")
        .annotate(reg_date=TruncDate("created_at"))
        .values("created_by_name", "subject__name", "exam__certification__name", "reg_date")
        .annotate(cnt=Count("pk"))
    )

    # 과목별 전체 문항수
    exam_totals = dict(
        Question.objects.filter(year__gte=2020)
        .values_list("subject__name")
        .annotate(cnt=Count("pk"))
    )
    gisa_totals = {}
    for row in (
        GisaQuestion.objects.filter(exam__exam_type="최신")
        .values("exam__certification__name", "subject__name")
        .annotate(cnt=Count("pk"))
    ):
        cert_name = row["exam__certification__name"]
        key = f"[{cert_name}{'' if '기사' in cert_name else '기사'}] {row['subject__name']}"
        gisa_totals[key] = row["cnt"]

    rows = []
    for row in exam_stats:
        subj = row["subject__name"]
        rows.append({
            "name": row["created_by_name"] or "미확인",
            "subject": subj,
            "count": row["cnt"],
            "total": exam_totals.get(subj, row["cnt"]),
            "reg_date": row["reg_date"],
        })
    for row in gisa_stats:
        cert_name = row["exam__certification__name"]
        subj = f"[{cert_name}{'' if '기사' in cert_name else '기사'}] {row['subject__name']}"
        rows.append({
            "name": row["created_by_name"] or "미확인",
            "subject": subj,
            "count": row["cnt"],
            "total": gisa_totals.get(subj, row["cnt"]),
            "reg_date": row["reg_date"],
        })
    rows.sort(key=lambda x: (x["reg_date"] or date.min,), reverse=True)

    start = (page - 1) * per_page
    end = start + per_page
    page_rows = rows[start:end]

    return JsonResponse({
        "rows": [
            {
                "name": r["name"],
                "subject": r["subject"],
                "count": r["count"],
                "total": r["total"],
                "reg_date": r["reg_date"].strftime("%Y.%m.%d") if r["reg_date"] else "-",
            }
            for r in page_rows
        ],
        "has_next": end < len(rows),
    })


@login_required
@user_passes_test(staff_required)
@require_POST
def member_toggle(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    field = request.POST.get("field", "")
    if field not in ("is_staff", "is_active", "receive_email"):
        return JsonResponse({"error": "invalid field"}, status=400)
    if field in ("is_staff", "is_active") and target_user == request.user:
        return JsonResponse({"error": "자기 자신의 권한은 변경할 수 없습니다."}, status=400)
    if field == "receive_email":
        from accounts.models import UserProfile
        profile, _ = UserProfile.objects.get_or_create(user=target_user)
        profile.receive_email = not profile.receive_email
        profile.save(update_fields=["receive_email"])
        return JsonResponse({"ok": True, "field": field, "value": profile.receive_email})
    new_val = not getattr(target_user, field)
    setattr(target_user, field, new_val)
    target_user.save(update_fields=[field])
    return JsonResponse({"ok": True, "field": field, "value": new_val})


@login_required
@user_passes_test(staff_required)
@require_POST
def member_cohort(request, pk):
    """회원 기수 저장. 빈 값으로 보내면 미지정으로 되돌린다."""
    from accounts.models import UserProfile

    target_user = get_object_or_404(User, pk=pk)
    raw = (request.POST.get("cohort") or "").strip()
    if raw == "":
        value = None
    else:
        try:
            value = int(raw)
        except ValueError:
            return JsonResponse({"error": "기수는 숫자로 입력하세요."}, status=400)
        if not 1 <= value <= 99:
            return JsonResponse({"error": "기수는 1~99 사이여야 합니다."}, status=400)

    profile, _ = UserProfile.objects.get_or_create(user=target_user)
    profile.cohort = value
    profile.save(update_fields=["cohort"])
    return JsonResponse({"ok": True, "cohort": value})


@login_required
@user_passes_test(staff_required)
@require_POST
def member_delete(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    if target_user == request.user:
        return JsonResponse({"error": "자기 자신은 삭제할 수 없습니다."}, status=400)
    if target_user.is_superuser:
        return JsonResponse({"error": "슈퍼유저는 삭제할 수 없습니다."}, status=400)
    username = target_user.username
    target_user.delete()
    return JsonResponse({"ok": True, "username": username})


@login_required
@user_passes_test(staff_required)
@require_POST
def member_approve(request, pk):
    """가입 신청 승인. 승인 시 이메일 인증 토큰 생성 + 인증 메일 발송."""
    from accounts.models import UserProfile, EmailVerificationToken
    from accounts.views import _send_verification_email
    from django.utils import timezone as _tz

    target_user = get_object_or_404(User, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=target_user)
    if profile.is_approved:
        return JsonResponse({"error": "이미 승인된 회원입니다."}, status=400)

    profile.is_approved = True
    profile.approved_at = _tz.now()
    profile.approved_by = request.user
    profile.save(update_fields=["is_approved", "approved_at", "approved_by"])

    # 토큰 발급 + 인증 메일 발송
    token, _ = EmailVerificationToken.objects.get_or_create(user=target_user)
    token.refresh()
    try:
        _send_verification_email(request, target_user, token)
    except Exception as e:
        return JsonResponse({"ok": True, "username": target_user.username,
                             "warning": f"승인은 됐으나 인증 메일 발송 실패: {e}"})
    return JsonResponse({"ok": True, "username": target_user.username})


@login_required
@user_passes_test(staff_required)
@require_POST
def member_reject(request, pk):
    """가입 신청 거부 = 즉시 삭제."""
    target_user = get_object_or_404(User, pk=pk)
    if target_user == request.user:
        return JsonResponse({"error": "자기 자신은 거부할 수 없습니다."}, status=400)
    if target_user.is_superuser:
        return JsonResponse({"error": "슈퍼유저는 거부할 수 없습니다."}, status=400)
    username = target_user.username
    target_user.delete()
    return JsonResponse({"ok": True, "username": username})


# ===== 교과목 자료 (PDF) 관리 =====

@login_required
@user_passes_test(staff_required)
def material_open_logs(request, pk):
    """자료별 PDF 열람·인쇄 로그 상세 (스태프 전용)"""
    from .models import MaterialOpenLog
    from django.db.models import Q
    material = get_object_or_404(SubjectMaterial.objects.select_related('subject'), pk=pk)
    # 사용자별 열람/인쇄 통계
    by_user = (
        MaterialOpenLog.objects.filter(material=material)
        .values('user_id', 'user__username', 'user__first_name')
        .annotate(
            views=Count('id', filter=Q(action='view')),
            prints=Count('id', filter=Q(action='print')),
            last=Max('opened_at'),
            first=Min('opened_at'),
        )
        .order_by('-last')
    )
    # 최근 30건 상세 로그
    recent_logs = (
        MaterialOpenLog.objects.filter(material=material)
        .select_related('user')
        .order_by('-opened_at')[:30]
    )
    total_view = MaterialOpenLog.objects.filter(material=material, action='view').count()
    total_print = MaterialOpenLog.objects.filter(material=material, action='print').count()
    return render(request, 'main/material_open_logs.html', {
        'material': material,
        'by_user': by_user,
        'recent_logs': recent_logs,
        'total_view': total_view,
        'total_print': total_print,
    })


@login_required
@user_passes_test(staff_required)
def material_manage(request):
    subjects = Subject.objects.all().order_by('grade', 'semester', 'name')
    selected_id = request.GET.get('subject')
    selected_subject = None
    materials = SubjectMaterial.objects.none()
    if selected_id:
        try:
            selected_subject = Subject.objects.get(pk=int(selected_id))
            materials = SubjectMaterial.objects.filter(subject=selected_subject).order_by('-created_at')
        except (Subject.DoesNotExist, ValueError):
            pass
    all_materials = SubjectMaterial.objects.select_related('subject').order_by('-created_at')[:100]

    # 자료별 열람·인쇄 통계
    from .models import MaterialOpenLog
    stats = {}
    for r in MaterialOpenLog.objects.values('material_id', 'action').annotate(c=Count('id'), uniq=Count('user_id', distinct=True)):
        mid = r['material_id']
        stats.setdefault(mid, {'view_c': 0, 'view_u': 0, 'print_c': 0, 'print_u': 0})
        if r['action'] == 'view':
            stats[mid]['view_c'] = r['c']
            stats[mid]['view_u'] = r['uniq']
        elif r['action'] == 'print':
            stats[mid]['print_c'] = r['c']
            stats[mid]['print_u'] = r['uniq']

    def _attach(mat_list):
        for m in mat_list:
            s = stats.get(m.pk, {'view_c': 0, 'view_u': 0, 'print_c': 0, 'print_u': 0})
            m.view_count = s['view_c']
            m.unique_viewers = s['view_u']
            m.print_count = s['print_c']
            m.unique_printers = s['print_u']

    _attach(materials)
    _attach(all_materials)

    return render(request, 'main/material_manage.html', {
        'subjects': subjects,
        'selected_subject': selected_subject,
        'materials': materials,
        'all_materials': all_materials,
    })


@login_required
@user_passes_test(staff_required)
@require_POST
def material_upload(request):
    subject_id = request.POST.get('subject')
    title = request.POST.get('title', '').strip()
    pdf_file = request.FILES.get('file')
    if not subject_id or not pdf_file:
        from django.contrib import messages
        messages.error(request, '과목과 파일을 모두 선택해주세요.')
        return redirect('main:material_manage')
    subject = get_object_or_404(Subject, pk=int(subject_id))
    if not pdf_file.name.lower().endswith('.pdf'):
        from django.contrib import messages
        messages.error(request, 'PDF 파일만 업로드할 수 있습니다.')
        return redirect(f'/manage/materials/?subject={subject.pk}')
    if not title:
        title = pdf_file.name.rsplit('.', 1)[0]
    SubjectMaterial.objects.create(
        subject=subject,
        title=title,
        file=pdf_file,
        uploaded_by=request.user,
    )
    return redirect(f'/manage/materials/?subject={subject.pk}')


@login_required
@user_passes_test(staff_required)
@require_POST
def material_delete(request, pk):
    material = get_object_or_404(SubjectMaterial, pk=pk)
    subject_id = material.subject_id
    if material.file:
        material.file.delete(save=False)
    material.delete()
    return redirect(f'/manage/materials/?subject={subject_id}')


@login_required
def material_list(request, pk):
    """과목별 자료 목록 (사용자 모달용 JSON)"""
    subject = get_object_or_404(Subject, pk=pk)
    materials = SubjectMaterial.objects.filter(subject=subject).order_by('-created_at')
    data = [{
        'id': m.id,
        'title': m.title,
        'created_at': m.created_at.strftime('%Y-%m-%d'),
    } for m in materials]
    return JsonResponse({'materials': data, 'subject_name': subject.name})


@login_required
@xframe_options_sameorigin
def material_stream(request, pk, material_pk):
    """PDF 파일 inline 스트리밍 (다운로드 차단 헤더)"""
    from django.http import FileResponse, Http404
    import os
    subject = get_object_or_404(Subject, pk=pk)
    material = get_object_or_404(SubjectMaterial, pk=material_pk, subject=subject)
    if not material.file:
        raise Http404
    try:
        path = material.file.path
        if not os.path.exists(path):
            raise Http404
        f = open(path, 'rb')
    except (FileNotFoundError, ValueError):
        raise Http404
    response = FileResponse(f, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="material_{material.pk}.pdf"'
    response['Content-Length'] = os.path.getsize(path)
    # Range 요청 비활성화 - Django FileResponse는 byte range를 제대로 못 다루므로
    # PDF.js가 부분 다운로드 시도하지 않도록 명시적으로 none 응답
    response['Accept-Ranges'] = 'none'
    response['X-Content-Type-Options'] = 'nosniff'
    response['Cache-Control'] = 'private, no-store'
    return response


@login_required
@xframe_options_sameorigin
def material_view(request, pk, material_pk):
    """PDF 뷰어 페이지 (다운로드 차단 UI). 진입 시 열람 로그 저장."""
    subject = get_object_or_404(Subject, pk=pk)
    material = get_object_or_404(SubjectMaterial, pk=material_pk, subject=subject)

    # 열람 로그 저장 (실패해도 PDF 보기는 계속)
    try:
        from .models import MaterialOpenLog
        ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() \
            or request.META.get('REMOTE_ADDR')
        ua = request.META.get('HTTP_USER_AGENT', '')[:300]
        MaterialOpenLog.objects.create(
            material=material,
            user=request.user,
            action='view',
            ip=ip or None,
            user_agent=ua,
        )
    except Exception:
        pass

    return render(request, 'main/material_view.html', {
        'subject': subject,
        'material': material,
    })


@login_required
@require_POST
def material_print_log(request, pk, material_pk):
    """PDF 인쇄 버튼 클릭 시 기록 (AJAX)"""
    from .models import MaterialOpenLog
    subject = get_object_or_404(Subject, pk=pk)
    material = get_object_or_404(SubjectMaterial, pk=material_pk, subject=subject)
    try:
        ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() \
            or request.META.get('REMOTE_ADDR')
        ua = request.META.get('HTTP_USER_AGENT', '')[:300]
        MaterialOpenLog.objects.create(
            material=material,
            user=request.user,
            action='print',
            ip=ip or None,
            user_agent=ua,
        )
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)
