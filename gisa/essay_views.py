# -*- coding: utf-8 -*-
"""실기 필답형 뷰.

화면 구성
  essay_list      실기 탭 — 회차 카드 + 영역별 학습 카드
  essay_take      풀이 화면 (회차 또는 영역)
  essay_submit    제출 → 채점 → 결과로 이동
  essay_result    채점 결과 (문항별 포인트 대조 + 점수 조정)
  essay_adjust    사용자 점수 조정 (AJAX)
  essay_sheet     인쇄용 시험지 (paper 모드)
  essay_upload    시험지 사진 업로드 → 판독
  essay_confirm   판독 결과 확인·수정 후 채점
"""
import json
import os
import random
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .essay_examinfo import exam_info, hm
from .resource_views import resource_tab_context, video_tab_context
from .essay_topics import siblings, topic_groups
from .pesticide import can_see as pest_can_see, stats as pest_stats
from .pest import can_see as bug_can_see, stats as bug_stats
from .essay_grading import grade_answer, grade_session
from .templatetags.gisa_filters import qtext
from main.models import QnaQuestion
from .models import (ESSAY_ROUND_SOURCES, Certification, GisaEssayAttempt, GisaEssayNote,
                     GisaEssayQuestion, GisaEssaySession, GisaEssayUpload)

# 영역별 학습 세션에 담을 문항 수
STUDY_BATCH = 10


def _daily_count(user, kind):
    """오늘 사용자의 LLM 호출 횟수 (채점=세션 수, 판독=업로드 수)."""
    since = timezone.now() - timedelta(days=1)
    if kind == 'grade':
        return GisaEssaySession.objects.filter(
            user=user, status='done', submitted_at__gte=since).count()
    return GisaEssayUpload.objects.filter(
        session__user=user, transcribed=True, uploaded_at__gte=since).count()


# ------------------------------------------------------------------ 목록

@login_required
def essay_list(request, cert_id):
    """실기 탭: 기출 회차 카드 + 예상문제 영역 카드."""
    cert = get_object_or_404(Certification, pk=cert_id)
    qs = GisaEssayQuestion.objects.filter(certification=cert)

    from django.db.models import Sum
    # 연도는 최신부터, 그 안의 회차는 1→2→3 순. 시험이 치러진 차례대로
    # 읽는 편이 자연스럽고, 특정 회차를 찾을 때도 눈이 덜 헤맨다.
    rounds = (qs.filter(source='기출')
              .values('year', 'round')
              .annotate(c=Count('id'), p=Sum('points'))
              .order_by('-year', 'round'))

    # 영역 카드 — 회차가 없는 문항 묶음(예상문제·구유형 적산)이 여기 실린다
    sections = list(qs.filter(source__in=('예상', '적산'))
                    .values('source', 'section')
                    .annotate(c=Count('id'))
                    .order_by('source', 'section'))
    # 구유형 적산은 가나다순이면 '측량'이 맨 앞으로 와 흐름이 끊긴다.
    # 적산이 실제로 진행되는 차례(무엇을 얼마나 옮기나 → 무엇으로 얼마나 드나)로 둔다.
    _JS_ORDER = ['토공량', '기계화 시공', '인력·기계 운반', '재료·적산',
                 '수목식재', '포장·시설', '측량·적산일반']
    sections.sort(key=lambda x: (x['source'] != '적산',
                                 _JS_ORDER.index(x['section'])
                                 if x['section'] in _JS_ORDER else 99,
                                 x['section']))

    # 화면만 열었다 나간 세션은 이력을 어지럽히므로 치운다.
    # 답을 하나도 쓰지 않았고, 인쇄용 시험지도 아니고, 하루가 지난 것.
    # (시험지 모드는 인쇄만 해두고 며칠 뒤 답을 올리는 흐름이라 남긴다)
    try:
        stale = timezone.now() - timedelta(days=1)
        (GisaEssaySession.objects
         .filter(user=request.user, certification=cert, status='progress',
                 mode__in=('online', 'quiz'), started_at__lt=stale,
                 attempts__isnull=True)
         .delete())
        # 모의·오답 세션은 문항을 빈 답안으로 붙여 두므로 답이 하나도 없는지 본다
        for s in GisaEssaySession.objects.filter(
                user=request.user, certification=cert, status='progress',
                mode='online', started_at__lt=stale, source__in=('모의', '오답')):
            if not s.attempts.exclude(answer_text='').exists():
                s.delete()
    except Exception:
        pass

    # 내 응시 이력 요약
    sessions = (GisaEssaySession.objects
                .filter(user=request.user, certification=cert)
                .order_by('-started_at')[:30])
    best = {}
    for s in GisaEssaySession.objects.filter(
            user=request.user, certification=cert, status='done',
            source__in=ESSAY_ROUND_SOURCES):
        key = (s.source, s.year, s.round)
        if key not in best or s.score > best[key]:
            best[key] = s.score

    # 복원이 일부만 된 회차는 배점 합계가 만점에 못 미치므로 카드에 그 사실을
    # 알린다. **만점은 자격증마다 다르다** — 자연생태복원 45, 조경 40,
    # 식물보호산업기사 100. 45 를 박아 두었을 때는 40점짜리 조경 회차가 전부
    # '일부 복원'으로 찍혔다.
    _einfo = exam_info(cert.name)
    FULL_POINTS = (_einfo or {}).get('essay_points', 45)
    round_cards = []
    for r in rounds:
        key = ('기출', r['year'], r['round'])
        pts = round(float(r['p'] or 0), 1)
        round_cards.append({
            'year': r['year'], 'round': r['round'], 'count': r['c'],
            'points': pts,
            'partial': pts < FULL_POINTS - 1,
            'best': best.get(key),
        })

    # 연도별로 묶는다 — 51개 회차가 한 줄로 늘어서면 어느 해 것인지
    # 카드를 하나씩 읽어야 한다.
    round_years = []
    for c in round_cards:
        if not round_years or round_years[-1]['year'] != c['year']:
            round_years.append({'year': c['year'], 'cards': [], 'done': 0})
        round_years[-1]['cards'].append(c)
        if c['best'] is not None:
            round_years[-1]['done'] += 1

    # 학원예상시험 — 학원 모의고사를 회차별로 싣는다. 기출 통계(빈출·모의고사
    # 뽑기·쪽집게 노트)에는 섞지 않는다 — 실제 출제가 아니라 학원의 예상이다.
    academy_cards = []
    for r in (qs.filter(source='학원').values('year', 'round')
              .annotate(c=Count('id'), p=Sum('points')).order_by('year', 'round')):
        academy_cards.append({
            'year': r['year'], 'round': r['round'], 'count': r['c'],
            'points': round(float(r['p'] or 0), 1),
            'best': best.get(('학원', r['year'], r['round'])),
        })

    # 빈출 주제 현황 — 되풀이 출제된 주제가 몇 개인지 보여 준다
    freq_cards = []
    for lo, label in ((4, '4회 이상'), (3, '3회 이상'), (2, '2회 이상')):
        n = (GisaEssayQuestion.objects
             .filter(certification=cert, source='기출', freq_rounds__gte=lo)
             .values('topic_key').distinct().count())
        if n:
            freq_cards.append({'min': lo, 'label': label, 'count': n})

    # 재출제 유력 — 실기 1회 출제인데 주제어가 필기에 10회 이상 등장한 문항
    comeback_count = (GisaEssayQuestion.objects
                      .filter(certification=cert, source='기출',
                              freq_rounds=1, written_freq__gte=10).count())

    # 오답노트 — 만점을 못 받은 문항(문항마다 최근 응시 기준)
    wrong = _wrong_attempts(request.user, cert)
    for a in wrong:                      # 2.5 · 1.25 처럼 필요한 자리까지만(2.50 이 아니라)
        a.score_disp = '%g' % round(a.score, 2)

    tab = request.GET.get('tab', 'textbook')
    _tabs = ['textbook', 'study', 'solve', 'mock', 'wrong', 'history', 'qna', 'res']
    # 해충·농약 DVD 는 'DVD' 탭 하나에 묶고 그 안에서 고른다(`?tab=dvd&dvd=pest`).
    # 예전 주소 ?tab=pest · ?tab=pesticide 는 그 칸을 연 DVD 탭으로 받는다.
    dvd_subs = ([('pest', '해충 DVD')] if bug_can_see(cert) else []) +                ([('pesticide', '농약 DVD')] if pest_can_see(cert) else [])
    dvd_keys = [k for k, _ in dvd_subs]
    dvd = request.GET.get('dvd', '')
    if tab in dvd_keys:
        tab, dvd = 'dvd', tab
    if dvd_keys:
        _tabs.append('dvd')
        if dvd not in dvd_keys:
            dvd = dvd_keys[0]
    if tab not in _tabs:
        tab = 'textbook'

    # 쪽집게 노트 — 주제별 교재. 탭이 클라이언트 전환이라 항상 내려보낸다(10분 캐시)
    from .essay_textbook import build_textbook
    textbook = build_textbook(cert)

    return render(request, 'gisa/essay_list.html', {
        'cert': cert,
        # 실기에 작업형이 있나. 없으면(식물보호산업기사) 시험이력의
        # '작업형 필요' 칸이 뜻을 잃어 통째로 뺀다.
        'has_work_stage': bool(_einfo.get('work_points')) if _einfo else True,
        # 실전 타이머 분수 — 자격증마다 다르다(안내 문구가 이 값을 쓴다)
        'exam_minutes': (_einfo or {}).get('essay_minutes', 90),
        # 배점·시간이 자격증마다 다르다(조경 40+60, 자연생태복원 45+55,
        # 식물보호산업기사는 필답 100점 단독). 머리말 문구를 여기서 받아 쓴다 —
        # 개요가 없는 자격증은 종전 문구 그대로.
        'info': _einfo,
        'active_tab': tab,
        'dvd_subs': dvd_subs,
        'dvd_active': dvd,
        # 농약 DVD 암기카드 — 식물보호 두 급수에만 낸다(`pesticide.can_see`).
        # 92종은 자격증에 매이지 않아 두 급수가 같은 카드를 함께 쓴다.
        'pest_on': pest_can_see(cert),
        'pest_stats': pest_stats(request.user) if pest_can_see(cert) else None,
        # 해충 DVD — 농약 DVD 바로 옆 탭. 조건은 같다(식물보호 두 급수)
        'bug_on': bug_can_see(cert),
        'bug_stats': bug_stats(request.user) if bug_can_see(cert) else None,
        'tb': textbook,
        'wrong_items': wrong,
        'wrong_count': len(wrong),
        # 오답노트의 내 답안에 채점 결과 화면과 같은 색연필 첨삭을 입힌다
        'wrong_pen': {a.pk: {
            'score': a.score, 'max': float(a.question.points),
            'marks': (a.feedback.get('marks') or []) if isinstance(a.feedback, dict) else [],
            'missing': (a.feedback.get('missing') or []) if isinstance(a.feedback, dict) else [],
            'answer': a.answer_text or '',
        } for a in wrong},
        'mock_size': MOCK_SIZE,
        'mock_years': sorted({c['year'] for c in round_cards}, reverse=True),
        # 모의고사 범위 지정의 분류 목록. 자격증마다 다르다.
        'topic_groups': topic_groups(cert.name),
        'mock_sessions': [s for s in sessions if s.source == '모의' and s.status == 'done'][:5],
        'round_cards': round_cards,
        'round_years': round_years,
        'academy_cards': academy_cards,
        'sections': sections,
        # 영역 카드의 제목. 조경은 구유형 적산, 자연생태복원은 예상문제가 실린다
        'section_title': ('영역별 구유형 적산'
                          if sections and all(x['source'] == '적산' for x in sections)
                          else '영역별 예상문제'),
        'freq_cards': freq_cards,
        'comeback_count': comeback_count,
        # 작업형 자료(work-*)는 작업형 화면에서 보여 주므로 필답 노트 링크에서 뺀다
        'notes': GisaEssayNote.objects.filter(certification=cert).exclude(slug__startswith='work-'),
        # 학습전략 화면은 '빈출 58주제 정리'를 전제로 쓰여 있어 그 자료가 있을 때만 연다
        'has_strategy': GisaEssayNote.objects.filter(
            certification=cert, slug='freq58').exists(),
        # 합격 전략 문서가 있는 자격증에만 링크를 낸다(essay_pass 참조)
        'has_pass': bool(pass_doc_path(cert.name)),
        # 자료실 — 필기 상세와 같은 조각을 쓴다(gisa/_resources.html)
        **resource_tab_context(cert, 'practical'),
        # 질의응답 — 실기 질문만. cert_subject='실기' 로 표시해 두면
        # 프롬프트가 답안 형식(①②③)으로 답하도록 갈린다.
        'qna_items': QnaQuestion.objects.filter(
            cert_name=cert.name, cert_subject='실기').select_related('user')[:10],
        'qna_count': QnaQuestion.objects.filter(
            cert_name=cert.name, cert_subject='실기').count(),
        'sessions': sessions,
        'total': qs.count(),
    })


