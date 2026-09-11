from collections import OrderedDict
from datetime import date, datetime, time, timedelta
from html import escape, unescape

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.files.base import ContentFile
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST

import json
import logging
import os
import uuid
import markdown
import re

from django.conf import settings
from django.utils import timezone
from django.db.models import Case, Count, F, IntegerField, Max, Min, Q, Sum, Value, When
from django.db.models.functions import TruncDate

from django.contrib.auth.models import User
from google import genai
from pydantic import BaseModel, Field

from accounts.models import LoginLog
import random

from exam.models import Attempt, Question, StudyNote, WeedCard, WeedQuizAttempt
from gisa.models import GisaAttempt, GisaQuestion
from .forms import SubjectForm
from .models import FavoriteSubject, QnaQuestion, Subject, SubjectMaterial

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
        # 이미지: ![설명](url) → <img>. 확대 버튼을 모서리에 붙이려면 감싸는 칸이 있어야 한다
        body = re.sub(
            r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)",
            r'<span class="note-img-wrap"><img class="note-img" src="\2" alt="\1">'
            r'<button type="button" class="note-img-zoom" title="크게 보기" '
            r'onclick="noteZoom(this)">+</button></span>', body)
        # WYSIWYG 편집기가 넣는 마크다운 이스케이프(\~ \_ \* 등) 제거. 표 구분자 \| 는 보존
        body = body.replace("\\|", "&#124;")
        body = re.sub(r"\\([~_*#\[\]()!<>\-.`])", r"\1", body)

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
            # 이미지만 있는 줄은 <p> 로 감싸지 않는다 — <p> 의 양끝 정렬·줄높이가
            # 이미지 위 확대 버튼의 자리를 흐트러뜨린다
            if re.fullmatch(r'\s*(<span class="note-img-wrap">.*?</span>\s*)+', joined, re.S):
                html_lines.append(joined)
            else:
                html_lines.append(f"<p>{joined}</p>")
            para_lines = []

        for raw_line in body.split("\n"):
            line = raw_line.strip()
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
            elif re.match(r"^ {2,4}[-*] ", raw_line):
                # 들여쓴 하위 불렛 (상위 불렛 검사보다 먼저 봐야 한다)
                _flush_para()
                lc = raw_line.strip()[2:]
                lc = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", lc)
                lc = re.sub(r"\*(.+?)\*", r"<em>\1</em>", lc)
                html_lines.append(f"<li class='sub-item'>{lc}</li>")
            elif line.startswith("- ") or line.startswith("* "):
                _flush_para()
                lc = line[2:]
                lc = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", lc)
                lc = re.sub(r"\*(.+?)\*", r"<em>\1</em>", lc)
                html_lines.append(f"<li>{lc}</li>")
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


def _site_totals():
    """홈 대시보드용 전체 누적 사용현황 (사용현황 페이지의 '전체' 합계와 같은 정의).

    회원 한 명씩 돌지 않고 집계 쿼리로 센다. 10분 캐시 — 홈은 누구나 여는 화면이다.
    """
    from django.core.cache import cache
    from gisa.models import GisaStudyLog
    from .models import MaterialOpenLog

    hit = cache.get("site_totals")
    if hit:
        return hit

    users = set()
    for model in (Attempt, GisaAttempt, LoginLog, GisaStudyLog, MaterialOpenLog):
        users |= set(model.objects.order_by().values_list("user_id", flat=True).distinct())
    users.discard(None)

    solved = correct = study = sessions = 0
    for model in (Attempt, GisaAttempt):
        solved += model.objects.count()
        correct += model.objects.filter(is_correct=True).count()
        study += model.objects.filter(mode="study").count()
        # 세션 = (회원, session_id) 짝의 수. order_by() 로 Meta.ordering 을 지워야
        # distinct 가 제대로 먹는다
        sessions += (model.objects.exclude(session_id="").order_by()
                     .values("user_id", "session_id").distinct().count())

    totals = {
        "users": len(users),
        "solved": solved,
        "rate": round(correct / solved * 100) if solved else None,
        "sessions": sessions,
        "study": study,
        "login": LoginLog.objects.count(),
    }
    cache.set("site_totals", totals, 600)
    return totals


def index(request):
    from bbs.models import Notice

    latest_notices = Notice.objects.all()[:5]
    return render(request, "main/index.html", {
        "latest_notices": latest_notices,
        "totals": _site_totals(),
    })


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
    # 학습/풀이 탭: 2020 이전만. 다만 2020 이전 문항이 하나도 없는 과목
    # (잡초방제학처럼 2023년 이후 기출만 있는 경우)은 전체 연도를 쓴다.
    base_qs = Question.objects.filter(subject=subject)
    if base_qs.filter(year__lt=2020).exists():
        base_qs = base_qs.filter(year__lt=2020)
    years = (
        base_qs.values_list("year", flat=True)
        .distinct()
        .order_by("-year")
    )
    year_cards = []
    for year in years:
        count = Question.objects.filter(subject=subject, year=year).count()
        year_cards.append({"year": year, "count": count})

    total_questions = base_qs.count()

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
        # 관리자 편집용: 파싱된 장 ↔ StudyNote 레코드 연결 (제목 일치 → 순서 일치)
        if request.user.is_staff and note_chapters:
            notes_list = list(notes_qs)
            by_title = {n.title.strip(): n for n in notes_list}
            for idx, ch in enumerate(note_chapters):
                note = by_title.get(ch["title"].strip())
                if note is None and len(notes_list) == len(note_chapters):
                    note = notes_list[idx]
                if note is not None:
                    ch["note_pk"] = note.pk
                    ch["note_title"] = note.title
                    ch["note_content"] = note.content

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

    # 잡초 동정 퀴즈 (카드가 있는 과목만 탭이 보인다)
    weed_count = WeedCard.objects.filter(subject=subject).count()
    weed_stats = None
    if weed_count:
        my = WeedQuizAttempt.objects.filter(user=request.user, card__subject=subject)
        answered = my.values("card").distinct().count()
        total_try = my.count()
        wrong_ids = _weed_latest_wrong_ids(request.user, subject)
        weed_stats = {
            "answered": answered,
            "tries": total_try,
            "correct_rate": round(my.filter(is_correct=True).count() / total_try * 100) if total_try else 0,
            "wrong": len(wrong_ids),
            "freq": WeedCard.objects.filter(subject=subject, exam_count__gt=0).count(),
        }

    # 쪽집게 노트 절 ↔ 질의응답 연결: 절 번호별 질문 목록 (노트 탭에서 절 아래에 펼친다)
    qna_by_sec = {}
    if active_tab == "notes":
        # 절 아래 질문은 물어본 차례대로 — 새 질문이 목록 끝에 붙는다
        for qq in (QnaQuestion.objects.filter(subject=subject).exclude(note_sec="")
                   .exclude(answer="").select_related("user").order_by("created_at")):
            qna_by_sec.setdefault(qq.note_sec, []).append({
                "pk": qq.pk, "title": qq.title, "answer": qq.answer,
                "who": qq.user.first_name or qq.user.username,
                "when": timezone.localtime(qq.created_at).strftime("%m.%d"),
                "mine": qq.user_id == request.user.id,
            })

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
            "qna_by_sec_json": json.dumps(qna_by_sec, ensure_ascii=False),
            "weed_count": weed_count,
            "weed_stats": weed_stats,
            # 질의응답 탭 — 그 과목 질문만 보여 준다
            "qna_items": QnaQuestion.objects.filter(
                subject=subject).select_related("user")[:15],
            "qna_count": QnaQuestion.objects.filter(subject=subject).count(),
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
def api_note_questions(request, pk):
    """쪽집게 노트의 관련 문제를 탭 안에 펼쳐 보이기 위한 JSON.
    ?ref=YYYY-N&ref=... (notes_study 와 같은 형식)"""
    subject = get_object_or_404(Subject, pk=pk)
    q_filters = Q()
    order = []
    for ref in request.GET.getlist("ref")[:60]:
        parts = ref.split("-")
        try:
            if len(parts) == 2:
                year, number = int(parts[0]), int(parts[1])
            elif len(parts) == 3:
                year, number = int(parts[0]), int(parts[2])
            else:
                continue
        except ValueError:
            continue
        q_filters |= Q(year=year, number=number)
        order.append((year, number))
    if not order:
        return JsonResponse({"questions": []})
    found = {(q.year, q.number): q for q in Question.objects.filter(q_filters, subject=subject)}
    out = []
    for key in order:
        q = found.get(key)
        if not q:
            continue
        out.append({
            "pk": q.pk, "year": q.year, "number": q.number, "text": q.text,
            "choices": [q.choice_1, q.choice_2, q.choice_3, q.choice_4],
            "answer": q.answer, "explanation": q.explanation,
            "choice_exps": [q.choice_1_exp, q.choice_2_exp, q.choice_3_exp, q.choice_4_exp],
        })
    return JsonResponse({"questions": out})


