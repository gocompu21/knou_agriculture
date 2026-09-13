# -*- coding: utf-8 -*-
"""농약 DVD — 농약명으로 살충제·살균제·제초제를 가려내는 암기 카드.

잡초 동정 퀴즈와 같은 흐름이다(문제 → 고르기 → 정답·보충 정보 → 다음 문제).
다른 점은 **보기가 늘 셋으로 고정**이라는 것 — 사진을 보고 이름을 맞히는
잡초와 달리, 여기서는 묻는 것이 언제나 "이 농약은 무엇을 잡는가" 하나다.
그래서 서버가 보기를 만들어 보낼 까닭이 없다.

카드 92종은 자격증에 매이지 않는다. 식물보호기사와 산업기사가 같은 농약을
다루므로 두 실기 페이지가 같은 카드를 함께 쓴다(`_can_see`).
"""
import random

from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import PesticideCard, PesticideQuizAttempt

CATEGORIES = ['살충제', '살균제', '제초제']


def can_see(cert):
    """이 자격증 페이지에 농약 탭을 낼 것인가.

    식물보호 두 급수만이다. 조경·자연생태복원 실기에 농약 카드를 붙이면
    남의 시험 이야기가 된다.
    """
    return bool(cert) and cert.name.startswith('식물보호')


def _latest_wrong_ids(user):
    """카드별 **가장 최근** 풀이가 틀린 것들.

    기록을 쌓아 두고 마지막 것만 보므로, 다시 풀어 맞히면 오답에서 빠진다.
    """
    if not user.is_authenticated:
        return set()
    last = (PesticideQuizAttempt.objects
            .filter(user=user)
            .values('card')
            .annotate(at=Max('created_at')))
    if not last:
        return set()
    pairs = {(r['card'], r['at']) for r in last}
    rows = (PesticideQuizAttempt.objects
            .filter(user=user, card__in=[c for c, _ in pairs])
            .values_list('card', 'created_at', 'is_correct'))
    return {c for c, at, ok in rows if (c, at) in pairs and not ok}


def stats(user):
    """탭 머리에 얹을 숫자 — 전체·푼 것·오답."""
    total = PesticideCard.objects.count()
    if not user.is_authenticated:
        return {'total': total, 'solved': 0, 'wrong': 0}
    solved = (PesticideQuizAttempt.objects.filter(user=user)
              .values('card').distinct().count())
    return {'total': total, 'solved': solved, 'wrong': len(_latest_wrong_ids(user))}


@login_required
def api_next(request):
    """다음 문제 한 건. `?mode=all|freq|wrong&seen=1,2,3`

    - all  : 전체에서 고르게
    - freq : 출제수로 가중 — 8회 나온 농약이 1회짜리보다 여덟 배 자주 나온다
    - wrong: 최신 풀이가 틀린 것만
    - seen 에 든 카드는 다시 내지 않는다. 한 바퀴 돌면 done
    """
    mode = request.GET.get('mode', 'all')
    seen = {int(x) for x in request.GET.get('seen', '').split(',') if x.isdigit()}
    cards = list(PesticideCard.objects.all())
    if not cards:
        return JsonResponse({'done': True, 'total': 0})

    pool = cards
    if mode == 'wrong':
        wrong = _latest_wrong_ids(request.user)
        pool = [c for c in cards if c.pk in wrong]
    elif mode == 'freq':
        # 한 번도 안 나온 농약은 없지만, 0이 섞여도 뽑히도록 최소 1을 준다
        pool = [c for c in cards if c.exam_count > 0] or cards

    remaining = [c for c in pool if c.pk not in seen]
    if not remaining:
        return JsonResponse({'done': True, 'total': len(pool)})

    if mode == 'freq':
        card = random.choices(remaining,
                              weights=[max(1, c.exam_count) for c in remaining])[0]
    else:
        card = random.choice(remaining)

    return JsonResponse({
        'done': False,
        'card': card.pk,
        'no': card.no,
        'name': card.name,
        'exam_count': card.exam_count,
        'choices': CATEGORIES,      # 늘 셋. 차례도 고정이라 눈이 자리를 기억한다
        'left': len(remaining) - 1,
        'total': len(pool),
    })


@login_required
@require_POST
def api_answer(request):
    """답을 채점하고 보충 정보를 돌려준다 (`card`, `selected`)."""
    try:
        card = PesticideCard.objects.get(pk=int(request.POST.get('card', 0)))
    except (PesticideCard.DoesNotExist, ValueError):
        return JsonResponse({'ok': False, 'error': '카드를 찾을 수 없습니다.'}, status=404)

    selected = (request.POST.get('selected') or '').strip()
    correct = selected == card.category
    PesticideQuizAttempt.objects.create(
        user=request.user, card=card, selected=selected, is_correct=correct)

    return JsonResponse({
        'ok': True,
        'correct': correct,
        'answer': card.category,
        'name': card.name,
        # 단서가 이름 전체면 '통암기' — 어미·어두로 가를 수 없는 것들이다
        'hint': card.hint,
        'whole': card.whole,
        'exam_count': card.exam_count,
        'note': card.note,
        'stats': stats(request.user),
    })


@login_required
@require_POST
def api_reset(request):
    """내 풀이 기록을 지운다."""
    n = PesticideQuizAttempt.objects.filter(user=request.user).delete()[0]
    return JsonResponse({'ok': True, 'deleted': n, 'stats': stats(request.user)})


@login_required
def api_list(request):
    """카드 92종 목록 — 구분별로 묶어 한눈에 훑는다."""
    rows = []
    for c in PesticideCard.objects.all():
        rows.append({'no': c.no, 'name': c.name, 'category': c.category,
                     'hint': c.hint, 'whole': c.whole,
                     'exam_count': c.exam_count, 'note': c.note})
    return JsonResponse({'ok': True, 'cards': rows, 'stats': stats(request.user)})