# ------------------------------------------------------------------ 풀이

MOCK_SIZE = 15          # 실제 필답형이 15문항 안팎 45점이다
WRONG_RETRY_MAX = 20    # 오답 재풀이 한 번에 담는 문항 수


def _wrong_attempts(user, cert):
    """만점을 못 받은 문항의 최근 답안. 문항마다 가장 최근 응시 하나로 판정한다.

    같은 문항을 나중에 다시 풀어 만점을 받았으면 오답에서 빠진다.
    답을 쓰지 않고 넘긴 문항은 '틀린' 게 아니라 '안 푼' 것이므로 넣지 않는다
    (0점이지만 오답노트에 쌓이면 실제 약점이 묻힌다).
    """
    atts = (GisaEssayAttempt.objects
            .filter(session__user=user, session__certification=cert,
                    session__status='done')
            .exclude(answer_text='')
            .select_related('question', 'session')
            .order_by('-session__submitted_at', 'question__number'))
    wrong, seen = [], set()
    for a in atts:
        if a.question_id in seen:
            continue
        seen.add(a.question_id)
        if a.wrong_dismissed:           # "노트 X" 로 뺀 답안 — 최근 답안이 이것이면 제외
            continue
        if a.score < float(a.question.points):
            wrong.append(a)
    wrong.sort(key=lambda a: (-a.question.year, -a.question.round, a.question.number))
    return wrong


def _mock_scope(request, cert):
    """모의고사 범위 파라미터 → (yfrom, yto, groups, n, 라벨).

    연도 범위·주제 분류·문항 수를 고를 수 있다. 라벨은 세션 section(30자)에
    들어가 시험이력에 "모의 2020~2026 · 3분류 · 15문항"처럼 남는다.
    """
    years = sorted(set(GisaEssayQuestion.objects.filter(certification=cert, source='기출')
                       .order_by().values_list('year', flat=True)))
    lo, hi = (years[0], years[-1]) if years else (None, None)

    def _int(name, default):
        try:
            return int(request.GET.get(name) or default)
        except (TypeError, ValueError):
            return default
    yfrom, yto = _int('yfrom', lo), _int('yto', hi)
    if yfrom and yto and yfrom > yto:
        yfrom, yto = yto, yfrom
    groups = []
    for g in request.GET.getlist('g'):
        try:
            groups.append(int(g))
        except ValueError:
            pass
    # 분류는 자격증마다 다르다(자연생태복원 8 · 식물보호 11)
    all_groups = [gid for gid, _ in topic_groups(cert.name)]
    if not groups or set(groups) >= set(all_groups):
        groups = []                                  # 전체
    n = max(5, min(30, _int('n', MOCK_SIZE)))

    parts = ['모의']
    if (yfrom, yto) != (lo, hi):
        parts.append('%d~%d' % (yfrom, yto) if yfrom != yto else str(yfrom))
    if groups:
        parts.append('%d분류' % len(groups))
    if n != MOCK_SIZE:
        parts.append('%d문항' % n)
    return yfrom, yto, groups, n, ' '.join(parts)[:30]


def _pick_mock(cert, yfrom=None, yto=None, groups=None, n=MOCK_SIZE):
    """모의고사 — 기출에서 주제가 겹치지 않게 무작위로 뽑는다.

    같은 주제(topic_key)가 두 번 나오면 한 회차 시험답지 않다. 최근 회차의
    문항이 조금 더 자주 뽑히도록 연도에 가중치를 둔다. 범위(연도·분류)를 주면
    그 안에서만 뽑는다.
    """
    qs = GisaEssayQuestion.objects.filter(certification=cert, source='기출')
    if yfrom:
        qs = qs.filter(year__gte=yfrom)
    if yto:
        qs = qs.filter(year__lte=yto)
    if groups:
        qs = qs.filter(topic_group__in=groups)
    pool = list(qs)
    random.shuffle(pool)
    years = [q.year for q in pool] or [0]
    lo = min(years)
    weighted = sorted(pool, key=lambda q: random.random() / (1 + (q.year - lo) / 10))
    picked, seen = [], set()
    for q in weighted:
        key = q.topic_key or f'#{q.pk}'
        if key in seen:
            continue
        seen.add(key)
        picked.append(q)
        if len(picked) >= n:
            break
    # 화면은 순번(1, 2, 3…)으로 보여 주므로 순서만 안정적이면 된다.
    # 이어 올 때 attempts 를 같은 기준으로 정렬해 같은 차례가 나온다.
    picked.sort(key=lambda q: (q.number, q.pk))
    return picked


def _pick_questions(cert, source, section=None, year=None, round_=None, user=None):
    if source == '모의':
        return _pick_mock(cert)
    if source == '오답':
        if not (user and user.is_authenticated):
            return []
        qs = [a.question for a in _wrong_attempts(user, cert)][:WRONG_RETRY_MAX]
        qs.sort(key=lambda q: (q.number, q.pk))
        return qs
    qs = GisaEssayQuestion.objects.filter(certification=cert, source=source)
    if source in ESSAY_ROUND_SOURCES:
        qs = qs.filter(year=year, round=round_)
        return list(qs.order_by('number'))
    qs = qs.filter(section=section)
    # 학습 모드: 아직 만점을 못 받은 문항을 우선 출제
    solved = set()
    if user and user.is_authenticated:
        solved = set(GisaEssayAttempt.objects.filter(
            session__user=user, question__in=qs,
            final_score__isnull=True, ai_score__isnull=False
        ).values_list('question_id', flat=True))
    items = list(qs.order_by('number'))
    fresh = [q for q in items if q.pk not in solved]
    pool = fresh or items
    return pool[:STUDY_BATCH]