## ══════════ 잡초 동정 퀴즈 (사진 → 이름 4지선다) ══════════ ##


def _weed_latest_wrong_ids(user, subject):
    """카드별 최신 풀이가 틀린 카드 id 집합."""
    latest = (WeedQuizAttempt.objects.filter(user=user, card__subject=subject)
              .values("card").annotate(latest_id=Max("id"))
              .values_list("latest_id", flat=True))
    return set(WeedQuizAttempt.objects.filter(pk__in=latest, is_correct=False)
               .values_list("card_id", flat=True))


def _weed_card_payload(c):
    return {
        "id": c.pk, "card_no": c.card_no, "name": c.name, "family": c.family,
        "life_form": c.life_form, "habitat": c.habitat, "features": c.features,
        "similar": c.similar, "control": c.control,
        "notes": [n for n in c.notes.split("\n") if n.strip()],
        "exam_count": c.exam_count,
        "a_img": c.a_image.url if c.a_image else "",
        "sketch": c.sketch_image.url if c.sketch_image else "",
    }


@login_required
def api_weed_quiz_next(request, pk):
    """다음 문제 한 건. ?mode=all|freq|wrong&seen=1,2,3
    - all: 전체에서 무작위 / freq: 출제된 카드만, 출제 횟수로 가중 / wrong: 최신 풀이가 틀린 카드만
    - seen 에 든 카드는 다시 내지 않는다 (한 바퀴 돌면 done)
    - 보기는 정답 + 같은 과에서 우선 고른 3개"""
    subject = get_object_or_404(Subject, pk=pk)
    mode = request.GET.get("mode", "all")
    seen = {int(x) for x in request.GET.get("seen", "").split(",") if x.isdigit()}
    cards = list(WeedCard.objects.filter(subject=subject))
    if not cards:
        return JsonResponse({"done": True, "total": 0})
    pool = cards
    if mode == "wrong":
        wrong = _weed_latest_wrong_ids(request.user, subject)
        pool = [c for c in cards if c.pk in wrong]
    elif mode == "freq":
        pool = [c for c in cards if c.exam_count > 0]
    remaining = [c for c in pool if c.pk not in seen]
    if not remaining:
        return JsonResponse({"done": True, "total": len(pool)})
    if mode == "freq":
        card = random.choices(remaining, weights=[c.exam_count for c in remaining])[0]
    else:
        card = random.choice(remaining)
    others = [c for c in cards if c.pk != card.pk]
    same = [c for c in others if c.family and c.family == card.family]
    random.shuffle(same)
    random.shuffle(others)
    picked = same[:3]
    for c in others:
        if len(picked) >= 3:
            break
        if c not in picked:
            picked.append(c)
    choices = picked + [card]
    random.shuffle(choices)
    return JsonResponse({
        "done": False,
        "card": {"id": card.pk, "q_img": card.q_image.url if card.q_image else ""},
        "choices": [{"id": c.pk, "name": c.name} for c in choices],
        "remaining": len(remaining), "total": len(pool),
    })


@login_required
def api_weed_quiz_list(request, pk):
    """전체 카드 목록 — 종명·과명·생활형·발생지, 내 풀이 상태."""
    subject = get_object_or_404(Subject, pk=pk)
    wrong = _weed_latest_wrong_ids(request.user, subject)
    done = set(WeedQuizAttempt.objects.filter(user=request.user, card__subject=subject)
               .values_list("card_id", flat=True))
    items = []
    for c in WeedCard.objects.filter(subject=subject).order_by("order"):
        items.append({
            "id": c.pk, "no": c.card_no, "name": c.name, "family": c.family,
            "life_form": c.life_form, "habitat": c.habitat,
            "exam_count": c.exam_count,
            "state": "wrong" if c.pk in wrong else ("ok" if c.pk in done else ""),
        })
    return JsonResponse({"items": items})


def _weed_gap_runs(is_gap, min_len):
    """틈(True)으로 나뉜 덩어리들의 [시작, 끝]을 돌려준다."""
    out, start = [], None
    for i, gap in enumerate(is_gap):
        if not gap and start is None:
            start = i
        if gap and start is not None:
            if i - start > min_len:
                out.append([start, i])
            start = None
    if start is not None and len(is_gap) - start > min_len:
        out.append([start, len(is_gap)])
    return out


def _weed_photo_boxes(path, min_side=40, gap_ratio=0.92):
    """붙어 있는 문제 사진에서 낱장의 사각 좌표 [x0, y0, x1, y1] 를 찾는다.

    **틈이 한 가지 색이 아니다.** 바깥 여백은 흰색인데 사진 사이는 원본
    슬라이드의 연녹색 판이 남아 있는 카드가 있다(강피의 좌우 두 장 사이가
    (225,234,207) 이고 바깥은 (255,255,255) 이었다). 그래서 '희다'로도
    '바탕색과 같다'로도 부족하고, **밝으면서 색이 옅은 화소**를 틈으로 본다 —
    사진은 초록이 짙어 채도가 높고 틈은 판 색이라 옅다.

    먼저 가로로 켜(층)를 나눈 뒤, 켜마다 세로 틈으로 다시 나눈다. 사진 안에도
    밝은 하늘이 있으므로 줄 전체(92%)가 틈이어야 자른다.
    """
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        return []
    try:
        arr = np.asarray(Image.open(path).convert("RGB")).astype(int)
    except Exception:
        return []

    height, width = arr.shape[:2]
    bright = arr.min(axis=2) > 180               # 어두운 곳은 사진이다
    faint = (arr.max(axis=2) - arr.min(axis=2)) < 45   # 색이 짙으면 사진이다
    gap = bright & faint

    def split(box, horizontal):
        """한 덩어리를 가로(또는 세로) 틈으로 나눈다. 더 못 나누면 자기 자신."""
        x0, y0, x1, y1 = box
        win = gap[y0:y1, x0:x1]
        axis = 1 if horizontal else 0
        runs = _weed_gap_runs(win.mean(axis=axis) > gap_ratio, min_side)
        if len(runs) <= 1:
            return [box]
        if horizontal:
            return [[x0, y0 + a, x1, y0 + b] for a, b in runs]
        return [[x0 + a, y0, x0 + b, y1] for a, b in runs]

    # 가로로 먼저 켜를 나누는 배열도, 세로로 먼저 나누는 배열도 있다(좌1-우2 꼴).
    # 두 순서를 다 해 보고 더 잘게 갈리는 쪽을 쓴다.
    best = None
    for first_h in (True, False):
        boxes = []
        for box in split([0, 0, width, height], first_h):
            boxes.extend(split(box, not first_h))
        # 한 번 더 — 3단 이상 섞인 배열(좌1-우2 안의 우측 두 장 등)
        deeper = []
        for box in boxes:
            deeper.extend(split(box, first_h))
        if best is None or len(deeper) > len(best):
            best = deeper
    return best or [[0, 0, width, height]]


