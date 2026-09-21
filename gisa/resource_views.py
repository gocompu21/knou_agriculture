# -*- coding: utf-8 -*-
"""자료실 — 유튜브·블로그 목록의 뷰.

화면 조각은 `templates/gisa/_resources.html` 하나이고 필기 상세와 실기 목록이
함께 쓴다. 컨텍스트도 `resource_tab_context()` 하나가 만든다.
"""
import json

from django.contrib.auth.decorators import login_required
from django.db.models import F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from .models import Certification, GisaResource, GisaSubject
from .resources import fetch


def resource_tab_context(cert, part):
    """자료실 탭이 쓰는 값. part 는 'written' 또는 'practical'.

    `both`(공통) 자료는 어느 쪽에서도 보이게 한다 — 시험 전략이나 수험 요령처럼
    필기·실기를 가리지 않는 것이 있다.
    """
    items = list(GisaResource.objects
                 .filter(cert_q(cert), Q(part=part) | Q(part='both'),
                         is_active=True, is_dead=False)
                 .select_related('subject'))
    counts = {}
    for r in items:
        counts[r.kind] = counts.get(r.kind, 0) + 1
    kinds = [(k, label, counts[k])
             for k, label in GisaResource.KIND_CHOICES if counts.get(k)]
    return {
        'res_items': items,
        'res_kinds': kinds,
        'res_part': part,
        'res_subjects': GisaSubject.objects.filter(certification=cert),
        'res_count': len(items),
    }


def cert_q(cert):
    return Q(certification=cert)


@require_POST
@login_required
def resource_add(request, cert_id):
    """주소를 받아 제목·채널을 가져와 등록한다. 여러 줄이면 한꺼번에.

    **주소만 받는다.** 제목을 손으로 적게 하면 수십 개를 넣을 때 그것만으로 지친다.
    유튜브는 oEmbed, 그 밖은 <title> 로 채우고(`gisa/resources.py`), 실패한 줄은
    무엇이 잘못됐는지 그대로 알려 준다.
    """
    if not request.user.is_staff:
        return JsonResponse({'message': '권한이 없습니다.'}, status=403)
    cert = get_object_or_404(Certification, pk=cert_id)
    try:
        body = json.loads(request.body or '{}')
    except ValueError:
        return JsonResponse({'message': '잘못된 요청입니다.'}, status=400)

    part = body.get('part') or 'written'
    if part not in dict(GisaResource.PART_CHOICES):
        part = 'written'
    subject = None
    if body.get('subject'):
        subject = GisaSubject.objects.filter(
            pk=body['subject'], certification=cert).first()
    note = (body.get('note') or '').strip()[:200]

    urls = [u.strip() for u in (body.get('urls') or '').splitlines() if u.strip()]
    if not urls:
        return JsonResponse({'message': '주소를 넣어 주세요.'})

    added, msgs = 0, []
    order = (GisaResource.objects.filter(certification=cert)
             .order_by('-order').values_list('order', flat=True).first() or 0)
    for url in urls:
        if GisaResource.objects.filter(certification=cert, url=url).exists():
            msgs.append(f'이미 있음 — {url[:60]}')
            continue
        meta = fetch(url)
        if meta.get('error') and not meta.get('video_id'):
            msgs.append(f"{meta['error']} — {url[:60]}")
            continue
        order += 1
        GisaResource.objects.create(
            certification=cert, subject=subject, part=part,
            kind=meta.get('kind') or ('youtube' if meta.get('video_id') else 'site'),
            url=url, title=meta.get('title', ''), author=meta.get('author', ''),
            video_id=meta.get('video_id', ''), start_sec=meta.get('start_sec', 0),
            note=note, order=order, is_dead=bool(meta.get('dead')),
        )
        added += 1
        msgs.append(f"등록 — {meta.get('title') or url[:60]}")
    return JsonResponse({'added': added, 'message': '\n'.join(msgs)})


@require_POST
@login_required
def resource_delete(request, res_id):
    if not request.user.is_staff:
        return JsonResponse({'ok': False}, status=403)
    GisaResource.objects.filter(pk=res_id).delete()
    return JsonResponse({'ok': True})


@require_POST
@login_required
def resource_open(request, res_id):
    """열람 수 — 어떤 자료가 실제로 쓰이는지 보려는 것이다.

    F() 로 올려 두 사람이 같이 눌러도 수가 어긋나지 않게 한다.
    """
    GisaResource.objects.filter(pk=res_id).update(open_count=F('open_count') + 1)
    return JsonResponse({'ok': True})
