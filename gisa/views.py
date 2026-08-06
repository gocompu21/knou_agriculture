import json
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

from .models import Certification, GisaAttempt, GisaExam, GisaGlossary, GisaQuestion, GisaSubject, GisaTextbook


## ══════════ 쪽집게 노트 과목 통합 ══════════ ##
#
# 자연생태복원기사는 2022년 출제 체계 개편으로 과목이 5개(구)→4개(신)로 바뀌었다.
# 노트는 현행 4과목 체계로 통합했으므로, 구 체계 과목은 UI에서 감추고
# 구 체계 문항(2012~2021)의 학습 링크는 통합된 신 체계 노트로 연결한다.
#
# 문항 데이터(GisaQuestion)와 구 체계 노트는 DB에 그대로 남아 있다.
# 되돌리려면 아래 두 상수만 비우면 된다.

TEXTBOOK_HIDDEN_SUBJECTS = {
    "자연생태복원기사": {
        "환경생태학개론", "환경계획학", "생태복원공학",
        "경관생태학", "자연환경관계법규",
    },
}

TEXTBOOK_SUBJECT_MERGE = {
    "자연생태복원기사": {
        "환경생태학개론": "생태환경조사분석",
        "경관생태학": "생태환경조사분석",
        "환경계획학": "생태복원계획",
        "생태복원공학": "생태복원설계·시공",
        "자연환경관계법규": "생태복원 사후관리·평가",
    },
}


## ══════════ 교재 마크다운 파서 ══════════ ##

# 파싱 결과 캐시: {cache_key: (version, parsed_data)}
_study_guide_cache = {}