@login_required
def essay_take(request, cert_id):
    """필답형 풀이 화면."""
    cert = get_object_or_404(Certification, pk=cert_id)
    source = request.GET.get('source', '기출')
    section = request.GET.get('section', '')
    year = request.GET.get('year')
    round_ = request.GET.get('round')
    mode = request.GET.get('mode', 'online')
    if mode not in ('online', 'paper', 'quiz'):
        mode = 'online'

    year = int(year) if year else None
    round_ = int(round_) if round_ else None

    # 인쇄한 시험지로 이어 오는 경우(?resume=<세션pk>)는 새로 만들지 않는다.
    session = None
    resume = request.GET.get('resume')
    if resume:
        session = GisaEssaySession.objects.filter(
            pk=resume, user=request.user, certification=cert,
            status='progress').first()

    questions = None
    if session is not None and source in ('모의', '오답'):
        # 무작위·오답 세트는 이어 올 때 다시 뽑으면 다른 문항이 된다.
        # 답을 저장해 둔 문항이 있으면 그 문항들로 잇는다.
        saved = [a.question for a in session.attempts.select_related('question')
                 .order_by('question__number', 'question_id')]
        if saved:
            questions = saved
    mock_label = '모의고사'
    if questions is None and source == '모의':
        yfrom, yto, groups, n, mock_label = _mock_scope(request, cert)
        questions = _pick_mock(cert, yfrom, yto, groups, n)
    if questions is None:
        questions = _pick_questions(cert, source, section, year, round_, request.user)
    if not questions:
        return redirect(f'/gisa/{cert_id}/essay/?tab=' + ('wrong' if source == '오답' else 'mock'))

    total_points = round(sum(float(q.points) for q in questions), 1)

    # 시험지 코드는 "연도-회차"(예: 2026-2)로 고정한다. 세션마다 다른 코드를
    # 주면 먼저 인쇄한 시험지가 다음 세션에서 "다른 시험지"로 거부된다.
    # 시험지 보안이 필요한 서비스가 아니므로 회차만 맞으면 된다.
    if session is None:
        code = ''
        if mode == 'paper':
            code = (f'{year}-{round_}' if source == '기출'
                    else f'학원 {year}-{round_}' if source == '학원' else section[:12])
        section_val = {'예상': section, '적산': section, '기출': '기출', '학원': '학원예상',
                       '모의': mock_label, '오답': '오답 재풀이'}.get(source, source)
        session = GisaEssaySession.objects.create(
            user=request.user, certification=cert,
            source=source, section=section_val,
            year=year, round=round_, mode=mode,
            total_points=total_points, paper_code=code,
        )
        if source in ('모의', '오답'):
            # 뽑힌 문항을 세션에 붙여 둔다(빈 답안). 이어 올 때 같은 세트가
            # 나오게 하는 유일한 저장소다 — 세션에 문항 목록 필드가 없다.
            GisaEssayAttempt.objects.bulk_create([
                GisaEssayAttempt(session=session, question=q, answer_text='')
                for q in questions])

    # 이어 올 때 서버에 저장된 초안을 채워 준다. localStorage 초안은 같은 브라우저
    # 에서만 살아 있어, 다른 기기에서 열면 빈 시험지였다.
    drafts = dict(session.attempts.values_list('question_id', 'answer_text'))
    for q in questions:
        q.draft = drafts.get(q.pk, '')

    # 실전(기출·모의)은 실제 시험시간만큼 타이머를 걸고, 학습(예상·오답)은 무제한.
    # **시험시간은 자격증마다 다르다** — 자연생태복원·조경기사 90분, 조경산업기사
    # 60분, 식물보호산업기사 120분. 90을 박아 두면 남의 시험시간으로 연습하게 된다.
    _info = exam_info(cert.name)
    exam_minutes = (_info or {}).get('essay_minutes', 90)
    time_limit = exam_minutes * 60 if source in ('기출', '학원', '모의') else 0

    if session.mode == 'quiz':
        return render(request, 'gisa/essay_quiz.html', {
            'cert': cert,
            'session': session,
            'questions': questions,
            'total_points': total_points,
            'seq_numbers': source in ('모의', '오답'),
            'quiz_state': _quiz_state(session),
        })

    return render(request, 'gisa/essay_take.html', {
        'cert': cert,
        'session': session,
        'questions': questions,
        'total_points': total_points,
        'time_limit': time_limit,
        'exam_minutes': exam_minutes,
        'is_exam': source in ('기출', '학원', '모의'),
        # 풀면서 채점해 둔 문항 — 이어 올 때 첨삭 답안지로 되살린다(퀴즈와 같은 규칙)
        'pen_state': _quiz_state(session),
        # 여러 회차를 섞은 세트는 원래 문항 번호가 겹치므로 순번으로 보여 준다
        'seq_numbers': source in ('모의', '오답'),
    })


def _quiz_state(session):
    """퀴즈를 이어 올 때 이미 채점한 문항의 결과를 되살린다.

    채점한 답과 지금 답이 같은 것만 — 채점 뒤 답을 고쳤으면 다시 채점해야 한다
    (`essay_grade_step` 과 같은 규칙).
    """
    state = {}
    for a in session.attempts.select_related('question'):
        fb = a.feedback if isinstance(a.feedback, dict) else None
        if not (a.graded_at and fb and a.answer_text
                and fb.get('answer') == a.answer_text):
            continue
        state[a.question_id] = {
            'score': a.score, 'max': float(a.question.points),
            'points': fb.get('points') or [], 'summary': fb.get('summary') or '',
            'marks': fb.get('marks') or [], 'missing': fb.get('missing') or [],
            'answer_html': _essay_answer_html(a.question),
        }
    return state


@login_required
@require_POST
def essay_submit(request, cert_id, session_id):
    """답안 제출 → 채점."""
    cert = get_object_or_404(Certification, pk=cert_id)
    session = get_object_or_404(GisaEssaySession, pk=session_id,
                                user=request.user, certification=cert)
    if session.status == 'done':
        return redirect('gisa:essay_result', cert_id=cert_id, session_id=session.pk)

    limit = getattr(settings, 'ESSAY_DAILY_GRADE_LIMIT', 20)
    if _daily_count(request.user, 'grade') >= limit:
        return render(request, 'gisa/essay_result.html', {
            'cert': cert, 'session': session, 'attempts': [],
            'error': f'하루 채점 한도({limit}회)를 초과했습니다. 내일 다시 시도해 주세요.',
        })

    qids = request.POST.getlist('question_id')
    for qid in qids:
        q = GisaEssayQuestion.objects.filter(pk=qid, certification=cert).first()
        if not q:
            continue
        GisaEssayAttempt.objects.update_or_create(
            session=session, question=q,
            defaults={'answer_text': request.POST.get(f'answer_{qid}', '').strip()},
        )

    session.status = 'grading'
    session.save(update_fields=['status'])
    grade_session(session)
    return redirect('gisa:essay_result', cert_id=cert_id, session_id=session.pk)


@login_required
@require_POST
def essay_draft(request, cert_id, session_id):
    """답안 초안 자동 저장 — 상태를 바꾸지 않고 답만 남긴다.

    essay_save 는 진행률 채점 1단계라 status 를 grading 으로 바꾸므로 초안용으로
    쓸 수 없다. 이어하기(?resume=)가 이 초안을 채워 준다. 비어 있는 답은 지운다.
    """
    cert = get_object_or_404(Certification, pk=cert_id)
    session = get_object_or_404(GisaEssaySession, pk=session_id,
                                user=request.user, certification=cert)
    if session.status != 'progress':
        return JsonResponse({'ok': False, 'error': '진행 중인 응시가 아닙니다.'}, status=400)
    n = 0
    for qid in request.POST.getlist('question_id'):
        q = GisaEssayQuestion.objects.filter(pk=qid, certification=cert).first()
        if not q:
            continue
        text = request.POST.get(f'answer_{qid}', '').strip()
        if text:
            GisaEssayAttempt.objects.update_or_create(
                session=session, question=q, defaults={'answer_text': text})
            n += 1
        elif session.source not in ('모의', '오답'):
            # 모의·오답은 빈 답안이 문항 세트를 붙잡아 두는 자리라 지우지 않는다
            GisaEssayAttempt.objects.filter(session=session, question=q).delete()
        else:
            GisaEssayAttempt.objects.filter(session=session, question=q).update(answer_text='')
    return JsonResponse({'ok': True, 'saved': n})


@login_required
@require_POST
def essay_save(request, cert_id, session_id):
    """답안만 저장한다 (채점 전). 진행률 채점의 1단계."""
    cert = get_object_or_404(Certification, pk=cert_id)
    session = get_object_or_404(GisaEssaySession, pk=session_id,
                                user=request.user, certification=cert)
    if session.status == 'done':
        return JsonResponse({'ok': False, 'error': '이미 채점된 세션입니다.'}, status=400)

    limit = getattr(settings, 'ESSAY_DAILY_GRADE_LIMIT', 20)
    if _daily_count(request.user, 'grade') >= limit:
        return JsonResponse(
            {'ok': False,
             'error': f'하루 채점 한도({limit}회)를 초과했습니다. 내일 다시 시도해 주세요.'},
            status=429)

    saved = []
    for qid in request.POST.getlist('question_id'):
        q = GisaEssayQuestion.objects.filter(pk=qid, certification=cert).first()
        if not q:
            continue
        GisaEssayAttempt.objects.update_or_create(
            session=session, question=q,
            defaults={'answer_text': request.POST.get(f'answer_{qid}', '').strip()},
        )
        saved.append({'question_id': q.pk, 'number': q.number})

    session.status = 'grading'
    session.save(update_fields=['status'])
    saved.sort(key=lambda x: x['number'])
    return JsonResponse({'ok': True, 'questions': saved})


@login_required
@require_POST
def essay_grade_step(request, cert_id, session_id, question_id):
    """문항 하나를 채점하고 결과를 저장한다.

    브라우저가 문항 수만큼(동시 3개씩) 호출하며 진행률을 갱신한다.
    한 문항이 실패해도 나머지는 계속 채점된다.
    """
    from django.utils import timezone

    cert = get_object_or_404(Certification, pk=cert_id)
    session = get_object_or_404(GisaEssaySession, pk=session_id,
                                user=request.user, certification=cert)
    attempt = get_object_or_404(GisaEssayAttempt,
                                session=session, question_id=question_id)

    # 이미 채점됐으면 다시 호출하지 않는다 (새로고침·중복 요청 대비, 그리고
    # 풀면서 '바로 채점'으로 매겨 둔 문항). **답이 그때와 같을 때만이다** —
    # 채점해 보고 답을 고쳤는데 옛 점수가 그대로 남으면 안 된다.
    done = attempt.feedback if isinstance(attempt.feedback, dict) else None
    if attempt.graded_at and done and done.get('answer') == attempt.answer_text:
        return JsonResponse({'ok': True, 'cached': True,
                             'number': attempt.question.number,
                             'score': attempt.score,
                             'max': float(attempt.question.points)})

    try:
        result = grade_answer(attempt.question, attempt.answer_text)
    except Exception as e:
        return JsonResponse({'ok': False, 'number': attempt.question.number,
                             'error': str(e)}, status=500)

    attempt.ai_score = result['score']
    attempt.feedback = dict(result, answer=attempt.answer_text)
    attempt.graded_at = timezone.now()
    attempt.save(update_fields=['ai_score', 'feedback', 'graded_at'])

    return JsonResponse({
        'ok': True,
        'number': attempt.question.number,
        'score': result['score'],
        'max': result['max'],
        'engine': result['engine'],
    })


