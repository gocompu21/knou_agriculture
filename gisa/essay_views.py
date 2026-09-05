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

from .essay_grading import grade_answer, grade_session
from .templatetags.gisa_filters import qtext
from main.models import QnaQuestion
from .models import (Certification, GisaEssayAttempt, GisaEssayNote,
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

    sections = (qs.filter(source='예상')
                .values('section')
                .annotate(c=Count('id'))
                .order_by('section'))

    # 화면만 열었다 나간 세션은 이력을 어지럽히므로 치운다.
    # 답을 하나도 쓰지 않았고, 인쇄용 시험지도 아니고, 하루가 지난 것.
    # (시험지 모드는 인쇄만 해두고 며칠 뒤 답을 올리는 흐름이라 남긴다)
    try:
        stale = timezone.now() - timedelta(days=1)
        (GisaEssaySession.objects
         .filter(user=request.user, certification=cert, status='progress',
                 mode='online', started_at__lt=stale, attempts__isnull=True)
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
            user=request.user, certification=cert, status='done', source='기출'):
        key = (s.year, s.round)
        if key not in best or s.score > best[key]:
            best[key] = s.score

    # 실제 시험은 15문항 안팎 45점이다. 복원이 일부만 된 회차는
    # 문항 수와 배점이 그에 못 미치므로 카드에 그 사실을 알린다.
    FULL_POINTS = 45
    round_cards = []
    for r in rounds:
        key = (r['year'], r['round'])
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

    tab = request.GET.get('tab', 'textbook')
    if tab not in ('textbook', 'study', 'solve', 'mock', 'wrong', 'history', 'qna'):
        tab = 'textbook'

    return render(request, 'gisa/essay_list.html', {
        'cert': cert,
        'active_tab': tab,
        'wrong_items': wrong,
        'wrong_count': len(wrong),
        'mock_size': MOCK_SIZE,
        'mock_sessions': [s for s in sessions if s.source == '모의' and s.status == 'done'][:5],
        'round_cards': round_cards,
        'round_years': round_years,
        'sections': sections,
        'freq_cards': freq_cards,
        'comeback_count': comeback_count,
        'notes': GisaEssayNote.objects.filter(certification=cert),
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
        if a.score < float(a.question.points):
            wrong.append(a)
    wrong.sort(key=lambda a: (-a.question.year, -a.question.round, a.question.number))
    return wrong


def _pick_mock(cert):
    """모의고사 — 기출 전체에서 주제가 겹치지 않게 무작위로 뽑는다.

    같은 주제(topic_key)가 두 번 나오면 한 회차 시험답지 않다. 최근 회차의
    문항이 조금 더 자주 뽑히도록 연도에 가중치를 둔다.
    """
    pool = list(GisaEssayQuestion.objects.filter(certification=cert, source='기출'))
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
        if len(picked) >= MOCK_SIZE:
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
    if source == '기출':
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
            code = f'{year}-{round_}' if source == '기출' else section[:12]
        section_val = {'예상': section, '기출': '기출', '모의': '모의고사',
                       '오답': '오답 재풀이'}.get(source, source)
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

    # 실전(기출·모의)은 90분 타이머, 학습(예상·오답)은 무제한
    time_limit = 90 * 60 if source in ('기출', '모의') else 0

    return render(request, 'gisa/essay_take.html', {
        'cert': cert,
        'session': session,
        'questions': questions,
        'total_points': total_points,
        'time_limit': time_limit,
        'is_exam': source in ('기출', '모의'),
        # 여러 회차를 섞은 세트는 원래 문항 번호가 겹치므로 순번으로 보여 준다
        'seq_numbers': source in ('모의', '오답'),
    })


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

    # 이미 채점됐으면 다시 호출하지 않는다 (새로고침·중복 요청 대비)
    if attempt.graded_at:
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
    attempt.feedback = result
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


# ------------------------------------------------------------------ 학습 전략

@login_required
def essay_strategy(request, cert_id):
    """학습 전략 — 기출 분석 결과를 근거로 공부 순서를 안내한다.

    수치는 모두 DB에서 그때그때 계산한다. 회차가 늘면 자동으로 갱신된다.
    """
    from django.db.models import Count, Sum

    cert = get_object_or_404(Certification, pk=cert_id)
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
    topic_names = dict(GisaEssayQuestion.TOPIC_CHOICES)
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
        if source == '기출':
            year = int(year) if year else None
            round_ = int(round_) if round_ else None
            qs = qs.filter(year=year, round=round_)
            title = f'{year}년 {round_}회'
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
    session = get_object_or_404(GisaEssaySession, pk=session_id,
                                user=request.user, certification=cert)
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
    topic_names = dict(GisaEssayQuestion.TOPIC_CHOICES)
    for m, d in sorted(by_major.items()):
        majors.append({
            'no': m, 'name': topic_names.get(m, '미분류'),
            'got': round(d['got'], 1), 'max': round(d['max'], 1),
            'count': d['count'],
            'pct': round(d['got'] / d['max'] * 100) if d['max'] else 0,
        })

    return render(request, 'gisa/essay_result.html', {
        'cert': cert,
        'session': session,
        'attempts': attempts,
        'majors': majors,
    })


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
    """인쇄용 시험지. 페이지마다 세션 코드를 넣어 업로드 시 매칭한다."""
    cert = get_object_or_404(Certification, pk=cert_id)
    session = get_object_or_404(GisaEssaySession, pk=session_id,
                                user=request.user, certification=cert)
    qs = GisaEssayQuestion.objects.filter(certification=cert, source=session.source)
    if session.source == '기출':
        qs = qs.filter(year=session.year, round=session.round)
    else:
        qs = qs.filter(section=session.section)
    questions = list(qs.order_by('number'))
    return render(request, 'gisa/essay_sheet.html', {
        'cert': cert, 'session': session, 'questions': questions,
    })


@login_required
@require_POST
def essay_upload(request, cert_id, session_id):
    """시험지 사진 업로드 → Gemini로 손글씨 판독."""
    cert = get_object_or_404(Certification, pk=cert_id)
    session = get_object_or_404(GisaEssaySession, pk=session_id,
                                user=request.user, certification=cert)

    limit = getattr(settings, 'ESSAY_DAILY_OCR_LIMIT', 40)
    if _daily_count(request.user, 'ocr') >= limit:
        return JsonResponse({'ok': False,
                             'error': f'하루 판독 한도({limit}장)를 초과했습니다.'}, status=429)

    files = request.FILES.getlist('images')
    if not files:
        return JsonResponse({'ok': False, 'error': '이미지가 없습니다'}, status=400)

    uploads = []
    start = session.uploads.count()
    for i, f in enumerate(files, start=start + 1):
        up = GisaEssayUpload.objects.create(session=session, page_no=i, image=f)
        uploads.append(up)

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
            up.image.delete(save=False)
            up.delete()

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
    """학습 모드에서 문항 하나만 즉시 채점한다."""
    cert = get_object_or_404(Certification, pk=cert_id)
    q = get_object_or_404(GisaEssayQuestion, pk=question_id, certification=cert)
    answer = request.POST.get('answer', '').strip()

    try:
        result = grade_answer(q, answer)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)

    return JsonResponse({
        'ok': True,
        'score': result['score'], 'max': result['max'],
        'engine': result['engine'],
        'points': result['points'],
        'summary': result['summary'],
        'answer_items': q.answer_items,
        'answer_text': q.answer_text,
        # 해설에는 표·도해가 들어가므로 서버에서 렌더링해 보낸다.
        # 브라우저에서 escape 하면 표는 파이프 문자로, 그림은 태그 글자로 보인다
        'reference_html': str(qtext(q.reference)) if q.reference else '',
    })


def essay_siblings(request, cert_id, question_id):
    """같은 주제로 묶인 다른 회차 문항들을 돌려준다.

    같은 개념이 회차마다 어떤 형태로 바뀌어 나왔는지 나란히 보면, 표현이
    달라져도 묻는 것이 같다는 걸 알게 된다. 답까지 함께 보내 대조할 수 있게 한다.
    """
    cert = get_object_or_404(Certification, pk=cert_id)
    q = get_object_or_404(GisaEssayQuestion, pk=question_id, certification=cert)
    if not q.topic_key:
        return JsonResponse({'ok': True, 'items': []})

    sibs = (GisaEssayQuestion.objects
            .filter(certification=cert, topic_key=q.topic_key)
            .order_by('-year', '-round', 'number'))
    # 학습 화면은 지금 보는 문항을 빼고 "다른 회차"만 보여주지만,
    # 정리 문서(?all=1)에서는 그 회차 자신까지 전부 나열한다
    if request.GET.get('all') != '1':
        sibs = sibs.exclude(pk=q.pk)

    items = [{
        'pk': s.pk,
        'label': f'{s.year}-{s.round}',
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
def essay_note(request, cert_id, slug):
    """실기 학습자료 (빈출 주제 정리 등).

    마크다운을 그대로 렌더링한다. 주제가 58개라 한 화면에 다 펼치면 길어지므로,
    `## N회 · 분류 · 주제` 단위로 잘라 접을 수 있게 한다.
    """
    import re
    import markdown as md

    cert = get_object_or_404(Certification, pk=cert_id)
    note = get_object_or_404(GisaEssayNote, certification=cert, slug=slug)

    text = note.content
    # 목차와 머리말(첫 `## 3회 …` 앞부분)은 통째로 두고, 주제부터 카드로 나눈다.
    # 분류명에도 가운뎃점이 들어가고(법규·제도) 주제명에도 들어가므로
    # (복원·복구·대체) 구분자만으로는 못 가른다. 분류명을 명시해 집는다.
    groups = '|'.join(re.escape(g) for _, g in GisaEssayQuestion.TOPIC_CHOICES)
    parts = re.split(r'^## (\d+)회 · (%s) · (.+)$' % groups, text, flags=re.M)
    intro_md = parts[0]
    items = []
    for i in range(1, len(parts), 4):
        freq, group, title, body = parts[i:i + 4]
        # 각 주제가 어느 회차에 나왔는지 — 본문 첫 **출제** 줄에서 뽑는다
        m = re.search(r'\*\*출제\*\*\s*(.+)', body)
        rounds = m.group(1).strip() if m else ''

        # 회차 배지를 누르면 그 주제의 기출 문항들을 펼쳐 보여준다.
        # 출제 줄의 첫 회차 + 빈출 수로 대표 문항을 찾는다 — 정확히 하나로
        # 좁혀질 때만 배지를 버튼으로 만든다 (calc 문서는 계산 유형으로 한정)
        rep_pk = None
        rm = re.search(r'(\d{4})-(\d)', rounds)
        if rm:
            cand = GisaEssayQuestion.objects.filter(
                certification=cert, source='기출',
                year=int(rm.group(1)), round=int(rm.group(2)),
                freq_rounds=int(freq))
            if note.slug == 'calc':
                cand = cand.filter(qtype='계산')
            pool = list(cand)
            if len(pool) > 1:
                # 같은 회차에 같은 빈출 수 주제가 여럿이면 제목 낱말이
                # 가장 많이 겹치는 것을 고른다
                key = set(re.findall(r'[가-힣A-Za-z]{2,}', title))
                pool.sort(key=lambda q: len(
                    key & set(re.findall(r'[가-힣A-Za-z]{2,}',
                                         (q.text or '') + ' ' +
                                         ' '.join(q.answer_items or [])))),
                    reverse=True)
            if pool:
                rep_pk = pool[0].pk

        # 「공식 / 대입 / 함정」처럼 라벨이 붙은 문단은 따로 떼어 낸다 —
        # 한 덩어리로 렌더링하면 줄바꿈만으로 구분돼 빽빽해 보인다.
        body_rest = re.sub(r'^\*\*출제\*\*.*$', '', body, flags=re.M)
        body_rest = re.sub(r'^\s*---\s*$', '', body_rest, flags=re.M)
        blocks = []
        for lab in ('공식', '대입', '함정', '유형', '주의'):
            bm = re.search(r'^\*\*%s\*\*\s*(.+)$' % lab, body_rest, flags=re.M)
            if not bm:
                continue
            raw = bm.group(1).strip()
            # 지수·아래첨자를 실제 수학식으로 (^{n} → <sup>n</sup>)
            raw = re.sub(r'\^\{([^}]{1,12})\}', r'<sup>\1</sup>', raw)
            raw = re.sub(r'\^\(([^)]{1,12})\)', r'<sup>\1</sup>', raw)
            raw = re.sub(r'\^(-?\d+(?:\.\d+)?|[A-Za-z]\d?)(?![\w.])',
                         r'<sup>\1</sup>', raw)
            raw = re.sub(r'_\{([^}]{1,12})\}', r'<sub>\1</sub>', raw)
            if lab in ('공식', '대입'):
                # X ÷ Y 는 세로 분수로. 한글 항(연면적 ÷ 대지면적)도 분수로
                # 만들되, 분자는 = 나 문장 구분자(/ ,) 뒤부터만 잡는다 —
                # 앞 문장까지 분자로 빨려 들어가면 공식이 뭉개진다.
                from gisa.templatetags.gisa_filters import frac_span
                # A ÷ B 를 세로 분수로. 항은 기호식 덩어리(2C, (A+B), ln1.5)와
                # ×·로 이어진 곱까지만 잡는다.
                #
                # 한글 공식(연면적 ÷ 대지면적 × 100)은 정규식으로 항의 경계를
                # 가르려 하면 띄어쓰기·볼드 때문에 매번 어긋난다. 그런 줄은
                # 데이터에서 [frac]분자|분모[/frac] 로 적어 두면 그대로 그린다.
                sym = (r"(?:\([^()]*\)|(?:ln|log)\s?[\d.,A-Za-z]*"
                       r"|[A-Za-z0-9.,₀-₉]+)")
                chain = r"%s(?:\s*[×·]\s*%s)*" % (sym, sym)
                raw = re.sub(
                    r"(?<![가-힣])(%s)\s*÷\s*(%s)" % (chain, chain),
                    lambda m2: frac_span(m2.group(1), m2.group(2)), raw)
                raw = re.sub(
                    r"\[frac\]([^|\[\]]+)\|([^|\[\]]+)\[/frac\]",
                    lambda m2: frac_span(m2.group(1).strip(),
                                         m2.group(2).strip()), raw)
            blocks.append({
                'label': lab,
                'html': md.markdown(raw, extensions=['tables']),
            })
            body_rest = body_rest.replace(bm.group(0), '')

        items.append({
            'freq': int(freq),
            'group': group.strip(),
            'title': title.strip(),
            'rounds': rounds,
            'rep_pk': rep_pk,
            'blocks': blocks,
            'warned': '⚠️ 요구가 커진 지점' in body,
            'html': md.markdown(body_rest, extensions=['tables', 'nl2br']),
        })

    # 머리말의 목차는 카드 목록이 대신하므로 걷어낸다
    intro_md = re.split(r'^## 목차', intro_md, flags=re.M)[0]

    return render(request, 'gisa/essay_note.html', {
        'cert': cert,
        'note': note,
        'intro': md.markdown(intro_md, extensions=['tables']),
        'items': items,
        'warned_count': sum(1 for x in items if x['warned']),
    })
