# -*- coding: utf-8 -*-
"""해충 DVD — 사진을 보고 해충 이름을 맞히는 암기 카드.

잡초 동정과 같은 흐름이다(사진 → 이름 고르기 → 정답·설명 → 다음 문제).
농약 DVD 와 다른 점은 **보기가 넷이고 서버가 만들어 보낸다**는 것 —
농약은 묻는 것이 늘 "살충제냐 살균제냐 제초제냐" 하나뿐이지만, 해충은
152종 가운데 하나를 고르는 것이라 그때그때 보기를 뽑아야 한다.

**보기는 같은 구분(농작물·수목)에서 먼저 고른다.** 농작물 해충 사진에
수목 해충만 섞어 놓으면 사진을 보지 않고도 답이 갈린다.
"""
import random

from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import PestCard, PestQuizAttempt


def can_see(cert):
    """이 자격증 페이지에 해충 탭을 낼 것인가 — 식물보호 두 급수만."""
    return bool(cert) and cert.name.startswith('식물보호')


def _latest_wrong_ids(user):
    """카드별 **가장 최근** 풀이가 틀린 것들."""
    if not user.is_authenticated:
        return set()
    last = (PestQuizAttempt.objects.filter(user=user)
            .values('card').annotate(at=Max('created_at')))
    if not last:
        return set()
    pairs = {(r['card'], r['at']) for r in last}
    rows = (PestQuizAttempt.objects
            .filter(user=user, card__in=[c for c, _ in pairs])
            .values_list('card', 'created_at', 'is_correct'))
    return {c for c, at, ok in rows if (c, at) in pairs and not ok}


def stats(user):
    total = PestCard.objects.count()
    if not user.is_authenticated:
        return {'total': total, 'solved': 0, 'wrong': 0}
    solved = (PestQuizAttempt.objects.filter(user=user)
              .values('card').distinct().count())
    return {'total': total, 'solved': solved, 'wrong': len(_latest_wrong_ids(user))}


@login_required
def api_next(request):
    """다음 문제 한 건. `?mode=all|crop|tree|wrong&seen=1,2,3`

    - all  : 152종 전체
    - crop : 농작물 해충만 / tree : 수목 해충만
    - wrong: 최신 풀이가 틀린 것만
    """
    mode = request.GET.get('mode', 'all')
    seen = {int(x) for x in request.GET.get('seen', '').split(',') if x.isdigit()}
    cards = list(PestCard.objects.all())
    if not cards:
        return JsonResponse({'done': True, 'total': 0})

    pool = cards
    if mode == 'wrong':
        wrong = _latest_wrong_ids(request.user)
        pool = [c for c in cards if c.pk in wrong]
    elif mode == 'crop':
        pool = [c for c in cards if c.group == '농작물']
    elif mode == 'tree':
        pool = [c for c in cards if c.group == '수목']

    remaining = [c for c in pool if c.pk not in seen]
    if not remaining:
        return JsonResponse({'done': True, 'total': len(pool)})
    card = random.choice(remaining)

    # 보기 넷 — 같은 구분에서 먼저 고른다
    others = [c for c in cards if c.pk != card.pk]
    same = [c for c in others if c.group and c.group == card.group]
    random.shuffle(same)
    random.shuffle(others)
    picks, used = [], {card.name}
    for c in same + others:
        if len(picks) >= 3:
            break
        if c.name in used:
            continue
        picks.append(c.name)
        used.add(c.name)
    choices = picks + [card.name]
    random.shuffle(choices)

    return JsonResponse({
        'done': False,
        'card': card.pk,
        'no': card.no,
        'image': card.image.url,
        'choices': choices,
        'left': len(remaining) - 1,
        'total': len(pool),
    })


@login_required
@require_POST
def api_answer(request):
    """답을 채점하고 이름·설명을 돌려준다 (`card`, `selected`)."""
    try:
        card = PestCard.objects.get(pk=int(request.POST.get('card', 0)))
    except (PestCard.DoesNotExist, ValueError):
        return JsonResponse({'ok': False, 'error': '카드를 찾을 수 없습니다.'}, status=404)

    selected = (request.POST.get('selected') or '').strip()
    correct = selected == card.name
    PestQuizAttempt.objects.create(
        user=request.user, card=card, selected=selected, is_correct=correct)

    return JsonResponse({
        'ok': True,
        'correct': correct,
        'answer': card.name,
        'group': card.group,
        'desc': card.desc,
        'note': card.note,
        'stats': stats(request.user),
    })


@login_required
@require_POST
def api_reset(request):
    n = PestQuizAttempt.objects.filter(user=request.user).delete()[0]
    return JsonResponse({'ok': True, 'deleted': n, 'stats': stats(request.user)})


@login_required
def api_list(request):
    """카드 152종 목록."""
    rows = [{'no': c.no, 'name': c.name, 'group': c.group,
             'image': c.image.url, 'desc': c.desc}
            for c in PestCard.objects.all()]
    return JsonResponse({'ok': True, 'cards': rows, 'stats': stats(request.user)})