@login_required
@require_POST
def essay_finish(request, cert_id, session_id):
    """모든 문항 채점 후 총점을 확정한다."""
    from django.utils import timezone

    cert = get_object_or_404(Certification, pk=cert_id)
    session = get_object_or_404(GisaEssaySession, pk=session_id,
                                user=request.user, certification=cert)

    total = sum(a.score for a in session.attempts.all())
    session.score = round(total, 2)
    session.status = 'done'
    session.submitted_at = session.submitted_at or timezone.now()
    session.save(update_fields=['score', 'status', 'submitted_at'])

    return JsonResponse({
        'ok': True,
        'score': session.score,
        'total_points': session.total_points,
        'percent': session.percent,
        'redirect': reverse('gisa:essay_result',
                            args=[cert_id, session.pk]),
    })


# ------------------------------------------------------------------ 시험 개요

@login_required
def essay_work(request, cert_id):
    """실기 작업형(도면 설계) 자료 — 필답형 페이지와 머리의 전환 단추로 오간다.

    탭은 넷이다: 개요 · 도면 기본기 · 기출분석(연도별 출제 도면 목록) · 설계 요소.
    도면 기본기와 설계 요소는 학습자료(GisaEssayNote) slug `work-basics`·`work-elements`
    에 쓰고, 기출분석은 GisaDrawingTask 다. 아직 자료가 없는 탭은 '준비 중'으로 둔다.
    """
    import markdown as md
    from .models import GisaDrawingTask

    cert = get_object_or_404(Certification, pk=cert_id)
    info = exam_info(cert.name)
    if not (info and info.get('work_part')):
        return redirect('gisa:essay_list', cert.pk)

    # 연도는 최신부터, 그 안의 회차는 1→2→3 — 필답형 회차 카드와 같은 차례
    tasks = list(GisaDrawingTask.objects.filter(certification=cert)
                 .order_by('-year', 'round', 'order').prefetch_related('images'))
    years = []
    for t in tasks:
        t.conditions_html = md.markdown(t.conditions, extensions=['tables']) if t.conditions else ''
        t.commentary_html = md.markdown(t.commentary, extensions=['tables']) if t.commentary else ''
        t.has_detail = bool(t.conditions or t.commentary or t.images.all())
        if not years or years[-1]['year'] != t.year:
            years.append({'year': t.year, 'tasks': []})
        years[-1]['tasks'].append(t)

    # 출제 빈도 — 도면(이름 + 번호)마다 몇 번 나왔고 평균 합격률이 얼마였나.
    # 같은 이름이라도 번호가 다르면 다른 도면이다(근린 공원 323·360·412).
    freq = {}
    for t in tasks:
        f = freq.setdefault((t.title, t.code), {'title': t.title, 'code': t.code,
                                                'rounds': [], 'rates': []})
        f['rounds'].append(t)
        if t.pass_rate is not None:
            f['rates'].append(t.pass_rate)
    freq = list(freq.values())
    for f in freq:
        f['count'] = len(f['rounds'])
        f['avg'] = round(sum(f['rates']) / len(f['rates']), 1) if f['rates'] else None
        f['rounds'].sort(key=lambda t: (t.year, t.round or 0))
        f['last'] = f['rounds'][-1]
    freq.sort(key=lambda f: (-f['count'], -f['last'].year, -(f['last'].round or 0)))
    top = max([f['count'] for f in freq] or [1])
    # 도면마다 색을 하나씩 준다 — 연도표에서 되나온 도면이 한눈에 보이게
    # 도면 색은 사용자가 준 출제 표(2007~2026)의 칸 색을 그대로 쓴다 — 도면 번호로 찾고,
    # 번호가 없는 도면(도시공원)은 이름으로 찾는다. 표에 없는 새 도면은 회색.
    DRAWING_COLORS = {
        '319': '#b38a2e', '323': '#c0632b', '328': '#a9d18e', '401': '#e2efda', '345': '#ffffff',
        '371': '#fff2cc', '434': '#bfbfbf', '360': '#bdd7ee', '365': '#f4b183', '383': '#ffd966',
        '391': '#548235', '412': '#d6dce4', '444': '#ffff00', '428': '#5b9bd5', '454': '#fbe5d6',
        '463': '#808080', '287': '#ffffff', '478': '#4472c4', '264': '#ffffff', '도시공원': '#e03c31',
    }
    for i, f in enumerate(freq):
        f['pct'] = round(f['count'] / top * 100)
        f['color'] = DRAWING_COLORS.get(f['code'] or f['title'], '#d9d9d9')
        f['key'] = f'{f["title"]}{f["code"]}'
        for t in f['rounds']:
            t.color = f['color']
            t.times = f['count']
            t.key = f['key']

    # 기출 도면별 자료 — 투표 줄에 그대로 달아 보인다(도면 번호, 없으면 이름으로 잇는다)
    from .models import GisaDrawingRef
    refs = {}                                 # 한 도면에 자료가 여러 벌이면 탭으로 나눠 보인다
    for r in GisaDrawingRef.objects.filter(certification=cert).prefetch_related('images'):
        refs.setdefault(r.code or r.title, []).append(r)

    def _sheet(rs):
        return [{'ref': r, 'name': r.source or '자료', 'imgs': list(r.images.all()),
                 'html': md.markdown(r.content, extensions=['tables']) if r.content else ''}
                for r in rs]

    tabs_of = {k: _sheet(rs) for k, rs in refs.items()}
    rounds_of = {(f['code'] or f['title']): f for f in freq}

    # 출제 예상 투표 — 실제 출제와 맞대어 본다(투표 몇 위였나, AI 예상은 맞았나)
    colors = {(f['code'] or f['title']): f['color'] for f in freq}
    keys = {(f['code'] or f['title']): f['key'] for f in freq}   # 투표 줄을 누르면 그 도면을 고른다
    used = set()                              # 투표에 실린 자료 — 남는 것은 아래 목록으로
    forecasts = []
    for t in sorted(tasks, key=lambda t: (-t.year, -(t.round or 0))):
        fc = t.forecast or {}
        if not fc.get('items'):
            continue
        items = sorted(fc['items'], key=lambda x: -x['votes'])
        top = max(x['votes'] for x in items) or 1
        voters = fc.get('voters') or top
        hit = None
        for rank, x in enumerate(items, 1):
            x['rank'] = rank
            x['pct'] = round(x['votes'] / top * 100)
            x['share'] = round(x['votes'] / voters * 100)
            x['color'] = colors.get(x['code'] or x['name'], '#9aa5a0')
            x['key'] = keys.get(x['code'] or x['name'], '')
            x['actual'] = bool(t.code) and x['code'] == t.code
            k = x['code'] or x['name']
            # 같은 도면이 여러 회차 투표에 나오면 가장 최근 투표 줄에만 자료를 단다
            x['tabs'] = [] if k in used else tabs_of.get(k, [])
            f = rounds_of.get(k)
            x['rounds'] = f['rounds'] if f else []
            x['count'] = f['count'] if f else 0
            x['avg'] = f['avg'] if f else None
            if x['tabs']:
                used.add(k)
            if x['actual']:
                hit = x
        # 순위·득표는 그대로 두고 **줄 차례만** 바꾼다 — 이미 출제된 도면은 다음 회차에
        # 다시 볼 일이 적어 맨 아래로, '신출'(어느 도면인지 모름)은 그 바로 위로 내린다
        items.sort(key=lambda x: (2 if x['actual'] else (1 if x['name'] == '신출' else 0),
                                  -x['votes']))
        forecasts.append({'task': t, 'source': fc.get('source', ''), 'voters': voters,
                          'items': items, 'hit': hit,
                          'claude_hit': bool(hit and hit.get('claude') == 1),
                          'gemini_hit': bool(hit and hit.get('gemini') == 1)})

    # 연도마다 회차 자리를 고정한다(1·2·4회, 2020년처럼 3회가 있으면 1~4회) —
    # 아직 치르지 않은 회차는 빈 칸으로 남긴다
    for y in years:
        have = {t.round: t for t in y['tasks']}
        rounds = [1, 2, 3, 4] if 3 in have else [1, 2, 4]
        y['slots'] = [{'round': r, 'task': have.get(r)} for r in rounds]
        y['cols'] = len(rounds)

    # 투표 줄에 실리지 않은 자료만 따로 목록으로 — 투표 목록에 없는 도면이 생겼을 때다.
    # (지금은 모든 자료가 투표 줄에 붙어 이 목록이 비어 있다.)
    sheets = []
    for f in freq:
        k = f['code'] or f['title']
        if k in used or k not in tabs_of:
            continue
        sheets.append({**f, 'ref': tabs_of[k][0]['ref'], 'tabs': tabs_of[k]})
        used.add(k)
    for k, tb in tabs_of.items():
        if k in used:
            continue
        r = tb[0]['ref']
        sheets.append({'title': r.title, 'code': r.code, 'count': 0, 'rounds': [], 'avg': None,
                       'color': '#d9d9d9', 'key': f'{r.title}{r.code}',
                       'ref': r, 'tabs': tb})

    notes = {n.slug: n for n in GisaEssayNote.objects.filter(
        certification=cert, slug__in=('work-basics', 'work-elements'))}

    def _note_html(slug):
        n = notes.get(slug)
        return md.markdown(n.content, extensions=['tables']) if n else ''

    # 탭 차례: 동영상 · 기출분석 · 설계 요소 · 자료실 (사용자 결정).
    # **개요와 도면 기본기는 화면에서 내렸다** — 자료(GisaEssayNote `work-basics`)는
    # 지우지 않았으므로 되돌리려면 템플릿에 탭만 도로 넣으면 된다.
    tab = request.GET.get('tab', 'video')
    if tab not in ('video', 'tasks', 'elements', 'res'):
        tab = 'video'               # 옛 주소 ?tab=sheets·overview·basics 는 여기로 받는다
    return render(request, 'gisa/essay_work.html', {
        # 자료실(블로그·사이트)과 동영상(분류별) — 둘 다 part='work' 를 본다
        **resource_tab_context(cert, 'work'),
        **video_tab_context(cert, 'work'),

        'cert': cert,
        'info': info,
        'active_tab': tab,
        'years': years,
        'freq': freq,
        'forecasts': forecasts,
        'sheets': sheets,
        'sheet_ready': len(tabs_of),
        'task_count': len(tasks),
        'basics_html': _note_html('work-basics'),
        'elements_html': _note_html('work-elements'),
    })