@user_passes_test(lambda u: u.is_staff)
def api_weed_card_photos(request, pk, card_id):
    """카드 한 장에 딸린 사진들 — 관리자가 골라 내려받는다.

    문제 사진은 여러 장이 세로로 붙은 한 장이라 낱장 좌표(crop)를 함께 준다.
    자르기는 브라우저가 하므로 서버에 새 파일을 만들지 않는다.
    """
    subject = get_object_or_404(Subject, pk=pk)
    card = get_object_or_404(WeedCard, pk=card_id, subject=subject)

    # 쓸모 있는 것은 잡초 사진뿐이다 — 손그림·답 슬라이드는 내려받을 일이 없다
    photos = []
    if card.q_image:
        url = card.q_image.url
        try:
            width, height = card.q_image.width, card.q_image.height
        except Exception:
            width = height = 0
        boxes = _weed_photo_boxes(card.q_image.path)
        if len(boxes) > 1:
            for i, box in enumerate(boxes, 1):
                photos.append({"url": url, "crop": box, "w": width, "h": height,
                               "label": "사진 %d" % i, "suffix": "_%d" % i})
        else:
            photos.append({"url": url, "crop": None, "w": width, "h": height,
                           "label": "사진", "suffix": ""})
    return JsonResponse({"name": card.name, "photos": photos})


class WeedInfo(BaseModel):
    """새 잡초 카드에 채워 넣을 정보 (Gemini 구조화 응답).

    여러 줄짜리 항목은 **리스트로 받는다** — 한 문자열로 받으면 줄바꿈을
    넣어 달라고 해도 "…보인다.잎은…" 처럼 붙여 놓는다.
    """

    sci_name: str = Field(description="학명(속명 종소명). 예: Echinochloa crus-galli")
    family: str = Field(description="과명. 예: 벼과(화본과), 국화과, 사초과")
    life_form: str = Field(description="생활형. 예: 하계 일년생, 다년생 수생, 월년생")
    habitat: str = Field(description="주로 나는 곳. 예: 논·수로·습지, 밭·과수원·길가")
    features: list[str] = Field(description="식별 포인트. 한 항목에 한 가지씩 2~4개")
    similar: list[str] = Field(description="헷갈리는 종과 구별하는 법. 0~3개")
    control: list[str] = Field(description="방제 요령·비고. 1~3개")


_WEED_INFO_PROMPT = """너는 한국 농학과 잡초방제학 교수다. 아래 잡초에 대해
방송대 학생용 동정 카드에 넣을 정보를 쓴다.

잡초 이름: {name}
{official}
규칙
- 한국에서 실제로 문제가 되는 잡초 기준으로 쓴다.
- 학명은 "속명 종소명" 두 낱말만 쓴다(명명자·아종은 빼고). 사진을 찾는 데
  쓰므로 가장 널리 통하는 이름으로 적는다.
- 식별 포인트는 사진을 보고 구별할 수 있는 것(잎 모양·잎집·엽설·줄기 단면·꽃·
  땅속 기관 등)을 한 항목에 한 가지씩 적는다.
- 유사종 구별은 실제로 헷갈리는 종 이름을 대고 어디가 다른지 적는다.
- 방제는 생태적 특성에 근거해 실무적으로 적는다.
- 모든 내용은 한국어. 불렛 기호(-, •)나 번호는 붙이지 않는다.
- 한 항목은 한 문장으로 짧게. 여러 문장을 한 항목에 몰아넣지 않는다.
- 확실하지 않으면 지어내지 말고 그 항목을 비운다.
- **국립수목원 자료가 주어졌으면 학명·과명은 그대로 따르고**, 형태 설명도 그것을
  근거로 삼는다. 다만 도감 문장을 그대로 옮기지 말고 **밭·논에서 눈으로 구별하는
  요령**으로 고쳐 쓴다 — 카드는 사진을 보고 이름을 맞히는 데 쓴다."""


@user_passes_test(lambda u: u.is_staff)
def api_weed_name_check(request, pk):
    """새 카드용 종명 확인 — 중복을 막고, 없으면 Gemini 로 정보를 채운다."""
    subject = get_object_or_404(Subject, pk=pk)
    name = (request.GET.get("name") or "").strip()
    if not name:
        return JsonResponse({"ok": False, "error": "종명을 입력하세요."})

    dup = WeedCard.objects.filter(subject=subject, name__iexact=name).first()
    if dup:
        return JsonResponse({"ok": False, "duplicate": True,
                             "error": "이미 등록된 종입니다 (카드 %d번)." % dup.card_no})

    # 국립수목원 도감을 먼저 본다 — 학명·과명이 정확하고, 형태·분포 글이
    # AI 가 지어내는 것보다 믿을 만하다 (사진은 주지 않는다)
    official = _weed_nature_info(name)
    block = ""
    if official:
        rows = [("학명", official.get("sci_full")),
                ("과명", official.get("family")),
                ("APG 과명", official.get("apg_family")),
                ("형태(도감)", (official.get("shape") or "")[:900]),
                ("분포(도감)", (official.get("dstrb") or "")[:300]),
                ("유사식물(도감)", (official.get("similar") or "")[:400]),
                ("비고(도감)", (official.get("note") or "")[:400])]
        lines = ["%s: %s" % (k, v) for k, v in rows if v]
        if lines:
            block = "\n[국립수목원 국가표준식물목록 자료]\n" + "\n".join(lines) + "\n"

    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return JsonResponse({"ok": True, "info": None, "official": official,
                             "warn": "GEMINI_API_KEY 가 없어 자동 조회를 건너뜁니다."})
    try:
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=_WEED_INFO_PROMPT.format(name=name, official=block),
            config={"response_mime_type": "application/json",
                    "response_schema": WeedInfo},
        )
        info = WeedInfo.model_validate_json(resp.text).model_dump()
        # 화면에서는 줄 단위 텍스트로 다룬다
        for f in ("features", "similar", "control"):
            info[f] = "\n".join(s.strip() for s in info[f] if s.strip())
    except Exception as e:
        logger.exception("잡초 정보 조회 실패")
        return JsonResponse({"ok": True, "info": None, "official": official,
                             "warn": "자동 조회에 실패했습니다: %s" % e})

    # 학명·과명은 도감 값으로 덮어쓴다 — AI 는 호출마다 달리 답할 때가 있다
    if official:
        if official.get("sci_name"):
            info["sci_name"] = official["sci_name"]
        if official.get("family"):
            info["family"] = official["family"]
    return JsonResponse({"ok": True, "info": info, "official": official})


