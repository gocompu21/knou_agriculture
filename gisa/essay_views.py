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

    rounds = (qs.filter(source='기출')
              .values('year', 'round')
              .annotate(c=Count('id'))
              .order_by('-year', '-round'))

    sections = (qs.filter(source='예상')
                .values('section')
                .annotate(c=Count('id'))
                .order_by('section'))

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

    round_cards = []
    for r in rounds:
        key = (r['year'], r['round'])
        round_cards.append({
            'year': r['year'], 'round': r['round'], 'count': r['c'],
            'best': best.get(key),
        })

    return render(request, 'gisa/essay_list.html', {
        'cert': cert,
        'round_cards': round_cards,
        'sections': sections,
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