@login_required
@require_POST
def drawing_ref_update(request, cert_id, ref_id):
    """기출 도면 자료(작도 팁·수량표)를 그 자리에서 고친다 (스태프 전용, AJAX).

    자료가 hwp·수험서를 옮긴 것이라 오식이 화면에서야 드러난다. 그때마다
    `_ls_drawing_refs/` 를 고쳐 다시 올리는 것은 느리므로 화면에서 바로 고친다.
    (파일 쪽 자료는 그대로이므로, 로더를 다시 돌리면 파일 내용으로 되돌아간다.)

    고친 자리만 다시 그려 돌려준다 — 새로 고치면 펼쳐 둔 도면 줄이 도로 접힌다.
    """
    import markdown as md

    from .models import GisaDrawingRef

    if not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': '권한이 없습니다.'}, status=403)

    ref = get_object_or_404(GisaDrawingRef, pk=ref_id, certification_id=cert_id)
    try:
        data = json.loads(request.body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': '본문을 읽지 못했습니다.'}, status=400)

    if 'content' in data:
        content = str(data['content']).strip()
        if len(content) > 120000:          # SVG 도면이 든 자료는 5~6만 자다(401 My)
            return JsonResponse({'ok': False, 'error': '자료가 너무 깁니다.'}, status=400)
        ref.content = content
    if 'source' in data:
        source = str(data['source']).strip()[:40]
        # 같은 도면에 같은 이름의 자료가 둘이면 고유 키에 걸린다
        if GisaDrawingRef.objects.filter(certification_id=cert_id, code=ref.code,
                                         title=ref.title, source=source).exclude(pk=ref.pk).exists():
            return JsonResponse({'ok': False, 'error': '같은 이름의 자료가 이미 있습니다.'}, status=400)
        ref.source = source
    ref.save()

    for im in ref.images.all():               # 도면 사진 설명
        cap = data.get('captions', {}).get(str(im.pk))
        if cap is not None and str(cap).strip()[:100] != im.caption:
            im.caption = str(cap).strip()[:100]
            im.save(update_fields=['caption'])

    return JsonResponse({
        'ok': True,
        'name': ref.source or '자료',
        'html': md.markdown(ref.content, extensions=['tables']) if ref.content else '',
    })


@login_required
def essay_overview(request, cert_id):
    """시험 개요 — 검정방법·배점·합격기준과 출제기준 주요항목.

    Q-net 종목별 상세정보(취득방법)와 출제기준(2025~2027)을 옮겨 둔 것이라
    DB 가 아니라 `essay_examinfo.EXAM_INFO` 에서 온다. 다만 '우리가 가진 기출'
    현황은 DB 에서 세어 함께 보여 준다 — 개요만 읽고 끝나지 않도록.
    """
    cert = get_object_or_404(Certification, pk=cert_id)
    info = exam_info(cert.name)
    if not info:
        return redirect('gisa:essay_list', cert.pk)

    exam_qs = GisaEssayQuestion.objects.filter(certification=cert, source='기출')
    rounds = sorted(set(exam_qs.order_by().values_list('year', 'round')))
    total = exam_qs.count()
    types = list(exam_qs.values('qtype').annotate(c=Count('id')).order_by('-c'))
    for t in types:
        t['pct'] = round(t['c'] / max(total, 1) * 100)

    # 기사↔산업기사는 필답 범위가 거의 같고 조건만 바꿔 되나오기도 해서,
    # 다른 급수 기출로 건너갈 수 있게 링크를 만든다. **그쪽에 실기 문항이 있을
    # 때만** — 식물보호기사는 자격증은 있어도 실기 필답이 아직 0건이라, 링크를
    # 내면 빈 목록으로 보내게 된다.
    sibling = Certification.objects.filter(name=info.get('sibling', '')).first()
    if sibling and not GisaEssayQuestion.objects.filter(certification=sibling).exists():
        sibling = None

    return render(request, 'gisa/essay_overview.html', {
        'cert': cert,
        'info': info,
        'sibling': sibling,
        'essay_time': hm(info['essay_minutes']),
        # 작업형이 없는 자격증은 work_minutes 가 0 이다. hm(0) 은 '0분'이라
        # 그대로 쓰면 안 되므로 빈 문자열로 둔다(화면도 그 칸을 감춘다).
        'work_time': hm(info['work_minutes']) if info['work_minutes'] else '',
        'total_time': hm(info['essay_minutes'] + info['work_minutes']),
        'round_count': len(rounds),
        'year_from': rounds[0][0] if rounds else '',
        'year_to': rounds[-1][0] if rounds else '',
        'exam_count': total,
        'types': types,
    })


# ------------------------------------------------------------------ 합격 전략

# 자격증 → 합격 전략 문서. **본문에 그 종목의 수치가 박혀 있으므로**(재출제율·
# 분야 비중·"잡초방제학은 건너뛰어도 된다") 다른 종목에서 열면 남의 수치를 읽게
# 된다. 그래서 문서가 있는 종목에만 연다 — `essay_strategy` 와 같은 까닭이다.
PASS_DOCS = {
    '식물보호기사': 'docs/실기합격전략.md',
    '식물보호산업기사': 'docs/실기합격전략.md',
}


def pass_doc_path(cert_name):
    """그 자격증의 합격 전략 문서 경로. 없으면 None."""
    rel = PASS_DOCS.get(cert_name)
    if not rel:
        return None
    path = os.path.join(settings.BASE_DIR, rel)
    return path if os.path.exists(path) else None


@login_required
def essay_pass(request, cert_id):
    """합격 전략 — `docs/실기합격전략.md` 를 그대로 읽어 보여 준다.

    **문서를 한 벌만 둔다.** 같은 글을 템플릿에도 적어 두면 수치를 고칠 때 한쪽만
    고쳐 어긋난다(재출제율은 회차가 늘 때마다 바뀐다). 문서의 머리말(작성 경위와
    갱신 방법)은 회원에게 보일 것이 아니므로 첫 `---` 앞을 잘라 낸다.
    """
    import markdown as md

    cert = get_object_or_404(Certification, pk=cert_id)
    path = pass_doc_path(cert.name)
    if not path:
        return redirect('gisa:essay_list', cert.pk)
    with open(path, encoding='utf-8') as f:
        text = f.read()
    body = text.split('\n---\n', 1)[-1]
    return render(request, 'gisa/essay_pass.html', {
        'cert': cert,
        'info': exam_info(cert.name),
        'body': md.markdown(body, extensions=['tables']),
    })


# ------------------------------------------------------------------ 학습 전략

@login_required
def essay_strategy(request, cert_id):
    """학습 전략 — 기출 분석 결과를 근거로 공부 순서를 안내한다.

    수치는 모두 DB에서 그때그때 계산한다. 회차가 늘면 자동으로 갱신된다.
    """
    from django.db.models import Count, Sum

    cert = get_object_or_404(Certification, pk=cert_id)
    # 본문이 '빈출 58주제 정리'를 전제로 쓰여 있다(58주제·계산 공식 18·예상문제 36건
    # 같은 수치가 문장에 박혀 있다). 그 자료가 없는 자격증에서 열면 남의 수치를 읽게
    # 되므로 목록으로 돌려보낸다 — 조경은 적산 공식 정리만 있으므로 여기 걸린다.
    if not GisaEssayNote.objects.filter(certification=cert, slug='freq58').exists():
        return redirect('gisa:essay_list', cert.pk)

    qs = GisaEssayQuestion.objects.filter(certification=cert)
    exam_qs = qs.filter(source='기출')

    rounds = sorted(set(exam_qs.order_by().values_list('year', 'round')))

    # 빈출 단계별 주제 수 — 몇 주제를 익히면 얼마를 커버하는지 보여 준다
    freq_steps = []
    for lo in (4, 3, 2):
        topics = (exam_qs.filter(freq_rounds__gte=lo)
                  .values('topic_key').distinct().count())
        items = exam_qs.filter(freq_rounds__gte=lo).count()
        if topics:
            freq_steps.append({
                'min': lo, 'topics': topics, 'items': items,
                # 회차당 평균 몇 문항이 이 범위에서 나오는지
                'per_round': round(items / max(1, len(rounds)), 1),
            })

    # 유형 분포
    types = list(exam_qs.values('qtype').annotate(c=Count('id')).order_by('-c'))
    tot_items = exam_qs.count() or 1
    for t in types:
        t['pct'] = round(t['c'] / tot_items * 100)

    # 주제별 분포. 출제기준 8항목은 실무 수행 순서라 학술 지식을 묻는 기출과
    # 맞지 않아, 실제로 무엇을 묻는지로 나눈 topic_group 을 쓴다
    topic_names = dict(topic_groups(cert.name))
    majors = []
    for r in (exam_qs.values('topic_group').annotate(c=Count('id')).order_by('-c')):
        majors.append({
            'name': topic_names.get(r['topic_group'], '미분류'),
            'count': r['c'],
            'pct': round(r['c'] / tot_items * 100),
        })

    # 최상위 빈출 주제 (주제마다 대표 문항 하나)
    top = []
    seen = set()
    for q in exam_qs.filter(freq_rounds__gte=3).order_by('-freq_rounds', 'topic_key',
                                                         '-year', '-round'):
        if q.topic_key in seen:
            continue
        seen.add(q.topic_key)
        top.append(q)

    # 계산 유형 — 공식만 외우면 확보되는 부분이라 따로 모은다
    calc, cseen = [], set()
    for q in exam_qs.filter(qtype='계산').order_by('-freq_rounds', '-year', '-round'):
        if q.topic_key in cseen:
            continue
        cseen.add(q.topic_key)
        calc.append(q)

    return render(request, 'gisa/essay_strategy.html', {
        'cert': cert,
        'total': qs.count(),
        'exam_count': exam_qs.count(),
        'round_count': len(rounds),
        'year_from': rounds[0][0] if rounds else '',
        'year_to': rounds[-1][0] if rounds else '',
        'freq_steps': freq_steps,
        'types': types,
        'majors': majors,
        'top_topics': top,
        'calc_topics': calc[:12],
    })


# ------------------------------------------------------------------ 학습 모드

@login_required
def essay_study(request, cert_id):
    """학습 모드 — 문제와 모범답안을 함께 본다.

    풀지 않고 눈으로 익히는 용도다. 세션을 만들지 않으므로 응시 이력에도
    남지 않고 채점 한도도 쓰지 않는다.

    앞으로 학습 방식이 여러 개 붙을 자리다(암기 카드, 키워드 가리기 등).
    `mode` 파라미터로 갈라 쓴다.
    """
    cert = get_object_or_404(Certification, pk=cert_id)
    source = request.GET.get('source', '기출')
    section = request.GET.get('section', '')
    year = request.GET.get('year')
    round_ = request.GET.get('round')
    study_mode = request.GET.get('mode', 'answer')      # answer | freq

    if study_mode == 'freq':
        # 빈출 학습 — 되풀이 출제된 주제만 모아 회차 수가 많은 순으로 본다.
        # 같은 주제의 여러 문항 중 가장 최근 것 하나만 남긴다.
        min_rounds = int(request.GET.get('min', 2))
        pool = (GisaEssayQuestion.objects
                .filter(certification=cert, source='기출',
                        freq_rounds__gte=min_rounds)
                .order_by('-freq_rounds', 'topic_key', '-year', '-round'))
        seen, questions = set(), []
        for q in pool:
            if q.topic_key in seen:
                continue
            seen.add(q.topic_key)
            questions.append(q)
        title = f'빈출 주제 ({min_rounds}회 이상 출제)'
        year = round_ = None
    elif study_mode == 'comeback':
        # 재출제 유력 — 실기에는 1회만 나왔지만 필기에서 자주 다뤄진 주제.
        # 최근 3개 회차 신규 주제를 역검증하니 81%가 필기 빈출 영역 출신이었다.
        questions = list(GisaEssayQuestion.objects
                         .filter(certification=cert, source='기출',
                                 freq_rounds=1, written_freq__gte=10)
                         .order_by('-written_freq', '-year', '-round'))
        title = '재출제 유력 주제'
        year = round_ = None
    elif study_mode == 'calc':
        # 계산만 몰아 풀기 — 공식이 고정돼 있어 가장 확실하게 점수가 되는 유형.
        # 같은 공식(topic_key)끼리 붙여 두어 수치만 바뀐 반복을 눈으로 확인한다.
        questions = list(GisaEssayQuestion.objects
                         .filter(certification=cert, source='기출', qtype='계산')
                         .order_by('-freq_rounds', 'topic_key', '-year', '-round'))
        title = '계산 문항 전체'
        year = round_ = None
    else:
        qs = GisaEssayQuestion.objects.filter(certification=cert, source=source)
        if source in ESSAY_ROUND_SOURCES:
            year = int(year) if year else None
            round_ = int(round_) if round_ else None
            qs = qs.filter(year=year, round=round_)
            title = (f'{year}년 {round_}회' if source == '기출'
                     else f'학원예상시험 {round_}회')
        else:
            qs = qs.filter(section=section)
            title = section
        questions = list(qs.order_by('number'))

    if not questions:
        return redirect('gisa:essay_list', cert_id=cert_id)

    return render(request, 'gisa/essay_study.html', {
        'cert': cert,
        'title': title,
        'source': source,
        'section': section,
        'year': year,
        'round': round_,
        'questions': questions,
        'study_mode': study_mode,
        'total_points': round(sum(float(q.points) for q in questions), 1),
    })


# ------------------------------------------------------------------ 결과

@login_required
def essay_result(request, cert_id, session_id):
    cert = get_object_or_404(Certification, pk=cert_id)
    session = _result_session(request, session_id, cert_id)
    attempts = list(session.attempts.select_related('question').order_by('question__number'))

    # 주제별 득점률 — 어느 주제가 약한지 파악용
    by_major = {}
    for a in attempts:
        m = a.question.topic_group
        d = by_major.setdefault(m, {'got': 0.0, 'max': 0.0, 'count': 0})
        d['got'] += a.score
        d['max'] += float(a.question.points)
        d['count'] += 1
    majors = []
    # 분류 이름은 자격증마다 다르다. TOPIC_CHOICES 는 자연생태복원 것이라 식물보호
    # 결과에 '생태학 기초'·'경관생태'가 나오고 9~11번은 미분류로 떴다
    topic_names = dict(topic_groups(cert.name))
    for m, d in sorted(by_major.items()):
        majors.append({
            'no': m, 'name': topic_names.get(m, '미분류'),
            'got': round(d['got'], 1), 'max': round(d['max'], 1),
            'count': d['count'],
            'pct': round(d['got'] / d['max'] * 100) if d['max'] else 0,
        })

    # 색연필 첨삭에 쓰는 채점 결과 — 화면 스크립트가 답안지 위에 그린다.
    # 점수는 사용자가 조정한 값(final_score)이 있으면 그것이다(attempt.score)
    pen_items = {}
    for a in attempts:
        fb = a.feedback if isinstance(a.feedback, dict) else {}
        pen_items[a.pk] = {
            'score': a.score, 'max': float(a.question.points),
            'points': fb.get('points') or [], 'summary': fb.get('summary') or '',
            'marks': fb.get('marks') or [], 'missing': fb.get('missing') or [],
            'answer': a.answer_text or '',
        }

    return render(request, 'gisa/essay_result.html', {
        'cert': cert,
        'session': session,
        'attempts': attempts,
        'majors': majors,
        'pen_items': pen_items,
        # 시험지 사진을 곧게 펴 판독한 세션이면 '내 시험지 첨삭'을 보여 준다
        'has_sheet': session.mode == 'paper' and session.uploads.filter(
            transcribed=True).exclude(flat_image='').exists(),
        # 관리자가 채점관리에서 남의 결과를 여는 경우 — 점수 조정은 막고 응시자를 밝힌다
        'admin_view': session.user_id != request.user.id,
    })


def _result_session(request, session_id, cert_id):
    """결과·첨삭 화면의 세션. 본인 것이거나, 관리자면 누구 것이든 연다(채점관리)."""
    q = Q(pk=session_id, certification_id=cert_id)
    if not request.user.is_staff:
        q &= Q(user=request.user)
    return get_object_or_404(GisaEssaySession.objects.select_related('user'), q)


@login_required
def essay_overlay(request, cert_id, session_id):
    """편 시험지 사진 위에 그릴 첨삭 자리(JSON) — 결과 화면이 SVG 로 그린다."""
    from .essay_overlay import build_overlay
    session = _result_session(request, session_id, cert_id)
    return JsonResponse({'ok': True, 'pages': build_overlay(session)})


@login_required
@require_POST
def essay_adjust(request, cert_id, attempt_id):
    """사용자가 채점 점수를 조정한다 (AI 오채점 보정)."""
    attempt = get_object_or_404(
        GisaEssayAttempt, pk=attempt_id, session__user=request.user,
        session__certification_id=cert_id)
    try:
        score = float(request.POST.get('score', 0))
    except ValueError:
        return JsonResponse({'ok': False, 'error': '점수 형식 오류'}, status=400)

    score = max(0.0, min(score, float(attempt.question.points)))
    attempt.final_score = score
    attempt.save(update_fields=['final_score'])

    session = attempt.session
    total = sum(a.score for a in session.attempts.all())
    session.score = round(total, 2)
    session.save(update_fields=['score'])

    return JsonResponse({
        'ok': True, 'score': score,
        'session_score': session.score,
        'percent': session.percent,
    })


# ------------------------------------------------------------------ 시험지 인쇄·사진

@login_required
def essay_sheet(request, cert_id, session_id):
    """인쇄용 시험지. 페이지마다 세션 코드와 사진 보정용 모서리 마커를 찍는다."""
    from .essay_rectify import marker_svgs
    cert = get_object_or_404(Certification, pk=cert_id)
    session = get_object_or_404(GisaEssaySession, pk=session_id,
                                user=request.user, certification=cert)
    qs = GisaEssayQuestion.objects.filter(certification=cert, source=session.source)
    if session.source in ESSAY_ROUND_SOURCES:
        qs = qs.filter(year=session.year, round=session.round)
    else:
        qs = qs.filter(section=session.section)
    questions = list(qs.order_by('number'))
    # 시험지 머리말의 배점·시간도 자격증마다 다르다(45점 90분을 박아 두었었다).
    _info = exam_info(cert.name)
    return render(request, 'gisa/essay_sheet.html', {
        'cert': cert, 'session': session, 'questions': questions,
        'sheet_points': sum(q.points for q in questions),
        'sheet_minutes': (_info or {}).get('essay_minutes', 90),
        'sheet_markers': marker_svgs(),
    })


def _flatten_upload(up):
    """업로드 한 장을 곧게 펴 flat_image 에 둔다. 실패해도 판독은 원본으로 이어 간다."""
    from django.core.files.base import ContentFile
    from .essay_rectify import rectify_bytes
    try:
        up.image.open('rb')
        data = up.image.read()
        up.image.close()
        out, method, info = rectify_bytes(data)
    except Exception as e:                  # 사진이 깨졌거나 보정이 터져도 업로드는 살린다
        out, method, info = None, 'none', {'error': str(e)[:200]}
    up.flat_method = method
    up.flat_info = info
    if out and method != 'none':
        up.flat_image.save('flat.jpg', ContentFile(out), save=False)
    up.save()
    return up


def _new_upload(session, f):
    """다음 쪽 번호로 업로드를 만든다.

    사진 여러 장을 한꺼번에 고르면 요청이 겹쳐 같은 번호를 잡는다(session, page_no
    고유 제약에 걸려 한 장이 500 이 났다). 걸리면 번호를 올려 다시 넣는다.
    """
    from django.db import IntegrityError, transaction
    from django.db.models import Max
    for _ in range(5):
        page_no = (session.uploads.aggregate(m=Max('page_no'))['m'] or 0) + 1
        up = GisaEssayUpload(session=session, page_no=page_no, image=f)
        try:
            with transaction.atomic():
                up.save()
                return up
        except IntegrityError:
            # 파일은 INSERT 보다 먼저 저장된다 — 실패한 번호로 쓴 파일을 지우고 다시
            if up.image and up.image.name:
                up.image.storage.delete(up.image.name)
            f.seek(0)
            continue
    raise RuntimeError('쪽 번호를 잡지 못했습니다')


def _upload_json(up):
    from .essay_rectify import METHOD_LABELS
    img = up.flat_image if up.flat_image else up.image
    return {'upload_id': up.pk, 'page_no': up.page_no, 'url': img.url,
            'method': up.flat_method or 'none',
            'label': METHOD_LABELS.get(up.flat_method or 'none', '')}


def _drop_upload(up):
    for f in (up.image, up.flat_image):
        if f:
            f.delete(save=False)
    up.delete()


@login_required
@require_POST
def essay_flatten(request, cert_id, session_id):
    """사진 한 장을 받아 곧게 편 결과를 미리 보여 준다(판독 전).

    판독은 장마다 API 를 부르고 하루 한도도 장수로 센다. 사진이 잘렸거나 펴지지
    않은 것을 판독 **전에** 보여 주어 다시 찍을 기회를 준다. 여기서 만든 업로드는
    판독하기 전까지 한도에 들지 않는다(_daily_count 는 transcribed 만 센다).
    """
    cert = get_object_or_404(Certification, pk=cert_id)
    session = get_object_or_404(GisaEssaySession, pk=session_id,
                                user=request.user, certification=cert)
    f = request.FILES.get('image')
    if not f:
        return JsonResponse({'ok': False, 'error': '이미지가 없습니다'}, status=400)

    # 올리고 판독하지 않은 채 버려진 사진은 하루 지나면 치운다
    stale = GisaEssayUpload.objects.filter(
        session__user=request.user, transcribed=False,
        uploaded_at__lt=timezone.now() - timedelta(days=1))
    for up in stale:
        _drop_upload(up)
    if session.uploads.filter(transcribed=False).count() >= 40:
        return JsonResponse({'ok': False, 'error': '판독하지 않은 사진이 너무 많습니다. 판독하거나 빼 주세요.'},
                            status=429)

    up = _new_upload(session, f)
    _flatten_upload(up)
    return JsonResponse({'ok': True, **_upload_json(up)})


@login_required
@require_POST
def essay_upload_remove(request, cert_id, session_id):
    """판독 전 사진을 뺀다(다시 찍을 때)."""
    session = get_object_or_404(GisaEssaySession, pk=session_id,
                                user=request.user, certification_id=cert_id)
    up = session.uploads.filter(pk=request.POST.get('upload_id'), transcribed=False).first()
    if up:
        _drop_upload(up)
    return JsonResponse({'ok': True})


@login_required
@require_POST
def essay_upload(request, cert_id, session_id):
    """시험지 사진 판독 → Gemini로 손글씨 판독.

    보통은 essay_flatten 으로 미리 올려 편 사진의 upload_id 를 보낸다. 사진 파일을
    곧바로 보내도 된다(그때는 여기서 편다).
    """
    cert = get_object_or_404(Certification, pk=cert_id)
    session = get_object_or_404(GisaEssaySession, pk=session_id,
                                user=request.user, certification=cert)

    limit = getattr(settings, 'ESSAY_DAILY_OCR_LIMIT', 40)
    if _daily_count(request.user, 'ocr') >= limit:
        return JsonResponse({'ok': False,
                             'error': f'하루 판독 한도({limit}장)를 초과했습니다.'}, status=429)

    uploads = list(session.uploads.filter(
        pk__in=request.POST.getlist('upload_id'), transcribed=False).order_by('page_no'))
    files = request.FILES.getlist('images')
    if not uploads and not files:
        return JsonResponse({'ok': False, 'error': '이미지가 없습니다'}, status=400)

    for f in files:
        uploads.append(_flatten_upload(_new_upload(session, f)))

    try:
        from .essay_ocr import transcribe_uploads
        results, rejected = transcribe_uploads(session, uploads)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'판독 실패: {e}'}, status=500)

    # 이 시험지가 아닌 사진은 업로드 기록도 지운다 — 남겨 두면 쪽 번호가
    # 밀리고 하루 판독 한도까지 먹는다.
    bad_pages = {r['page_no'] for r in rejected if r['reason'].startswith('다른 시험지')}
    for up in uploads:
        if up.page_no in bad_pages:
            _drop_upload(up)

    if not results and rejected:
        return JsonResponse({'ok': False, 'error': rejected[0]['reason'],
                             'rejected': rejected}, status=422)
    return JsonResponse({'ok': True, 'answers': results, 'rejected': rejected})