# 사진을 어떻게 늘어놓을지 — 칸마다 (x, y, 폭, 높이) 비율, 그리고 전체 세로:가로 비
# 기존 카드가 대개 세로로 길쭉하므로(452x630 꼴) 그에 맞춘다
_WEED_LAYOUTS = {
    "1":    ([(0, 0, 1, 1)], 0.72),
    "1t1b": ([(0, 0, 1, .5), (0, .5, 1, .5)], 1.40),
    "1t2b": ([(0, 0, 1, .5), (0, .5, .5, .5), (.5, .5, .5, .5)], 1.30),
    "2t2b": ([(0, 0, .5, .5), (.5, 0, .5, .5), (0, .5, .5, .5), (.5, .5, .5, .5)], 1.00),
    "1l2r": ([(0, 0, .5, 1), (.5, 0, .5, .5), (.5, .5, .5, .5)], 0.75),
    "2l2r": ([(0, 0, .5, .5), (0, .5, .5, .5), (.5, 0, .5, .5), (.5, .5, .5, .5)], 1.00),
}


def _weed_compose(files, layout, width=900, gap=10):
    """올린 사진들을 고른 배열대로 한 장에 붙인다.

    **높이는 사진에 맞춰 정한다** — 배열 비율로 틀을 먼저 못 박으면 사진이
    칸보다 납작할 때 위아래에 큰 빈 자리가 남는다(상·하 사진 사이가 벌어져
    보였다). 열마다 사진을 폭에 맞춰 줄인 뒤 그 높이를 그대로 쓴다.

    낱장 가르기(`_weed_photo_boxes`)가 다시 찾아낼 수 있도록 칸 사이는 흰
    여백으로 띄우되, 구별될 만큼만 둔다. **바깥 여백도 칸 사이와 같게** 둬
    상하좌우가 고르게 보이도록 한다. 사진은 자르지 않는다.
    """
    from PIL import Image, ImageDraw

    cells, _ratio = _WEED_LAYOUTS.get(layout) or _WEED_LAYOUTS["1"]
    photos = [Image.open(f).convert("RGB") for f in files]
    inner = max(1, width - gap * 2)          # 사진이 놓이는 폭 (바깥 여백 뺀 것)

    # 칸마다 폭을 정하고, 그 폭에 맞춘 사진 높이를 구한다
    plan = []
    for cell, photo in zip(cells, photos):
        cx, cy, cw, ch = cell
        x0 = gap + int(cx * inner) + (gap // 2 if cx > 0 else 0)
        x1 = gap + int((cx + cw) * inner) - (gap // 2 if cx + cw < 1 else 0)
        bw = max(1, x1 - x0)
        nh = max(1, round(photo.height * bw / photo.width))
        plan.append({"cell": cell, "photo": photo, "x0": x0, "w": bw, "h": nh})

    # 줄(row)마다 그 줄에서 가장 높은 사진에 맞춘다. cy 가 같은 것이 한 줄이다.
    # 여러 줄을 차지하는 사진(좌1·우2 의 왼쪽)은 줄 높이 계산에서 뺀다 —
    # 그것까지 넣으면 오른쪽 두 장 사이가 그만큼 벌어진다
    rows = sorted({round(p["cell"][1], 3) for p in plan})
    one_row = 1.0 / len(rows) + 1e-6 if rows else 1.0
    row_h = {}
    for r in rows:
        hs = [p["h"] for p in plan
              if round(p["cell"][1], 3) == r and p["cell"][3] <= one_row]
        row_h[r] = max(hs) if hs else max(p["h"] for p in plan)
    row_y, y = {}, gap                       # 위쪽 바깥 여백부터 시작
    for r in rows:
        row_y[r] = y
        y += row_h[r] + gap
    height = max(1, y)                       # 마지막 gap 이 아래쪽 바깥 여백

    canvas = Image.new("RGB", (width, height), (255, 255, 255))
    placed = []
    for p in plan:
        cx, cy, cw, ch = p["cell"]
        r = round(cy, 3)
        # 차지하는 줄들의 높이 합
        span = [rr for rr in rows if cy - 1e-6 <= rr < cy + ch - 1e-6]
        bh = sum(row_h[rr] for rr in span) + gap * (len(span) - 1)
        photo = p["photo"]
        scale = min(p["w"] / photo.width, bh / photo.height)
        nw, nh = max(1, round(photo.width * scale)), max(1, round(photo.height * scale))
        photo = photo.resize((nw, nh), Image.LANCZOS)
        # 남는 자리는 **아래로** 몰아 사진을 위에 붙인다. 가운데 두면 여러 줄을
        # 차지하는 사진(좌1·우2 의 왼쪽)의 위아래가 다 떠 보인다
        px, py = p["x0"] + (p["w"] - nw) // 2, row_y[r]
        canvas.paste(photo, (px, py))
        placed.append((px, py, px + nw, py + nh))

    # 사진마다 테두리를 그린다 — 밝은 사진은 흰 바탕과 경계가 안 보인다.
    # 검정은 너무 세서 옅은 회색을 쓴다
    draw = ImageDraw.Draw(canvas)
    for x0, y0, x1, y1 in placed:
        draw.rectangle([x0, y0, x1 - 1, y1 - 1], outline=(170, 170, 170), width=1)
    return canvas


_WIKI_UA = "HanulStudy/1.0 (https://hanulstudy.kr; gocompu21@gmail.com)"


def _wiki_json(url):
    import json as _json
    import urllib.request

    req = urllib.request.Request(url, headers={"User-Agent": _WIKI_UA})
    with urllib.request.urlopen(req, timeout=12) as resp:
        return _json.load(resp)


def _weed_web_photos(name, sci_name="", limit=12):
    """위키미디어 공용에서 그 잡초 사진을 찾는다.

    **학명으로 찾아야 한다** — 한국어 이름으로는 거의 안 나오고(흰명아주·올방개
    모두 0장), 학명을 주면 잘 나온다. 학명이 없으면 한국어 위키백과 → 위키데이터
    (P225)로 찾아본다.

    CC 라이선스라 쓸 수 있지만 저작자 표시가 필요하므로 라이선스·저작자를 함께 준다.
    """
    import urllib.parse

    terms = []
    if sci_name:
        terms.append(sci_name.strip())
    if not terms:
        try:
            d = _wiki_json("https://ko.wikipedia.org/w/api.php?action=query&format=json"
                           "&prop=pageprops&redirects=1&titles=" + urllib.parse.quote(name))
            for page in (d.get("query", {}).get("pages") or {}).values():
                qid = (page.get("pageprops") or {}).get("wikibase_item")
                if not qid:
                    continue
                wd = _wiki_json("https://www.wikidata.org/w/api.php?action=wbgetclaims"
                                "&format=json&property=P225&entity=" + qid)
                claims = wd.get("claims", {}).get("P225") or []
                if claims:
                    terms.append(claims[0]["mainsnak"]["datavalue"]["value"])
        except Exception:
            logger.exception("학명 조회 실패")
    terms.append(name)

    out, seen = [], set()
    for term in terms:
        if len(out) >= limit:
            break
        try:
            # filetype:bitmap 으로 PDF·DjVu(옛 책 스캔)를 애초에 뺀다
            d = _wiki_json(
                "https://commons.wikimedia.org/w/api.php?action=query&format=json"
                "&generator=search&gsrnamespace=6&gsrlimit=%d&gsrsearch=%s"
                "&prop=imageinfo&iiprop=url|extmetadata|size&iiurlwidth=480"
                % (limit, urllib.parse.quote(term + " filetype:bitmap")))
        except Exception:
            logger.exception("공용 사진 검색 실패: %s", term)
            continue
        for page in (d.get("query", {}).get("pages") or {}).values():
            info = (page.get("imageinfo") or [{}])[0]
            url = info.get("thumburl")
            title = page.get("title", "")
            if not url or url in seen:
                continue
            # 학명 사진이 없으면 **옛 식물학 책 스캔**이 잔뜩 걸린다(선피막이가 그랬다 —
            # 12장이 모두 표지·본문 PDF 였다). 동정 카드에는 살아 있는 사진이 필요하다
            low = title.lower()
            if any(w in low for w in (".pdf", ".svg", ".djvu", ".tif",
                                      "illustration", "drawing", "herbarium",
                                      "plate ", "catalogue", "flora of ", "naturalist",
                                      " list of ", "jstor-", "(ia ", "botanicum",
                                      "journal", "bulletin", "magazine")):
                continue
            # 학명으로 찾았는데 제목에 그 학명이 없으면 대개 딴 사진이다
            # (선피막이는 사진이 없어 수족관 사진 한 장이 걸렸다)
            if term != name and term.lower().split()[0] not in low:
                continue
            seen.add(url)
            meta = info.get("extmetadata") or {}
            author = re.sub(r"<[^>]+>", "", (meta.get("Artist") or {}).get("value", ""))
            # 추적 파라미터를 떼고, 카드에 넣을 것은 더 큰 판으로 받는다.
            # 위키는 요청한 폭(480)이 아니라 가까운 규격(500px)으로 줄 때가 있어
            # 숫자를 못 박지 않고 정규식으로 바꾼다
            clean = url.split("?")[0]
            out.append({
                "thumb": clean,
                "full": re.sub(r"/\d+px-", "/1280px-", clean),
                "title": title.replace("File:", ""),
                "license": (meta.get("LicenseShortName") or {}).get("value", ""),
                "author": author.strip()[:60],
                "page": info.get("descriptionurl", ""),
            })
            if len(out) >= limit:
                break
    return out


_NATURE_BASE = "https://apis.data.go.kr/1400119/PlantResource"


def _nature_xml(path, **params):
    """국립수목원 식물자원 API 호출.

    키는 **이미 URL 인코딩된 상태로 발급**되므로 그대로 붙인다 —
    `urlencode` 로 다시 인코딩하면 403 이 난다.
    """
    import urllib.parse
    import urllib.request
    from xml.etree import ElementTree

    key = getattr(settings, "NATURE_API_KEY", "")
    if not key:
        return None
    qs = "&".join("%s=%s" % (k, urllib.parse.quote(str(v))) for k, v in params.items())
    url = "%s%s?%s&serviceKey=%s" % (_NATURE_BASE, path, qs, key)
    req = urllib.request.Request(url, headers={"User-Agent": _WIKI_UA})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return ElementTree.fromstring(resp.read())


def _weed_nature_info(name):
    """국립수목원 식물도감에서 그 식물의 공식 자료를 가져온다.

    **사진은 없다** — 학명·과명과 형태·분포·유사식물 같은 도감 글이다. AI 추정보다
    정확하므로 이것을 먼저 받아 AI 프롬프트의 바탕으로 쓴다.

    이름이 들어간 종이 여럿 걸리므로("바랭이" → 갯바랭이·왕바랭이…) 국명이 정확히
    같은 것을 고르고, 없으면 이명(notRcmmGnrlNm)까지 본다. '강피'처럼 표준 국명이
    아닌 이름은 아예 안 걸린다 — 그때는 AI 만으로 채운다.
    """
    if not name:
        return None
    try:
        root = _nature_xml("/plantPilbkSearch", reqSearchWrd=name, numOfRows=30, pageNo=1)
    except Exception:
        logger.exception("국립수목원 목록 검색 실패")
        return None
    if root is None:
        return None

    exact = alias = None
    for item in root.iter("item"):
        if (item.findtext("plantGnrlNm") or "").strip() == name:
            exact = item
            break
        if alias is None:
            others = [o.strip() for o in (item.findtext("notRcmmGnrlNm") or "").split(",")]
            if name in others:
                alias = item
    item = exact if exact is not None else alias
    if item is None:
        return None

    info = {
        "std_name": (item.findtext("plantGnrlNm") or "").strip(),
        "sci_full": (item.findtext("plantSpecsScnm") or "").strip(),
        "family": (item.findtext("familyKorNm") or "").strip(),
        "apg_family": (item.findtext("apgFamilyKorNm") or "").strip(),
        "no": (item.findtext("plantPilbkNo") or "").strip(),
        "matched": "exact" if exact is not None else "alias",
    }
    # 학명에서 명명자를 떼어 "속명 종소명"만 남긴다 (사진 검색에 쓴다)
    parts = info["sci_full"].split()
    info["sci_name"] = " ".join(parts[:2]) if len(parts) >= 2 else info["sci_full"]

    if info["no"]:
        try:
            detail = _nature_xml("/plantPilbkInfo", reqPlantPilbkNo=info["no"])
            node = next(detail.iter("item"), None) if detail is not None else None
            if node is not None:
                for key, tag in (("shape", "shpe"), ("dstrb", "dstrb"),
                                 ("similar", "smlrPlntDesc"), ("note", "note")):
                    info[key] = (node.findtext(tag) or "").strip()
        except Exception:
            logger.exception("국립수목원 상세 조회 실패")
    return info


@user_passes_test(lambda u: u.is_staff)
def api_weed_web_photos(request, pk):
    """등록 화면용 — 인터넷에서 그 잡초 사진 후보를 찾아 준다."""
    get_object_or_404(Subject, pk=pk)
    name = (request.GET.get("name") or "").strip()
    if not name:
        return JsonResponse({"photos": []})
    # 학명으로 찾아야 잘 나온다. 화면이 안 보내 주면 도감에서 찾아본다
    sci = (request.GET.get("sci") or "").strip()
    if not sci:
        official = _weed_nature_info(name)
        sci = (official or {}).get("sci_name", "")
    return JsonResponse({"photos": _weed_web_photos(name, sci)})


@user_passes_test(lambda u: u.is_staff)
def api_weed_fetch_photo(request, pk):
    """고른 사진을 서버가 받아 브라우저로 넘겨준다 (다른 도메인이라 canvas 가 막힌다)."""
    import urllib.request

    get_object_or_404(Subject, pk=pk)
    # 사진을 내려주는 곳만 받는다 (아무 주소나 받으면 SSRF 통로가 된다)
    url = request.GET.get("url") or ""
    if not url.startswith(("https://upload.wikimedia.org/", "https://thumb.wikimedia.org/",
                           "http://www.nature.go.kr/", "https://www.nature.go.kr/")):
        return JsonResponse({"ok": False, "error": "허용되지 않은 주소입니다."}, status=400)
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": _WIKI_UA,
            "Referer": "https://commons.wikimedia.org/",
        })
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read(12 * 1024 * 1024)
            ctype = resp.headers.get("Content-Type", "image/jpeg")
    except Exception as e:
        logger.exception("사진 내려받기 실패")
        return JsonResponse({"ok": False, "error": str(e)}, status=502)
    return HttpResponse(data, content_type=ctype)


