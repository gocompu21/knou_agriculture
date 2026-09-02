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
import uuid
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
from .models import (Certification, GisaEssayAttempt, GisaEssayQuestion,
                     GisaEssaySession, GisaEssayUpload)

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
    rounds = (qs.filter(source='기출')
              .values('year', 'round')
              .annotate(c=Count('id'), p=Sum('points'))
              .order_by('-year', '-round'))

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

    # 빈출 주제 현황 — 되풀이 출제된 주제가 몇 개인지 보여 준다
    freq_cards = []
    for lo, label in ((4, '4회 이상'), (3, '3회 이상'), (2, '2회 이상')):
        n = (GisaEssayQuestion.objects
             .filter(certification=cert, source='기출', freq_rounds__gte=lo)
             .values('topic_key').distinct().count())
        if n:
            freq_cards.append({'min': lo, 'label': label, 'count': n})

    return render(request, 'gisa/essay_list.html', {
        'cert': cert,
        'round_cards': round_cards,
        'sections': sections,
        'freq_cards': freq_cards,
        'sessions': sessions,
        'total': qs.count(),
    })


# ------------------------------------------------------------------ 풀이

def _pick_questions(cert, source, section=None, year=None, round_=None, user=None):
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

    questions = _pick_questions(cert, source, section, year, round_, request.user)
    if not questions:
        return redirect(f'/gisa/{cert_id}/essay/')

    total_points = round(sum(float(q.points) for q in questions), 1)

    # 인쇄한 시험지로 이어 오는 경우(?resume=<세션pk>)는 새로 만들지 않는다.
    # 새 세션을 만들면 종이에 찍힌 시험지 코드와 어긋난다.
    session = None
    resume = request.GET.get('resume')
    if resume:
        session = GisaEssaySession.objects.filter(
            pk=resume, user=request.user, certification=cert,
            status='progress').first()

    if session is None:
        session = GisaEssaySession.objects.create(
            user=request.user, certification=cert,
            source=source, section=(section if source == '예상' else '기출'),
            year=year, round=round_, mode=mode,
            total_points=total_points,
            paper_code=uuid.uuid4().hex[:10].upper() if mode == 'paper' else '',
        )

    # 실전(기출)은 90분 타이머, 학습(예상)은 무제한
    time_limit = 90 * 60 if source == '기출' else 0

    return render(request, 'gisa/essay_take.html', {
        'cert': cert,
        'session': session,
        'questions': questions,
        'total_points': total_points,
        'time_limit': time_limit,
        'is_exam': source == '기출',
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

    # 출제기준 주요항목 분포
    from .management.commands.classify_essay_std import MAJOR_NAMES
    majors = []
    for r in (exam_qs.values('std_major').annotate(c=Count('id')).order_by('-c')):
        majors.append({
            'name': MAJOR_NAMES.get(r['std_major'], '미분류'),
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
        'pred_count': qs.filter(source='예상').count(),
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

    # 출제기준 주요항목별 득점률 — 약한 항목 파악용
    by_major = {}
    for a in attempts:
        m = a.question.std_major
        d = by_major.setdefault(m, {'got': 0.0, 'max': 0.0, 'count': 0})
        d['got'] += a.score
        d['max'] += float(a.question.points)
        d['count'] += 1
    majors = []
    from .management.commands.classify_essay_std import MAJOR_NAMES
    for m, d in sorted(by_major.items()):
        majors.append({
            'no': m, 'name': MAJOR_NAMES.get(m, '미분류'),
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
        results = transcribe_uploads(session, uploads)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'판독 실패: {e}'}, status=500)

    return JsonResponse({'ok': True, 'answers': results})


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
        'reference': q.reference,
    })