@login_required
@require_POST
def essay_confirm(request, cert_id, session_id):
    """판독 결과를 사용자가 확인·수정한 뒤 채점한다."""
    cert = get_object_or_404(Certification, pk=cert_id)
    session = get_object_or_404(GisaEssaySession, pk=session_id,
                                user=request.user, certification=cert)

    for key, val in request.POST.items():
        if not key.startswith('answer_'):
            continue
        qid = key[len('answer_'):]
        q = GisaEssayQuestion.objects.filter(pk=qid, certification=cert).first()
        if not q:
            continue
        att, _ = GisaEssayAttempt.objects.update_or_create(
            session=session, question=q,
            defaults={'answer_text': val.strip(), 'transcribe_confirmed': True},
        )

    session.status = 'grading'
    session.save(update_fields=['status'])
    grade_session(session)
    return redirect('gisa:essay_result', cert_id=cert_id, session_id=session.pk)


# ------------------------------------------------------------------ 단건 채점(학습 모드)

@login_required
@require_POST
def essay_grade_one(request, cert_id, question_id):
    """문항 하나만 즉시 채점한다.

    학습 모드(예상·오답)뿐 아니라 **기출·모의 풀이 화면의 '바로 채점'** 도 이리
    온다. `session` 이 함께 오면 그 세션의 답안에 점수를 적어 둔다 — 그래야
    제출할 때 같은 답을 다시 채점하지 않는다(`grade_session` 이 건너뛴다).
    한 문항을 확인하며 20문항을 풀면 LLM 호출이 두 배가 되고, 같은 답인데
    점수가 달라지는 일도 생긴다.
    """
    cert = get_object_or_404(Certification, pk=cert_id)
    q = get_object_or_404(GisaEssayQuestion, pk=question_id, certification=cert)
    answer = request.POST.get('answer', '').strip()

    try:
        result = grade_answer(q, answer)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)

    sid = request.POST.get('session')
    if sid:
        session = GisaEssaySession.objects.filter(
            pk=sid, user=request.user, certification=cert,
            status='progress').first()
        if session is not None:
            # 채점한 답안을 함께 남긴다 — 제출할 때 답이 그대로인지 견주는 열쇠다
            res = dict(result, answer=answer)
            GisaEssayAttempt.objects.update_or_create(
                session=session, question=q,
                defaults={'answer_text': answer, 'ai_score': result['score'],
                          'feedback': res, 'graded_at': timezone.now()})

    return JsonResponse({
        'ok': True,
        'score': result['score'], 'max': result['max'],
        'engine': result['engine'],
        'points': result['points'],
        'summary': result['summary'],
        # 첨삭 — 퀴즈 화면이 답안 위에 색연필로 겹쳐 그린다
        'marks': result.get('marks') or [],
        'missing': result.get('missing') or [],
        'answer_items': q.answer_items,
        'answer_text': q.answer_text,
        # 해설에는 표·도해가 들어가므로 서버에서 렌더링해 보낸다.
        # 브라우저에서 escape 하면 표는 파이프 문자로, 그림은 태그 글자로 보인다
        'reference_html': str(qtext(q.reference)) if q.reference else '',
        # 퀴즈 화면은 학습 화면과 같은 조각으로 모범답안·해설을 그린다
        'answer_html': _essay_answer_html(q),
    })