def parse_study_guide(filepath_or_content, cache_key=None, cache_version=None, glossary=None):
    """마크다운 핵심정리를 파싱하여 구조화된 데이터 반환.
    filepath_or_content: 파일 경로 또는 마크다운 문자열.
    glossary: {용어: 설명} 딕셔너리 — 볼드 텍스트에 용어집 팝업 연결.
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

    _gl = glossary or {}

    def _bold_replace(m):
        """볼드 텍스트를 <strong>으로 변환. glossary에 있으면 팝업 속성 추가."""
        term = m.group(1)
        desc = _gl.get(term)
        if desc:
            esc = desc.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
            return f'<strong class="gl" data-desc="{esc}">{term}</strong>'
        return f"<strong>{term}</strong>"

    def _apply_bold(text):
        """볼드+이탤릭 마크다운을 HTML로 변환 (glossary 매칭 포함)."""
        text = re.sub(r"\*\*(.+?)\*\*", _bold_replace, text)
        text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
        return text

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
            text = _apply_bold(text)
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
                line = _apply_bold(line)
                table_rows.append(line)
                continue
            _flush_table()
            # 원번호(①~⑳) 항목 감지
            circled_match = re.match(r"^([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳])\s*(.*)", line)
            if circled_match:
                _flush_para()
                num = circled_match.group(1)
                line_content = _apply_bold(circled_match.group(2))
                html_lines.append(f"<div class='num-item'><span class='num-marker'>{num}</span>{line_content}</div>")
            elif line.startswith("→ ") or line.startswith("  → "):
                _flush_para()
                line_content = _apply_bold(line.lstrip().lstrip("→").strip())
                html_lines.append(f"<div class='num-item num-sub'>→ {line_content}</div>")
            elif line.startswith("- "):
                _flush_para()
                line_content = _apply_bold(line[2:])
                html_lines.append(f"<li>{line_content}</li>")
            elif line.startswith("  - "):
                _flush_para()
                line_content = _apply_bold(line[4:])
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


def _glossary_json(cert, include_ids=False):
    """자격증의 전 과목 용어집을 JSON 문자열로 반환.
    include_ids=True이면 {term: [description, id]} 형태, 아니면 {term: description}."""
    qs = GisaGlossary.objects.filter(certification=cert).exclude(description="")
    if not qs.exists():
        return "{}"
    if include_ids:
        data = {t: [d, pk] for pk, t, d in qs.values_list("id", "term", "description")}
    else:
        data = dict(qs.values_list("term", "description"))
    return json.dumps(data, ensure_ascii=False)


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

    # 페이지 진입 로그 저장 (실패해도 페이지 표시는 계속)
    try:
        from .models import CertificationViewLog
        ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() \
            or request.META.get('REMOTE_ADDR')
        ua = request.META.get('HTTP_USER_AGENT', '')[:300]
        CertificationViewLog.objects.create(
            certification=cert,
            user=request.user,
            tab=active_tab[:20],
            ip=ip or None,
            user_agent=ua,
        )
    except Exception:
        pass

    # 교재 탭이 아닐 때만 시험/세션 데이터 로드 (switchTab은 페이지 리로드)
    exam_cards = []
    wrong_count = 0
    exam_sessions = []

    # 탭별 필요한 데이터만 로드 (switchTab은 페이지 리로드)
    if active_tab in ("study", "solve"):
        _exam_list = list(
            exams.annotate(q_count=Count("gisaquestion")).order_by("-year", "-round")
        )
        # 회차마다 실제 출제된 과목만 노출한다.
        # (자연생태복원기사처럼 연도에 따라 과목 체계가 바뀌는 자격증이 있어
        #  자격증 전체 과목 목록을 그대로 쓰면 없는 과목까지 표시된다)
        _card_subjects = {}
        for row in (
            GisaQuestion.objects.filter(exam__in=_exam_list)
            .values("exam__pk", "subject__pk", "subject__name", "subject__order")
            .annotate(cnt=Count("pk"))
            .order_by("exam__pk", "subject__order")
        ):
            if not row["subject__pk"]:
                continue
            _card_subjects.setdefault(row["exam__pk"], []).append({
                "pk": row["subject__pk"],
                "order": row["subject__order"],
                "name": row["subject__name"],
                "count": row["cnt"],
            })
        exam_cards = [
            {
                "exam": e,
                "count": e.q_count,
                "subjects": _card_subjects.get(e.pk, []),
            }
            for e in _exam_list
        ]

    wrong_results = []
    if active_tab == "wrong" and request.user.is_authenticated:
        # 오답 판단은 wrong_review 제외한 최신 시도 기준
        latest_ids = (
            GisaAttempt.objects.filter(
                user=request.user,
                question__exam__certification=cert,
            )
            .exclude(mode="wrong_review")
            .values("question")
            .annotate(latest_id=Max("id"))
            .values_list("latest_id", flat=True)
        )
        wrong_attempts = list(
            GisaAttempt.objects.filter(pk__in=latest_ids, is_correct=False)
            .exclude(selected="0")
            .select_related("question", "question__subject", "question__exam")
        )
        # 오답복습 최신 시각 매핑
        review_times = dict(
            GisaAttempt.objects.filter(
                user=request.user,
                mode="wrong_review",
                question__exam__certification=cert,
            ).values_list("question_id", "created_at")
        )
        # 복습 시각이 최근 오답 시각보다 이전이면 무효(=복습 안 한 것으로 취급)
        def is_valid_review(a):
            rt = review_times.get(a.question_id)
            return rt is not None and rt >= a.created_at
        # 복습 안 한 문제 먼저, 복습한 문제는 오래된 복습 순으로 뒤
        wrong_attempts.sort(
            key=lambda a: (
                is_valid_review(a),  # False(0) 먼저, True(1) 뒤
                review_times.get(a.question_id) if is_valid_review(a) else a.created_at,
                a.question.subject.order,
                a.question.number,
            )
        )
        wrong_results = build_results(wrong_attempts)
        wrong_count = len(wrong_results)

    # 오답 탭 쪽집게 노트 매핑
    wrong_q_notes_json = "{}"
    if active_tab == "wrong" and wrong_results:
        wrong_questions = [r["question"] for r in wrong_results]
        wrong_note_subjects = list({q.subject for q in wrong_questions if q.subject})
        wrong_note_map = _build_note_map(cert, wrong_note_subjects)
        wrong_q_notes = {}
        for q in wrong_questions:
            key = f"{q.exam.year}-{q.exam.round}-{q.number}"
            if key in wrong_note_map:
                wrong_q_notes[str(q.id)] = _rank_notes(q.text, wrong_note_map[key])
        wrong_q_notes_json = json.dumps(wrong_q_notes, ensure_ascii=False)

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

    # 용어집 탭
    glossary_terms = []
    glossary_count = 0
    glossary_subject = ""
    glossary_subjects = []
    if active_tab == "glossary":
        # 용어가 등록된 과목만 노출
        _g_names = set(
            GisaGlossary.objects.filter(certification=cert)
            .values_list("subject__name", flat=True)
        )
        glossary_subjects = [n for n in subjects.values_list("name", flat=True) if n in _g_names]
        glossary_subject = request.GET.get("subject", glossary_subjects[0] if glossary_subjects else "")
        import re as _re
        glossary_terms = list(
            GisaGlossary.objects.filter(
                certification=cert, subject__name=glossary_subject
            ).values("id", "term", "description")
        )
        glossary_terms.sort(key=lambda t: _re.sub(r'[^가-힣a-zA-Z0-9]', '', t["term"]))
        glossary_count = GisaGlossary.objects.filter(certification=cert).count()

    # 교재 데이터 — 교재 탭일 때만 장 제목 전달 (섹션은 AJAX로 로드)
    # 통합으로 감춘 과목은 목록에서 제외한다 (모듈 상단 TEXTBOOK_HIDDEN_SUBJECTS 참조)
    _hidden = TEXTBOOK_HIDDEN_SUBJECTS.get(cert.name, set())

    textbook_chapters = []
    textbook_subjects = [
        n for n in subjects.values_list("name", flat=True) if n not in _hidden
    ]
    first_subject = textbook_subjects[0] if textbook_subjects else ""
    textbook_subject = request.GET.get("subject", first_subject)
    if textbook_subject in _hidden:
        textbook_subject = first_subject
    if active_tab == "textbook":
        textbook = GisaTextbook.objects.filter(
            certification=cert, subject__name=textbook_subject
        ).first()
        if textbook:
            # 용어집 로드 (해당 과목)
            _gl_qs = GisaGlossary.objects.filter(
                certification=cert, subject__name=textbook_subject
            ).exclude(description="").values_list("term", "description")
            _gl_dict = dict(_gl_qs) if _gl_qs.exists() else {}
            full = parse_study_guide(
                textbook.content,
                cache_key=f"gisa_tb_{textbook.pk}_gl{len(_gl_dict)}",
                cache_version=textbook.updated_at,
                glossary=_gl_dict,
            )
            textbook_chapters = [
                {"id": ch["id"], "title": ch["title"]} for ch in full
            ]

    # 모의고사에 쓸 수 있는 과목(=문항이 있는 과목)만 추린다.
    # 연도별로 과목 체계가 바뀐 자격증은 전체 과목을 그대로 쓰면
    # 문항이 없는 과목까지 버튼이 생긴다.
    _mock_pool = {
        row["subject__pk"]: row["cnt"]
        for row in GisaQuestion.objects.filter(exam__certification=cert)
        .exclude(exam__exam_type="최신")
        .values("subject__pk")
        .annotate(cnt=Count("pk"))
        if row["subject__pk"]
    }
    mock_subjects = [s for s in subjects if _mock_pool.get(s.pk)]

    # 모의고사 탭: 사용자별 과목 진행도 통계 (MockGeneration 기반)
    mock_stats = []
    if request.user.is_authenticated:
        from .models import MockGeneration
        gen_map = {
            g.subject_id: g
            for g in MockGeneration.objects.filter(user=request.user, subject__certification=cert)
        }
        for subj in mock_subjects:
            total_pool = GisaQuestion.objects.filter(
                exam__certification=cert, subject=subj
            ).exclude(exam__exam_type="최신").count()
            g = gen_map.get(subj.pk)
            if g:
                seen = len(g.seen_question_ids or [])
                gen = g.generation
            else:
                seen = 0
                gen = 1
            pct = round(seen / total_pool * 100, 1) if total_pool else 0
            mock_stats.append({
                "subject_id": subj.pk,
                "order": subj.order,
                "name": subj.name,
                "round": gen,           # R (Round)
                "seen": seen,
                "total": total_pool,
                "pct": pct,
                "rounds_completed": gen - 1,  # 완주한 라운드 수
            })

    return render(
        request,
        "gisa/certification_detail.html",
        {
            "cert": cert,
            "exams": exams,
            "subjects": subjects,
            "mock_subjects": mock_subjects,
            "exam_cards": exam_cards,
            "wrong_count": wrong_count,
            "wrong_results": wrong_results,
            "wrong_q_notes_json": wrong_q_notes_json,
            "exam_sessions": exam_sessions,
            "active_tab": active_tab,
            "total_questions": total_questions,
            "textbook_chapters": textbook_chapters,
            "textbook_subject": textbook_subject,
            "textbook_subjects": textbook_subjects,
            "latest_year_cards": latest_year_cards,
            "latest_questions": latest_questions,
            "glossary_terms": glossary_terms,
            "glossary_count": glossary_count,
            "glossary_subject": glossary_subject,
            "glossary_subjects": glossary_subjects,
            "glossary_json": _glossary_json(cert, include_ids=request.user.is_staff if request.user.is_authenticated else False),
            "mock_stats": mock_stats,
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
    _gl_qs = GisaGlossary.objects.filter(
        certification=cert, subject__name=subject
    ).exclude(description="").values_list("term", "description")
    _gl_dict = dict(_gl_qs) if _gl_qs.exists() else {}
    chapters = parse_study_guide(
        textbook.content,
        cache_key=f"gisa_tb_{textbook.pk}_gl{len(_gl_dict)}",
        cache_version=textbook.updated_at,
        glossary=_gl_dict,
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
                "explanation": q.explanation or "",
                "choice_1_exp": q.choice_1_exp or "",
                "choice_2_exp": q.choice_2_exp or "",
                "choice_3_exp": q.choice_3_exp or "",
                "choice_4_exp": q.choice_4_exp or "",
            }
            for q in qs
        ],
        "keywords": words,
    })


## ══════════ 학습모드 ══════════ ##


_RE_HTML_TAG = re.compile(r"<[^>]+>")
_RE_PAREN = re.compile(r"[（(]([^)）]+)[)）]")
_RE_HANJA = re.compile(r"[\u4e00-\u9fff]+")


def _extract_keywords(text):
    """문제 텍스트에서 매칭용 키워드를 추출한다."""
    keywords = set()
    # 괄호 안 내용 (한자, 영문, 한글)
    for m in _RE_PAREN.finditer(text):
        inner = m.group(1).strip()
        if inner:
            keywords.add(inner.lower())
    # 한자
    for m in _RE_HANJA.finditer(text):
        keywords.add(m.group())
    # 2글자 이상 한글 명사구 (정원, 궁전, 양식 등 포함)
    for m in re.finditer(r"[가-힣]{2,}", text):
        w = m.group()
        if len(w) >= 3:
            keywords.add(w)
    return keywords


def _rank_notes(question_text, notes):
    """문제 텍스트와의 키워드 매칭도로 노트를 정렬한다."""
    if len(notes) <= 1:
        return notes
    keywords = _extract_keywords(question_text)
    if not keywords:
        return notes

    scored = []
    for note in notes:
        plain = _RE_HTML_TAG.sub("", note.get("html", "")).lower()
        title = note.get("title", "").lower()
        target = title + " " + plain
        score = sum(1 for kw in keywords if kw.lower() in target)
        scored.append((score, note))

    scored.sort(key=lambda x: -x[0])
    return [n for _, n in scored]


def _build_note_map(cert, subjects):
    """쪽집게 노트에서 문제 참조(YYYY-R-N) → 절 HTML 매핑을 구축한다."""
    note_map = {}  # "YYYY-R-N" -> [{title, chapter, html}, ...]
    for subj in subjects:
        try:
            tb = GisaTextbook.objects.get(certification=cert, subject=subj)
        except GisaTextbook.DoesNotExist:
            continue
        if not tb.content:
            continue
        chapters = parse_study_guide(
            tb.content,
            cache_key=f"tb_{tb.pk}",
            cache_version=str(tb.updated_at),
        )
        for ch in chapters:
            for sec in ch["sections"]:
                sec_html = sec.get("content_html", "")
                sec_title = sec.get("title", "")
                ch_title = ch.get("title", "")
                for qref in sec.get("questions", []):
                    note_map.setdefault(qref, []).append({
                        "title": sec_title,
                        "chapter": ch_title,
                        "html": sec_html,
                    })
                for sub in sec.get("subsections", []):
                    sub_html = sub.get("content_html", "")
                    sub_title = sub.get("title", "")
                    for qref in sub.get("questions", []):
                        note_map.setdefault(qref, []).append({
                            "title": sub_title,
                            "chapter": ch_title,
                            "html": sub_html,
                        })
    return note_map


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

    # 쪽집게 노트 매핑
    if subject:
        note_subjects = [subject]
    else:
        note_subjects = list(GisaSubject.objects.filter(certification=cert))
    note_map = _build_note_map(cert, note_subjects)

    # 문제별 노트 매핑 (관련도 정렬)
    q_notes = {}
    for q in questions:
        key = f"{exam.year}-{exam.round}-{q.number}"
        if key in note_map:
            q_notes[str(q.id)] = _rank_notes(q.text, note_map[key])

    # 사용자의 현재 오답노트에 등록된 문제 ID
    wrong_qids = (
        set(_get_wrong_question_ids(request.user, cert))
        if request.user.is_authenticated
        else set()
    )

    return render(
        request,
        "gisa/study_mode.html",
        {
            "cert": cert,
            "exam": exam,
            "subject": subject,
            "questions": questions,
            "wrong_qids": wrong_qids,
            "q_notes_json": json.dumps(q_notes, ensure_ascii=False),
            "glossary_json": _glossary_json(cert, include_ids=request.user.is_staff if request.user.is_authenticated else False),
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
            "glossary_json": _glossary_json(cert, include_ids=request.user.is_staff if request.user.is_authenticated else False),
        },
    )


## ══════════ 모의고사 ══════════ ##


@login_required
def mock_exam_take(request, cert_id):
    cert = get_object_or_404(Certification, pk=cert_id)
    subject_id = request.GET.get("subject")
    subjects = GisaSubject.objects.filter(certification=cert).order_by("order")
    if subject_id:
        subjects_target = subjects.filter(pk=subject_id)
    else:
        subjects_target = subjects

    # 세대(generation) 추적: 과목별로 독립. 같은 세대에 이미 출제된 문제 제외, 풀 소진 시 +1
    # ※ 누적 저장은 출제 시점이 아니라 '제출' 시점(mock_exam_submit)에서 수행
    #   → 사용자가 페이지만 열고 풀지 않으면 세대 누적에 반영되지 않음
    from .models import MockGeneration
    questions = []
    gen_info = []           # 각 과목별 세대 정보 (UI 표시용)
    gen_reset_just_now = False

    for subject in subjects_target:
        gen_obj, _ = MockGeneration.objects.get_or_create(
            user=request.user, subject=subject,
            defaults={'generation': 1, 'seen_question_ids': []},
        )
        seen_ids = set(gen_obj.seen_question_ids or [])
        base_qs = GisaQuestion.objects.filter(
            exam__certification=cert, subject=subject
        ).exclude(exam__exam_type="최신")
        total_pool = base_qs.count()
        unseen_list = list(base_qs.exclude(id__in=seen_ids).order_by("?")[:20])

        # 미출제 풀이 20개 미만이면 → 이 과목 세대 종료, 리셋 후 새 세대 추출
        # (리셋은 즉시 저장 — 출제 풀이 진짜로 소진된 시점이므로)
        if len(unseen_list) < min(20, total_pool):
            seen_ids = set()
            gen_obj.generation += 1
            gen_obj.seen_question_ids = []
            gen_obj.save(update_fields=['generation', 'seen_question_ids', 'updated_at'])
            gen_reset_just_now = True
            unseen_list = list(base_qs.order_by("?")[:20])

        # ⚠️ 출제 시점에는 저장하지 않음. submit에서 실제 푼 문제만 반영.
        gen_info.append({
            'subject': subject.name,
            'generation': gen_obj.generation,
            'seen': len(gen_obj.seen_question_ids),
            'total': total_pool,
        })
        questions.extend(unseen_list)

    if not questions:
        return redirect("gisa:certification_detail", cert_id=cert_id)

    # 과목순서 → 문제번호 정렬
    questions.sort(key=lambda q: (q.subject.order, q.number))

    session_id = str(uuid.uuid4())
    request.session[f"gisa_mock_{session_id}"] = [q.pk for q in questions]
    # 단일 과목 응시: 그 과목 세대, 다중 과목: 최저 세대(전체 진행도 기준)
    current_generation = min(g['generation'] for g in gen_info) if gen_info else 1
    seen_count = sum(g['seen'] for g in gen_info)

    # 쪽집게 노트 매핑
    note_subjects = list(GisaSubject.objects.filter(certification=cert))
    note_map = _build_note_map(cert, note_subjects)
    q_notes = {}
    for q in questions:
        key = f"{q.exam.year}-{q.exam.round}-{q.number}"
        if key in note_map:
            q_notes[str(q.id)] = _rank_notes(q.text, note_map[key])

    # 이미 오답노트에 등록된 문제 ID (학습모드에서 오답노트 등록 상태 표시용)
    wrong_qids = set()
    if request.user.is_authenticated:
        wrong_qids = set(_get_wrong_question_ids(request.user, cert))

    return render(
        request,
        "gisa/mock_exam_take.html",
        {
            "cert": cert,
            "questions": questions,
            "session_id": session_id,
            "subjects": subjects,
            "q_notes_json": json.dumps(q_notes, ensure_ascii=False),
            "wrong_qids": wrong_qids,
            "current_generation": current_generation,
            "seen_count": seen_count,
            "gen_reset_just_now": gen_reset_just_now,
            "gen_info": gen_info,
        },
    )


@login_required
@require_POST
def mock_mark_answered(request, cert_id):
    """모의고사 풀이 중 답안 선택 시 즉시 해당 문제를 세대(MockGeneration)에 기록.
    body: {"question_id": 123}
    """
    cert = get_object_or_404(Certification, pk=cert_id)
    try:
        qid = int(request.POST.get('question_id', '0'))
    except (TypeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'bad question_id'}, status=400)
    if not qid:
        return JsonResponse({'ok': False}, status=400)
    try:
        q = GisaQuestion.objects.select_related('subject').get(pk=qid, exam__certification=cert)
    except GisaQuestion.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'question not found'}, status=404)

    from .models import MockGeneration
    gen_obj, _ = MockGeneration.objects.get_or_create(
        user=request.user, subject=q.subject,
        defaults={'generation': 1, 'seen_question_ids': []},
    )
    seen = set(gen_obj.seen_question_ids or [])
    if qid not in seen:
        seen.add(qid)
        gen_obj.seen_question_ids = list(seen)
        gen_obj.save(update_fields=['seen_question_ids', 'updated_at'])
    return JsonResponse({'ok': True, 'seen': len(gen_obj.seen_question_ids), 'generation': gen_obj.generation})


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

    # 세대 누적은 풀이 중 답안 선택 시점에 AJAX(mock_mark_answered)로 이미 처리됨
    # 제출 시점에는 누적 갱신 없음 (보조 방어선으로 응답한 문제만 한 번 더 보장)
    from .models import MockGeneration
    answered_qids_by_subject = {}
    for q in ordered_questions:
        selected = request.POST.get(f"question_{q.id}", "0") or "0"
        if selected == "0":
            continue
        answered_qids_by_subject.setdefault(q.subject_id, []).append(q.pk)
    for sid, qids in answered_qids_by_subject.items():
        gen_obj = MockGeneration.objects.filter(user=request.user, subject_id=sid).first()
        if not gen_obj:
            gen_obj = MockGeneration.objects.create(
                user=request.user, subject_id=sid,
                generation=1, seen_question_ids=[],
            )
        seen = set(gen_obj.seen_question_ids or [])
        before = len(seen)
        seen.update(qids)
        if len(seen) != before:
            gen_obj.seen_question_ids = list(seen)
            gen_obj.save(update_fields=['seen_question_ids', 'updated_at'])

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

    # 새 모의고사 URL: 단일 과목 응시였으면 같은 과목으로 재응시
    distinct_subject_ids = {a.question.subject_id for a in attempts}
    if len(distinct_subject_ids) == 1:
        only_sid = next(iter(distinct_subject_ids))
        next_mock_url = f"/gisa/{cert.pk}/mock/?subject={only_sid}"
    else:
        next_mock_url = f"/gisa/{cert.pk}/mock/"

    # 쪽집게 노트 매핑
    note_subjects = list(GisaSubject.objects.filter(certification=cert))
    note_map = _build_note_map(cert, note_subjects)
    q_notes = {}
    for a in attempts:
        q = a.question
        key = f"{q.exam.year}-{q.exam.round}-{q.number}"
        if key in note_map:
            q_notes[str(q.id)] = _rank_notes(q.text, note_map[key])

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
            "glossary_json": _glossary_json(cert, include_ids=request.user.is_staff if request.user.is_authenticated else False),
            "q_notes_json": json.dumps(q_notes, ensure_ascii=False),
            "next_mock_url": next_mock_url,
        },
    )


## ══════════ 오답노트 ══════════ ##


def _get_wrong_question_ids(user, cert):
    """사용자의 최신 GisaAttempt 중 오답인 문제 ID 리스트 반환 (미응답 제외)"""
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
        .exclude(selected="0")
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
        .exclude(selected="0")
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
            "glossary_json": _glossary_json(cert, include_ids=request.user.is_staff if request.user.is_authenticated else False),
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
        .exclude(selected="0")
        .select_related("question", "question__subject", "question__exam")
        .order_by("question__number")
    )

    results = build_results(wrong_attempts)
    total_in_session = GisaAttempt.objects.filter(
        user=request.user, session_id=session_id
    ).count()
    mode = wrong_attempts.first().mode if wrong_attempts.exists() else "exam"

    # 쪽집게 노트 매핑
    note_subjects = list(GisaSubject.objects.filter(certification=cert))
    note_map = _build_note_map(cert, note_subjects)
    q_notes = {}
    for a in wrong_attempts:
        q = a.question
        key = f"{q.exam.year}-{q.exam.round}-{q.number}"
        if key in note_map:
            q_notes[str(q.id)] = _rank_notes(q.text, note_map[key])

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
            "glossary_json": _glossary_json(cert, include_ids=request.user.is_staff if request.user.is_authenticated else False),
            "q_notes_json": json.dumps(q_notes, ensure_ascii=False),
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
            "glossary_json": _glossary_json(cert, include_ids=request.user.is_staff if request.user.is_authenticated else False),
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
def mark_wrong(request, cert_id, question_id):
    """학습모드에서 문제를 오답노트로 보내는 기능.
    오답 attempt를 추가해 가장 최근 attempt가 오답이 되게 만든다.
    selected가 실제 사용자 오답이면 그걸 저장, 아니면 첫 번째 오답 선지 사용."""
    cert = get_object_or_404(Certification, pk=cert_id)
    question = get_object_or_404(
        GisaQuestion, pk=question_id, exam__certification=cert
    )
    correct_answers = question.answer.split(",")
    selected = request.POST.get("selected", "")
    if selected not in ["1", "2", "3", "4"] or selected in correct_answers:
        selected = "1"
        for c in ["1", "2", "3", "4"]:
            if c not in correct_answers:
                selected = c
                break
    GisaAttempt.objects.create(
        user=request.user,
        question=question,
        selected=selected,
        is_correct=False,
        mode="study",
    )
    return JsonResponse({"ok": True})


@login_required
@require_POST
def wrong_review(request, cert_id, question_id):
    """오답노트에서 선지를 클릭한 풀이 기록 저장 (순환용).
    기존 wrong_review 기록이 있으면 갱신, 없으면 생성."""
    cert = get_object_or_404(Certification, pk=cert_id)
    question = get_object_or_404(
        GisaQuestion, pk=question_id, exam__certification=cert
    )
    selected = request.POST.get("selected", "0")
    correct_answers = question.answer.split(",")
    is_correct = selected in correct_answers and selected != "0"
    # 기존 wrong_review 기록 삭제 후 새로 생성 (최신 시각 반영)
    GisaAttempt.objects.filter(
        user=request.user, question=question, mode="wrong_review"
    ).delete()
    GisaAttempt.objects.create(
        user=request.user,
        question=question,
        selected=selected,
        is_correct=is_correct,
        mode="wrong_review",
    )
    return JsonResponse({"ok": True, "is_correct": is_correct})


@login_required
@require_POST
def session_delete(request, cert_id, session_id):
    GisaAttempt.objects.filter(
        user=request.user,
        session_id=session_id,
        question__exam__certification_id=cert_id,
    ).delete()
    return redirect(
        f"{reverse('gisa:certification_detail', args=[cert_id])}?tab=history"
    )


@login_required
@require_POST
def session_delete_all(request, cert_id):
    GisaAttempt.objects.filter(
        user=request.user,
        question__exam__certification_id=cert_id,
    ).delete()
    return redirect(
        f"{reverse('gisa:certification_detail', args=[cert_id])}?tab=history"
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
        # 미응답(selected='0')은 오답노트에서 제외되므로 wrong 카운트에도 포함 안 함
        wrong = s_attempts.filter(is_correct=False).exclude(selected="0").count()
        skipped = s_attempts.filter(selected="0").count()
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
            "skipped": skipped,
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
    subsection_id = ""
    if questions:
        subj_name = questions[0].subject.name if questions[0].subject else ""
        # 자연생태복원기사 구 체계 과목(2012~2021)의 문항은 통합된 신 체계 노트로 연결한다.
        subj_name = TEXTBOOK_SUBJECT_MERGE.get(cert.name, {}).get(subj_name, subj_name)
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
                            subsection_id = sub["id"]
                            break
                    if section_id:
                        break
                if section_id:
                    break

    # 쪽집게 노트 매핑
    note_subjects = list({q.subject for q in questions if q.subject})
    note_map = _build_note_map(cert, note_subjects)
    q_notes = {}
    for q in questions:
        key = f"{q.exam.year}-{q.exam.round}-{q.number}"
        if key in note_map:
            q_notes[str(q.id)] = _rank_notes(q.text, note_map[key])

    # 사용자의 현재 오답노트에 등록된 문제 ID
    wrong_qids = (
        set(_get_wrong_question_ids(request.user, cert))
        if request.user.is_authenticated
        else set()
    )

    return render(
        request,
        "gisa/study_mode.html",
        {
            "cert": cert,
            "exam": None,
            "subject": None,
            "questions": questions,
            "wrong_qids": wrong_qids,
            "is_textbook_study": True,
            "section_title": section_title,
            "textbook_subject": textbook_subject,
            "chapter_idx": chapter_idx,
            "section_id": section_id,
            "subsection_id": subsection_id,
            "q_notes_json": json.dumps(q_notes, ensure_ascii=False),
            "glossary_json": _glossary_json(cert, include_ids=request.user.is_staff if request.user.is_authenticated else False),
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


@login_required
@user_passes_test(_gisa_staff_required)
@require_POST
def glossary_delete(request, pk):
    """용어집 항목 삭제 (staff only, AJAX)"""
    glossary = get_object_or_404(GisaGlossary, pk=pk)
    term = glossary.term
    glossary.delete()
    return JsonResponse({"ok": True, "term": term})