def _weed_plain(raw):
    """textarea 가 보낸 평문의 줄바꿈을 고른다 (\\r\\n → \\n, 빈 줄 정리)."""
    text = (raw or "").replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.strip() for line in text.split("\n") if line.strip())


def _weed_control_with_credits(control, credits_json):
    """방제·비고 끝에 사진 출처를 적는다.

    위키미디어 사진은 CC 라이선스라 **저작자와 라이선스를 밝혀야 쓸 수 있다**.
    따로 필드를 만들지 않고 이미 화면에 보이는 '방제·비고' 끝에 붙인다.
    """
    text = _weed_plain(control)
    try:
        items = json.loads(credits_json or "[]")
    except (TypeError, ValueError):
        items = []
    lines = []
    for it in items:
        if not isinstance(it, dict):
            continue
        bits = [b for b in (it.get("title"), it.get("author"), it.get("license")) if b]
        if bits:
            where = "국립수목원" if it.get("license") == "공공누리" else "위키미디어 공용"
            lines.append("사진: " + " / ".join(str(b)[:80] for b in bits) + " (%s)" % where)
    if not lines:
        return text
    return (text + "\n" if text else "") + "\n".join(lines)


@user_passes_test(lambda u: u.is_staff)
@require_POST
def api_weed_card_create(request, pk):
    """새 잡초 카드를 등록한다 — 사진 여러 장을 고른 배열대로 한 장에 붙인다."""
    import io

    subject = get_object_or_404(Subject, pk=pk)
    name = (request.POST.get("name") or "").strip()
    if not name:
        return JsonResponse({"ok": False, "error": "종명을 입력하세요."})
    if WeedCard.objects.filter(subject=subject, name__iexact=name).exists():
        return JsonResponse({"ok": False, "error": "이미 등록된 종입니다."})

    photos = request.FILES.getlist("photos")
    if not photos:
        return JsonResponse({"ok": False, "error": "사진을 한 장 이상 올리세요."})

    layout = request.POST.get("layout") or "1"
    spec = _WEED_LAYOUTS.get(layout)
    if not spec:
        return JsonResponse({"ok": False, "error": "사진 배열을 고르세요."})
    cells = spec[0]
    if len(photos) != len(cells):
        return JsonResponse({"ok": False,
                             "error": "이 배열은 사진 %d장이 필요합니다 (지금 %d장)."
                                      % (len(cells), len(photos))})

    try:
        composed = _weed_compose(photos, layout)
    except Exception as e:
        logger.exception("잡초 사진 합성 실패")
        return JsonResponse({"ok": False, "error": "사진을 붙이지 못했습니다: %s" % e})

    last = WeedCard.objects.filter(subject=subject).order_by("-card_no").first()
    card = WeedCard(
        subject=subject,
        card_no=(last.card_no + 1) if last else 1,
        order=(last.order + 1) if last else 1,
        name=name,
        family=(request.POST.get("family") or "").strip(),
        life_form=(request.POST.get("life_form") or "").strip(),
        habitat=(request.POST.get("habitat") or "").strip(),
        # 등록 화면은 평문 textarea 다. HTML 정리는 필요 없고 줄바꿈만 고른다
        # (textarea 는 \r\n 을 보내는데 그대로 두면 화면에서 빈 줄이 생긴다)
        features=_weed_plain(request.POST.get("features")),
        similar=_weed_plain(request.POST.get("similar")),
        control=_weed_control_with_credits(request.POST.get("control"),
                                           request.POST.get("credits")),
        notes=_weed_plain(request.POST.get("notes")),
    )
    buf = io.BytesIO()
    composed.save(buf, format="JPEG", quality=92)
    card.q_image.save("q_%s.jpg" % uuid.uuid4().hex[:10], ContentFile(buf.getvalue()), save=False)
    card.save()
    return JsonResponse({"ok": True, "card_no": card.card_no, "name": card.name})


