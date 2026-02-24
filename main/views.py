from collections import OrderedDict
from datetime import date

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
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
from .models import FavoriteSubject, Subject

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

    for m in members:
        td = usage_map.get(m.pk, timedelta())
        total_sec = int(td.total_seconds())
        if total_sec < 60:
            m.usage_display = "-"
        else:
            hours, rem = divmod(total_sec, 3600)
            minutes = rem // 60
            if hours > 0:
                m.usage_display = f"{hours}시간 {minutes}분"
            else:
                m.usage_display = f"{minutes}분"

    return render(request, "main/member_manage.html", {"members": members})


@login_required
@user_passes_test(staff_required)
def restore_stats(request):
    """복원통계: 최신기출 등록자별 과목/문항수/등록일"""
    exam_stats = (
        Question.objects.filter(year__gte=2020)
        .annotate(reg_date=TruncDate("created_at"))
        .values("created_by_name", "subject__name", "reg_date")
        .annotate(cnt=Count("pk"))
        .order_by("-reg_date")
    )
    gisa_stats = (
        GisaQuestion.objects.filter(exam__exam_type="최신")
        .annotate(reg_date=TruncDate("created_at"))
        .values("created_by_name", "subject__name", "exam__certification__name", "reg_date")
        .annotate(cnt=Count("pk"))
        .order_by("-reg_date")
    )

    restore_rows = []
    for row in exam_stats:
        restore_rows.append({
            "name": row["created_by_name"] or "미확인",
            "subject": row["subject__name"],
            "count": row["cnt"],
            "reg_date": row["reg_date"],
        })
    for row in gisa_stats:
        cert_name = row["exam__certification__name"]
        restore_rows.append({
            "name": row["created_by_name"] or "미확인",
            "subject": f"[{cert_name}{'' if '기사' in cert_name else '기사'}] {row['subject__name']}",
            "count": row["cnt"],
            "reg_date": row["reg_date"],
        })
    restore_rows.sort(key=lambda x: (x["reg_date"] or date.min,), reverse=True)
    restore_total = sum(r["count"] for r in restore_rows)

    return render(request, "main/restore_stats.html", {
        "restore_rows": restore_rows,
        "restore_total": restore_total,
    })


@login_required
@user_passes_test(staff_required)
@require_POST
def member_toggle(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    field = request.POST.get("field", "")
    if field not in ("is_staff", "is_active"):
        return JsonResponse({"error": "invalid field"}, status=400)
    if target_user == request.user:
        return JsonResponse({"error": "자기 자신의 권한은 변경할 수 없습니다."}, status=400)
    new_val = not getattr(target_user, field)
    setattr(target_user, field, new_val)
    target_user.save(update_fields=[field])
    return JsonResponse({"ok": True, "field": field, "value": new_val})