def essay_siblings(request, cert_id, question_id):
    """같은 주제로 묶인 다른 회차 문항들을 돌려준다.

    같은 개념이 회차마다 어떤 형태로 바뀌어 나왔는지 나란히 보면, 표현이
    달라져도 묻는 것이 같다는 걸 알게 된다. 답까지 함께 보내 대조할 수 있게 한다.

    **묶음 전체에서 찾는다**(`siblings`). 쪽집게 노트가 기사와 산업기사를 한
    덩어리로 보여 주므로 대표 문항이 다른 급수일 수 있다 — `certification=cert`
    로 좁혔더니 기사 페이지에서 산업기사 대표 문항을 눌러 404 가 났다.
    """
    cert = get_object_or_404(Certification, pk=cert_id)
    names = siblings(cert.name)
    q = get_object_or_404(GisaEssayQuestion, pk=question_id,
                          certification__name__in=names)
    if not q.topic_key:
        return JsonResponse({'ok': True, 'items': []})

    sibs = (GisaEssayQuestion.objects
            .filter(certification__name__in=names, topic_key=q.topic_key)
            .select_related('certification')
            .order_by('-year', '-round', 'number'))
    # 학습 화면은 지금 보는 문항을 빼고 "다른 회차"만 보여주지만,
    # 정리 문서(?all=1)에서는 그 회차 자신까지 전부 나열한다
    if request.GET.get('all') != '1':
        sibs = sibs.exclude(pk=q.pk)
    # 기출을 앞에, 학원예상은 뒤에 — 같은 "26-2" 라도 실제 출제가 먼저 펼쳐져야 한다
    sibs = sorted(sibs, key=lambda s: s.source == '학원')

    # 묶음이면 급수를 함께 보낸다 — "25-2" 만으로는 두 급수 가운데 어느
    # 시험지에 나온 것인지 알 수 없다. **`label` 에 붙이지는 않는다** —
    # 화면이 `label.slice(0, 4)` 로 연도를 떼어 쓰므로 앞에 글자가 붙으면
    # 연도 파싱이 깨진다.
    def _grade(s):
        if s.source == '학원':          # 학원 문항도 같은 주제로 묶여 함께 온다
            return '학원'
        if len(names) < 2:
            return ''
        return '산기' if s.certification.category == '산업기사' else '기사'

    items = [{
        'pk': s.pk,
        'label': f'{s.year}-{s.round}',
        'grade': _grade(s),
        'number': s.number,
        'orig_number': s.orig_number,
        'qtype': s.get_qtype_display(),
        'points': s.points,
        'text_html': str(qtext(s.text)),
        # 답 항목도 서버에서 렌더링한다. 원번호·첨자·표가 들어 있어 그대로
        # 넣으면 글자로 보이고, escape 없이 넣으면 위험하다
        'answer_html_items': [str(qtext(it)) for it in (s.answer_items or [])],
        'answer_html': str(qtext(s.answer_text)) if s.answer_text else '',
    } for s in sibs]
    return JsonResponse({'ok': True, 'items': items})