@login_required
def api_weed_quiz_card(request, pk, card_id):
    """목록에서 고른 카드 한 장을 문제로 낸다 (보기는 같은 과 우선)."""
    subject = get_object_or_404(Subject, pk=pk)
    card = get_object_or_404(WeedCard, pk=card_id, subject=subject)
    cards = list(WeedCard.objects.filter(subject=subject).exclude(pk=card.pk))
    same = [c for c in cards if c.family and c.family == card.family]
    random.shuffle(same)
    random.shuffle(cards)
    picked = same[:3]
    for c in cards:
        if len(picked) >= 3:
            break
        if c not in picked:
            picked.append(c)
    choices = picked + [card]
    random.shuffle(choices)
    return JsonResponse({
        "done": False,
        "card": {"id": card.pk, "q_img": card.q_image.url if card.q_image else ""},
        "choices": [{"id": c.pk, "name": c.name} for c in choices],
        "remaining": 1, "total": 1,
    })


@login_required
@require_POST
def api_weed_quiz_answer(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    try:
        card = WeedCard.objects.get(pk=int(request.POST.get("card", 0)), subject=subject)
        selected = WeedCard.objects.get(pk=int(request.POST.get("selected", 0)), subject=subject)
    except (ValueError, WeedCard.DoesNotExist):
        return JsonResponse({"error": "잘못된 요청"}, status=400)
    correct = card.pk == selected.pk
    WeedQuizAttempt.objects.create(user=request.user, card=card, selected=selected, is_correct=correct)
    return JsonResponse({"correct": correct, "selected_name": selected.name,
                         "answer": _weed_card_payload(card)})


@login_required
@require_POST
def api_weed_quiz_reset(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    n, _ = WeedQuizAttempt.objects.filter(user=request.user, card__subject=subject).delete()
    return JsonResponse({"ok": True, "deleted": n})


# 답 화면 서술 항목에 허용하는 서식. 글 색과 밑줄이 목적이라 이만큼이면 충분하다.
_WEED_TAGS = {"b", "strong", "i", "em", "u", "s", "br", "span", "mark", "ul", "ol", "li", "div", "p"}
_WEED_DROP = {"script", "style", "iframe", "object", "embed", "template", "noscript"}
_WEED_COLOR = re.compile(r"^#[0-9a-fA-F]{3,6}$|^rgb\([\d,\s]+\)$")


def _clean_weed_html(raw):
    """편집기가 보낸 HTML 에서 허용 태그·색만 남긴다.

    style 은 색(color·background-color)만 통과시킨다. 글꼴 크기나 위치까지
    허용하면 답 화면 서식이 카드마다 제각각이 된다.
    """
    from html.parser import HTMLParser

    class Cleaner(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.out = []
            self.skip = 0            # 허용하지 않는 태그의 안쪽 깊이

        def _style(self, value):
            keep = []
            for part in (value or "").split(";"):
                if ":" not in part:
                    continue
                prop, _, val = part.partition(":")
                prop, val = prop.strip().lower(), val.strip()
                if prop in ("color", "background-color") and _WEED_COLOR.match(val):
                    keep.append(f"{prop}: {val}")
            return "; ".join(keep)

        def handle_starttag(self, tag, attrs):
            if tag in _WEED_DROP:            # 태그도 내용도 버린다
                self.skip += 1
                return
            if tag not in _WEED_TAGS:        # 태그만 벗기고 글은 남긴다
                return
            style = self._style(dict(attrs).get("style"))
            self.out.append(f'<{tag} style="{style}">' if style else f"<{tag}>")

        def handle_endtag(self, tag):
            if tag in _WEED_DROP:
                if self.skip:
                    self.skip -= 1
                return
            if tag in _WEED_TAGS and tag != "br":
                self.out.append(f"</{tag}>")

        def handle_data(self, data):
            if not self.skip:                 # script·style 안의 글은 버린다
                self.out.append(escape(data))

    c = Cleaner()
    c.feed(raw or "")
    c.close()
    text = "".join(c.out).strip()
    # 편집기가 남기는 빈 껍데기는 지운다
    return "" if re.fullmatch(r"(<(p|div|br)>|</(p|div)>|\s|&nbsp;)*", text or "") else text


def _weed_notes_lines(raw):
    """편집기가 보낸 HTML 을 줄 단위 교수 메모로 되돌린다.

    Chrome 의 contenteditable 은 Enter 를 누르면 **첫 줄은 태그 없이 두고 둘째
    줄부터** <div> 로 감싼다("첫 줄<div>둘째 줄</div>"). 닫는 태그에서만 자르면
    첫 줄과 둘째 줄이 붙으므로 여는 태그에서도 잘라야 한다.
    """
    html = _clean_weed_html(raw)
    lines = re.split(r"</?(?:li|br|p|div)\s*/?>", html)
    lines = [unescape(re.sub(r"<[^>]+>", "", x)).replace("\xa0", " ").strip() for x in lines]
    return "\n".join(x for x in lines if x)


@login_required
@user_passes_test(staff_required)
@require_POST
def api_weed_card_update(request, pk, card_id):
    """잡초 카드의 서술 항목을 고친다 (스태프 전용).

    글 색·밑줄을 쓸 수 있도록 HTML 을 받되 허용 태그만 남긴다.
    교수 메모는 줄 단위로 저장하는 필드라 <li>·<br> 을 줄바꿈으로 되돌린다.
    """
    subject = get_object_or_404(Subject, pk=pk)
    card = get_object_or_404(WeedCard, pk=card_id, subject=subject)

    for f in ("features", "similar", "control"):
        if f in request.POST:
            setattr(card, f, _clean_weed_html(request.POST[f]))

    if "notes" in request.POST:
        card.notes = _weed_notes_lines(request.POST["notes"])

    card.save()
    return JsonResponse({"ok": True, "card": _weed_card_payload(card)})


## ══════════ 쪽집게 노트 관리자 편집 ══════════ ##


def _note_payload(request, note=None):
    """POST 의 title/content 를 정리해 (title, content, order, error) 로 돌려준다."""
    title = (request.POST.get("title") or "").strip()
    content = (request.POST.get("content") or "").replace("\r\n", "\n").strip("\n") + "\n"
    if not content.strip():
        return None, None, None, "내용이 비어 있습니다."
    heading = re.search(r"^## (.+)$", content, re.M)
    if not title:
        title = heading.group(1).strip() if heading else (note.title if note else "")
    if not title:
        return None, None, None, "제목이 없습니다. '## 제N장. 제목' 줄을 넣어 주세요."
    if not heading:
        # 파서는 '## 제N장.' 줄로 장을 나누므로 없으면 제목 줄을 앞에 붙인다
        content = f"## {title}\n\n{content}"
    elif heading.group(1).strip() != title:
        content = content.replace(heading.group(0), f"## {title}", 1)
    m = re.match(r"제(\d+)장", title)
    order = int(m.group(1)) if m else (note.order if note else None)
    return title, content, order, None


@login_required
@user_passes_test(staff_required)
@require_POST
def note_update(request, note_pk):
    note = get_object_or_404(StudyNote.objects.select_related("subject"), pk=note_pk)
    title, content, order, err = _note_payload(request, note)
    if err:
        return JsonResponse({"error": err}, status=400)
    if order != note.order and StudyNote.objects.filter(
            subject=note.subject, order=order).exclude(pk=note.pk).exists():
        return JsonResponse({"error": f"제{order}장은 이미 있습니다. 장 번호를 바꿔 주세요."}, status=400)
    note.title, note.content, note.order = title, content, order
    note.save()
    return JsonResponse({"ok": True, "pk": note.pk, "order": note.order})


@login_required
@user_passes_test(staff_required)
@require_POST
def note_create(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    last = StudyNote.objects.filter(subject=subject).aggregate(m=Max("order"))["m"] or 0
    order = last + 1
    if request.POST.get("content"):
        title, content, order2, err = _note_payload(request)
        if err:
            return JsonResponse({"error": err}, status=400)
        order = order2 or order
        if StudyNote.objects.filter(subject=subject, order=order).exists():
            return JsonResponse({"error": f"제{order}장은 이미 있습니다."}, status=400)
    else:
        title = f"제{order}장. 새 장"
        content = (f"## {title}\n\n### {order}.1 절 제목\n\n내용을 적습니다. "
                   f"핵심 용어는 **볼드**로 표시합니다.\n\n**관련 문제**: \n")
    note = StudyNote.objects.create(subject=subject, title=title, content=content, order=order)
    return JsonResponse({"ok": True, "pk": note.pk, "order": note.order})


@login_required
@user_passes_test(staff_required)
@require_POST
def note_image_upload(request):
    """쪽집게 노트 편집기 이미지 업로드 → media/notes/<subject>/ 에 저장하고 URL 반환"""
    f = request.FILES.get("image") or request.FILES.get("file")
    if not f:
        return JsonResponse({"error": "파일이 없습니다."}, status=400)
    allowed = {"image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif",
               "image/webp": ".webp", "image/svg+xml": ".svg"}
    if f.content_type not in allowed:
        return JsonResponse({"error": "이미지 파일(jpg·png·gif·webp·svg)만 올릴 수 있습니다."}, status=400)
    if f.size > 8 * 1024 * 1024:
        return JsonResponse({"error": "8MB 이하만 올릴 수 있습니다."}, status=400)
    subject_pk = re.sub(r"\D", "", request.POST.get("subject", "")) or "0"
    rel_dir = os.path.join("notes", f"s{subject_pk}")
    os.makedirs(os.path.join(settings.MEDIA_ROOT, rel_dir), exist_ok=True)
    filename = f"{timezone.now():%Y%m%d}_{uuid.uuid4().hex[:10]}{allowed[f.content_type]}"
    with open(os.path.join(settings.MEDIA_ROOT, rel_dir, filename), "wb") as out:
        for chunk in f.chunks():
            out.write(chunk)
    return JsonResponse({"url": f"{settings.MEDIA_URL}notes/s{subject_pk}/{filename}"})


@login_required
@user_passes_test(staff_required)
@require_POST
def note_delete(request, note_pk):
    note = get_object_or_404(StudyNote, pk=note_pk)
    note.delete()
    return JsonResponse({"ok": True})


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
    """PDF 자료 업로드.

    화면은 XHR 로 올려 진행률을 보여 준다(자료가 80MB 까지 있어 그냥 두면
    한참 아무 반응이 없다). XHR 이면 JSON 으로, 아니면 종전대로 리다이렉트.
    """
    ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    def fail(msg, subject_pk=None):
        if ajax:
            return JsonResponse({'ok': False, 'error': msg}, status=400)
        from django.contrib import messages
        messages.error(request, msg)
        if subject_pk:
            return redirect(f'/manage/materials/?subject={subject_pk}')
        return redirect('main:material_manage')

    subject_id = request.POST.get('subject')
    title = request.POST.get('title', '').strip()
    pdf_file = request.FILES.get('file')
    if not subject_id or not pdf_file:
        return fail('과목과 파일을 모두 선택해주세요.')
    subject = get_object_or_404(Subject, pk=int(subject_id))
    if not pdf_file.name.lower().endswith('.pdf'):
        return fail('PDF 파일만 업로드할 수 있습니다.', subject.pk)
    if not title:
        title = pdf_file.name.rsplit('.', 1)[0]
    SubjectMaterial.objects.create(
        subject=subject,
        title=title,
        file=pdf_file,
        uploaded_by=request.user,
    )
    if ajax:
        return JsonResponse({'ok': True, 'redirect': f'/manage/materials/?subject={subject.pk}'})
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


# ---------------------------------------------------------------- 질의응답

@login_required
def qna_list(request):
    """질의응답 목록 — 과목별로 걸러 본다.

    과목은 사용자가 매번 고르는 대신 질문한 화면에서 자동으로 잡히므로,
    여기서는 이미 쌓인 질문을 과목으로 걸러 보는 역할만 한다.
    """
    subject_id = request.GET.get("subject") or ""
    cert = request.GET.get("cert") or ""
    mine = request.GET.get("mine") == "1"

    qs = QnaQuestion.objects.select_related("subject", "user")
    if subject_id.isdigit():
        qs = qs.filter(subject_id=int(subject_id))
    elif cert:
        qs = qs.filter(cert_name=cert)
    if mine:
        qs = qs.filter(user=request.user)

    # 과목 곁의 숫자는 "그 과목에 쌓인 질문 수"라 목록을 고르는 데 쓰인다
    counts = dict(
        QnaQuestion.objects.exclude(subject=None)
        .values_list("subject_id")
        .annotate(n=Count("id"))
    )
    subjects = []
    for s in Subject.objects.order_by("grade", "name"):
        n = counts.get(s.pk)
        if n:
            s.qna_count = n
            subjects.append(s)
    cert_counts = (
        QnaQuestion.objects.exclude(cert_name="")
        .values("cert_name").annotate(n=Count("id")).order_by("-n")
    )

    return render(request, "main/qna_list.html", {
        "questions": qs[:200],
        "subjects": subjects,
        "counts": counts,
        "cert_counts": cert_counts,
        "sel_subject": subject_id,
        "sel_cert": cert,
        "mine": mine,
        "total": QnaQuestion.objects.count(),
    })


@login_required
def qna_detail(request, pk):
    from .models import QnaQuestion, QnaView

    q = get_object_or_404(
        QnaQuestion.objects.select_related("subject", "user"), pk=pk)
    # 조회수는 사람 단위로 센다 — 같은 사람이 여러 번 열어도 하나다
    _, created = QnaView.objects.get_or_create(question=q, user=request.user)
    if created:
        QnaQuestion.objects.filter(pk=q.pk).update(view_count=F("view_count") + 1)
        q.refresh_from_db(fields=["view_count"])

    return render(request, "main/qna_detail.html", {
        "q": q,
        "viewers": q.views.select_related("user").order_by("-viewed_at")[:30],
    })


@login_required
@require_POST
def qna_create(request):
    """질문을 올리고 곧바로 답을 받는다."""
    from .models import QnaQuestion
    from . import qna as qna_engine

    title = (request.POST.get("title") or "").strip()
    if not title:
        return JsonResponse({"ok": False, "error": "질문을 입력해 주세요."})
    if len(title) > 200:
        return JsonResponse({"ok": False, "error": "질문은 200자 이내로 써 주세요."})

    left = qna_engine.remaining_today(request.user)
    if left <= 0:
        return JsonResponse({
            "ok": False,
            "error": f"하루 질문 한도({qna_engine.DAILY_LIMIT}회)를 다 썼습니다. "
                     f"내일 다시 물어봐 주세요.",
        })

    # 질문은 과목·자격증 화면에서만 받는다. 어디에 관한 물음인지 모르면
    # 과목에 맞춘 답을 할 수 없고, 목록에서도 분류가 안 된다.
    subject = None
    sid = request.POST.get("subject_id") or ""
    if sid.isdigit():
        subject = Subject.objects.filter(pk=int(sid)).first()
    cert_name = (request.POST.get("cert_name") or "").strip()[:50]
    if subject is None and not cert_name:
        return JsonResponse({
            "ok": False,
            "error": "과목 화면의 질의응답 탭에서 물어봐 주세요.",
        })

    # 쪽집게 노트의 절에서 바로 물은 경우: 절 번호("7.5")와 제목이 함께 온다
    note_sec = (request.POST.get("note_sec") or "").strip()
    if not re.fullmatch(r"\d+\.\d+", note_sec) or subject is None:
        note_sec = ""
    if note_sec and not request.user.is_staff:
        # 절에 직접 다는 질문은 노트를 보완하는 관리자용이다. 회원은 질의응답 탭에서 묻는다
        return JsonResponse({"ok": False, "error": "절에 질문을 다는 것은 관리자만 할 수 있습니다."})
    note_sec_title = (request.POST.get("note_sec_title") or "").strip()[:200] if note_sec else ""

    q = QnaQuestion.objects.create(
        subject=subject,
        cert_name=cert_name,
        cert_subject=(request.POST.get("cert_subject") or "").strip()[:50],
        user=request.user,
        title=title,
        body=(request.POST.get("body") or "").strip()[:2000],
        note_sec=note_sec,
        note_sec_title=note_sec_title,
    )
    ok = qna_engine.ask_gemini(q)
    return JsonResponse({
        "ok": ok,
        "pk": q.pk,
        "title": q.title,
        "answer": q.answer,
        "note_ref": q.note_ref,
        "note_sec": q.note_sec,
        "note_sec_title": q.note_sec_title,
        "error": q.error,
        "who": request.user.first_name or request.user.username,
        "when": timezone.localtime(q.created_at).strftime("%m.%d"),
        "left": qna_engine.remaining_today(request.user),
        "url": f"/qna/{q.pk}/",
    })


@login_required
@require_POST
def qna_flag(request, pk):
    """답이 이상하다는 신고 — 관리 화면에서 모아 본다."""
    from .models import QnaQuestion

    QnaQuestion.objects.filter(pk=pk).update(flagged=F("flagged") + 1)
    return JsonResponse({"ok": True})


@login_required
@require_POST
def qna_delete(request, pk):
    from .models import QnaQuestion

    q = get_object_or_404(QnaQuestion, pk=pk)
    if q.user_id != request.user.id and not request.user.is_staff:
        return JsonResponse({"ok": False, "error": "지울 권한이 없습니다."})
    q.delete()
    return JsonResponse({"ok": True})