@login_required
@require_POST
def essay_wrong_dismiss(request, cert_id, question_id):
    """오답노트 "노트 X" — 이 문항의 가장 최근 답안에 제외 표시를 한다.

    필기의 wrong_dismiss 는 정답 응시를 하나 만들어 빼지만, 실기는 응시가 세션
    단위라 그렇게 하면 이력이 어지러워진다. 답안에 표시만 남긴다.
    """
    cert = get_object_or_404(Certification, pk=cert_id)
    a = (GisaEssayAttempt.objects
         .filter(session__user=request.user, session__certification=cert,
                 session__status='done', question_id=question_id)
         .exclude(answer_text='')
         .order_by('-session__submitted_at').first())
    if a is None:
        return JsonResponse({'ok': False, 'error': '해당 문항의 답안이 없습니다.'}, status=404)
    a.wrong_dismissed = True
    a.save(update_fields=['wrong_dismissed'])
    return JsonResponse({'ok': True, 'remaining': len(_wrong_attempts(request.user, cert))})


@login_required
@require_POST
def essay_session_delete(request, cert_id, session_id):
    """시험이력에서 응시 하나를 지운다. 답안·업로드 사진은 CASCADE 로 함께 지워진다."""
    cert = get_object_or_404(Certification, pk=cert_id)
    s = get_object_or_404(GisaEssaySession, pk=session_id, user=request.user, certification=cert)
    for up in s.uploads.all():
        up.image.delete(save=False)
    s.delete()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})
    return redirect(reverse('gisa:essay_list', args=[cert.pk]) + '?tab=history')


@login_required
@require_POST
def essay_session_delete_all(request, cert_id):
    """내 실기 응시 기록 전체 삭제."""
    cert = get_object_or_404(Certification, pk=cert_id)
    qs = GisaEssaySession.objects.filter(user=request.user, certification=cert)
    for up in GisaEssayUpload.objects.filter(session__in=qs):
        up.image.delete(save=False)
    qs.delete()
    return redirect(reverse('gisa:essay_list', args=[cert.pk]) + '?tab=history')


@login_required
def essay_note(request, cert_id, slug):
    """실기 학습자료 (빈출 주제 정리 등).

    마크다운을 그대로 렌더링한다. 주제가 58개라 한 화면에 다 펼치면 길어지므로,
    `## N회 · 분류 · 주제` 단위로 잘라 접을 수 있게 한다.
    """
    import re
    import markdown as md
    from .essay_textbook import parse_note_items

    cert = get_object_or_404(Certification, pk=cert_id)
    note = get_object_or_404(GisaEssayNote, certification=cert, slug=slug)

    # 파싱은 쪽집게 노트(essay_textbook)와 같은 함수를 쓴다
    intro_md, items = parse_note_items(cert, note)

    # 머리말의 목차는 카드 목록이 대신하므로 걷어낸다
    intro_md = re.split(r'^## 목차', intro_md, flags=re.M)[0]

    return render(request, 'gisa/essay_note.html', {
        'cert': cert,
        'note': note,
        'intro': md.markdown(intro_md, extensions=['tables']),
        'items': items,
        # 빈도·분류 배지가 있는 노트인지(자연생태복원 빈출 정리) 여부.
        # 조경 적산 정리처럼 `## 제목` 만 쓰는 노트는 배지와 걸러 보기를 감춘다.
        'has_freq': any(x['freq'] for x in items),
        # 빈칸 암기 노트(⟦답⟧)면 머리에 "빈칸 모두 보기" 단추를 둔다
        'has_blanks': '⟦' in note.content,
        'warned_count': sum(1 for x in items if x['warned']),
    })


# ── 관리자 인라인 편집 ────────────────────────────────────────────────────
# 판독본에 오식이 남아 있고 그림이 원도와 다른 것이 학습 화면에서야 드러난다.
# 그때마다 스크립트를 새로 써서 고치는 것은 느리고, 무엇을 고쳤는지도 흩어진다.
# 화면에서 바로 고칠 수 있게 두되 **스태프만** 쓴다.
_EDIT_FIELDS = ('text', 'answer_text', 'reference')

# 글자 수 상한 — 사람이 손으로 적는 칸은 넉넉히, 답 서술은 자작 SVG 가 통째로
# 들어가므로(뿌리분 그림이 3,700자다) 훨씬 크게 잡는다.
_EDIT_MAX = {'text': 20000, 'answer_text': 200000, 'reference': 20000}
_ITEM_MAX = 8000


@login_required
@require_POST
def essay_question_update(request, cert_id, question_id):
    """문제문·답 항목·답 서술·해설을 고친다 (스태프 전용, AJAX).

    고친 뒤에는 **그 자리만 다시 그려 돌려준다** — 새로 고치면 열어 둔 답이
    도로 접히고 읽던 자리를 잃는다. 문제문은 qtext 를 그대로 태우고, 답 영역은
    화면과 같은 조각(`gisa/_essay_answer.html`)을 렌더한다.
    """
    if not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': '권한이 없습니다.'}, status=403)

    q = get_object_or_404(GisaEssayQuestion, pk=question_id, certification_id=cert_id)
    try:
        data = json.loads(request.body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': '본문을 읽지 못했습니다.'}, status=400)

    changed = []

    # 답 항목 — 빈 칸은 버린다(화면에서 × 로 지우지 않고 비워 두는 사람이 있다)
    if 'items' in data:
        raw = data['items']
        if not isinstance(raw, list):
            return JsonResponse({'ok': False, 'error': '답 항목 형식이 잘못됐습니다.'},
                                status=400)
        items = [str(x).strip() for x in raw]
        items = [x for x in items if x]
        if any(len(x) > _ITEM_MAX for x in items):
            return JsonResponse({'ok': False, 'error': '답 항목이 너무 깁니다.'},
                                status=400)
        if items != q.answer_items:
            q.answer_items = items
            changed.append('answer_items')

    for f in _EDIT_FIELDS:
        if f not in data:
            continue
        v = str(data[f]).strip()
        if len(v) > _EDIT_MAX[f]:
            return JsonResponse({'ok': False, 'error': f'{f} 가 너무 깁니다.'}, status=400)
        if f == 'text' and not v:
            return JsonResponse({'ok': False, 'error': '문제문은 비울 수 없습니다.'},
                                status=400)
        if v != getattr(q, f):
            setattr(q, f, v)
            changed.append(f)

    if not changed:
        return JsonResponse({'ok': True, 'changed': [], 'text_html': qtext(q.text),
                             'ans_html': _essay_answer_html(q)})

    # 채점 기준표는 답 항목에서 파생된다(`build_rubric`). 답을 고쳤는데 예전
    # 기준표가 남아 있으면 화면과 채점이 어긋나므로 비워 다시 만들게 한다.
    if 'answer_items' in changed and q.rubric:
        q.rubric = []
        changed.append('rubric')

    q.save(update_fields=changed)
    return JsonResponse({'ok': True, 'changed': changed, 'text_html': qtext(q.text),
                         'ans_html': _essay_answer_html(q)})


def _essay_answer_html(q):
    from django.template.loader import render_to_string
    return render_to_string('gisa/_essay_answer.html', {'q': q})


# ------------------------------------------------------------------ 관리 · 채점관리

GRADING_PAGE = 30


@login_required
def essay_grading_manage(request):
    """채점관리 — 채점을 마친 실기 필답형 세션 목록 (스태프 전용).

    관리 메뉴의 한 탭이다. 줄을 누르면 응시자의 채점 결과 화면(essay_result)을
    그대로 연다 — 관리자는 남의 세션도 열 수 있고, 점수 조정만 막힌다.
    """
    if not request.user.is_staff:
        return redirect('main:index')

    base = GisaEssaySession.objects.filter(status='done')
    qs = base.select_related('user', 'certification').annotate(
        n_q=Count('attempts'),
        n_wrote=Count('attempts', filter=~Q(attempts__answer_text='')),
    ).order_by('-submitted_at', '-started_at')

    cert = request.GET.get('cert', '')
    if cert.isdigit():
        qs = qs.filter(certification_id=int(cert))
    user_q = request.GET.get('q', '').strip()
    if user_q:
        qs = qs.filter(Q(user__username__icontains=user_q) | Q(user__first_name__icontains=user_q)
                       | Q(user__last_name__icontains=user_q))
    mode = request.GET.get('mode', '')
    if mode in dict(GisaEssaySession.MODE_CHOICES):
        qs = qs.filter(mode=mode)

    try:
        page = max(1, int(request.GET.get('page', 1)))
    except ValueError:
        page = 1
    total = qs.count()
    pages = max(1, (total + GRADING_PAGE - 1) // GRADING_PAGE)
    page = min(page, pages)
    rows = list(qs[(page - 1) * GRADING_PAGE: page * GRADING_PAGE])
    for r in rows:                            # 답을 안 쓴 문항은 0점 — 점수가 낮은 까닭이 여기 있다
        r.n_blank = r.n_q - r.n_wrote

    certs = (Certification.objects.filter(pk__in=base.values('certification_id'))
             .annotate(n=Count('gisaessaysession', filter=Q(gisaessaysession__status='done')))
             .order_by('name'))
    keep = request.GET.copy()
    keep.pop('page', None)
    return render(request, 'gisa/essay_grading_manage.html', {
        'rows': rows, 'total': total, 'page': page, 'pages': pages,
        'certs': certs, 'cert': cert, 'user_q': user_q, 'mode': mode,
        'modes': GisaEssaySession.MODE_CHOICES,
        'people': base.values('user').distinct().count(),
        'keep': keep.urlencode(),
    })
