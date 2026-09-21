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

from .models import (Certification, GisaResource, GisaSubject,
                     GisaVideoCategory)
from .resources import fetch, youtube_id


def resource_tab_context(cert, part):
    """자료실 탭이 쓰는 값. part 는 'written' 또는 'practical'.

    `both`(공통) 자료는 어느 쪽에서도 보이게 한다 — 시험 전략이나 수험 요령처럼
    필기·실기를 가리지 않는 것이 있다.
    """
    # **영상은 빼고 본다.** 유튜브는 '동영상' 탭이 분류별로 맡고, 자료실은
    # 블로그·사이트 글을 모으는 자리로 갈랐다(사용자 결정).
    items = list(GisaResource.objects
                 .filter(cert_q(cert), Q(part=part) | Q(part='both'),
                         is_active=True, is_dead=False)
                 .exclude(kind='youtube')
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
    category = None
    if body.get('category'):
        category = GisaVideoCategory.objects.filter(
            pk=body['category'], certification=cert).first()

    urls = [u.strip() for u in (body.get('urls') or '').splitlines() if u.strip()]
    if not urls:
        return JsonResponse({'message': '주소를 넣어 주세요.'})

    added, msgs = 0, []
    order = (GisaResource.objects.filter(certification=cert)
             .order_by('-order').values_list('order', flat=True).first() or 0)
    for url in urls:
        # **중복은 영상 id 로 본다.** 유튜브 공유 버튼이 `?si=...` 추적 파라미터를
        # 붙여 주므로 같은 영상인데도 주소가 달라진다 — 주소만 견주면 같은 영상이
        # 두 번 등록된다(실제로 그렇게 됐다).
        vid = youtube_id(url)
        dup = (GisaResource.objects.filter(certification=cert, video_id=vid)
               if vid else GisaResource.objects.filter(certification=cert, url=url))
        if dup.exists():
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
            embeddable=meta.get('embeddable', True), category=category,
        )
        added += 1
        tail = f" ({meta['info']})" if meta.get('info') else ''
        msgs.append(f"등록 — {meta.get('title') or url[:60]}{tail}")
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


# ------------------------------------------------------------ 동영상 (분류별)

def video_tab_context(cert, part):
    """동영상 탭 — 대분류 > 중분류 > 영상 으로 묶어 내려보낸다.

    영상은 `GisaResource` 가운데 유튜브인 것이다(자료실 탭은 그 나머지를 맡는다).
    분류가 없는 영상은 '분류 없음' 묶음에 모아, 등록만 해 두고 나중에 정리할 수
    있게 한다 — 분류를 먼저 만들게 강요하면 URL 을 붙여넣다 말게 된다.
    """
    cats = list(GisaVideoCategory.objects.filter(certification=cert, part=part))
    majors = [c for c in cats if c.parent_id is None]
    subs = {}
    for c in cats:
        if c.parent_id:
            subs.setdefault(c.parent_id, []).append(c)

    vids = list(GisaResource.objects
                .filter(certification=cert, part=part, kind='youtube',
                        is_active=True, is_dead=False)
                .select_related('category'))
    by_cat = {}
    loose = []
    for v in vids:
        if v.category_id:
            by_cat.setdefault(v.category_id, []).append(v)
        else:
            loose.append(v)
    tree = []
    for m in majors:
        groups = [{'cat': s, 'videos': by_cat.get(s.id, [])} for s in subs.get(m.id, [])]
        # **대분류에 바로 붙인 영상도 보여 준다.** 중분류를 꼭 만들게 하면 영상 두어
        # 개뿐인 분류에서도 한 칸을 더 파야 한다. 그런 것은 'direct' 로 따로 낸다.
        direct = by_cat.get(m.id, [])
        tree.append({'cat': m, 'groups': groups, 'direct': direct,
                     'count': len(direct) + sum(len(g['videos']) for g in groups)})
    # 옮길 자리 목록 — 대분류도 고를 수 있게 함께 낸다
    choices = []
    for m in majors:
        choices.append((m.id, m.name))
        for sub in subs.get(m.id, []):
            choices.append((sub.id, f'{m.name} > {sub.name}'))
    return {
        'vid_tree': tree,
        'vid_loose': loose,
        'vid_total': len(vids),
        'vid_part': part,
        'vid_choices': choices,
    }


@require_POST
@login_required
def video_category_add(request, cert_id):
    """분류 추가. parent 를 주면 중분류, 안 주면 대분류."""
    if not request.user.is_staff:
        return JsonResponse({'message': '권한이 없습니다.'}, status=403)
    cert = get_object_or_404(Certification, pk=cert_id)
    body = json.loads(request.body or '{}')
    name = (body.get('name') or '').strip()[:60]
    if not name:
        return JsonResponse({'message': '이름을 넣어 주세요.'})
    part = body.get('part') or 'work'
    parent = None
    if body.get('parent'):
        parent = GisaVideoCategory.objects.filter(
            pk=body['parent'], certification=cert).first()
    if GisaVideoCategory.objects.filter(certification=cert, part=part,
                                        parent=parent, name=name).exists():
        return JsonResponse({'message': '같은 이름이 이미 있습니다.'})
    order = (GisaVideoCategory.objects.filter(certification=cert, part=part, parent=parent)
             .order_by('-order').values_list('order', flat=True).first() or 0) + 1
    GisaVideoCategory.objects.create(certification=cert, part=part, parent=parent,
                                     name=name, order=order)
    return JsonResponse({'ok': True})


@require_POST
@login_required
def video_category_edit(request, cat_id):
    """이름 바꾸기·지우기. 지울 때 **영상은 지우지 않는다** — 분류만 떨어져 나가
    '분류 없음' 으로 모인다. 분류를 지웠다고 자료가 사라지면 곤란하다."""
    if not request.user.is_staff:
        return JsonResponse({'ok': False}, status=403)
    cat = get_object_or_404(GisaVideoCategory, pk=cat_id)
    body = json.loads(request.body or '{}')
    if body.get('delete'):
        # 하위 중분류의 영상까지 분류를 떼어 낸다(FK 는 SET_NULL 이라 영상은 남는다)
        cat.delete()
        return JsonResponse({'ok': True})
    name = (body.get('name') or '').strip()[:60]
    if name:
        cat.name = name
        cat.save(update_fields=['name'])
    return JsonResponse({'ok': True})


@require_POST
@login_required
def video_move(request, res_id):
    """영상을 다른 분류로 옮긴다(빈 값이면 분류 없음)."""
    if not request.user.is_staff:
        return JsonResponse({'ok': False}, status=403)
    res = get_object_or_404(GisaResource, pk=res_id)
    body = json.loads(request.body or '{}')
    cat = None
    if body.get('category'):
        cat = GisaVideoCategory.objects.filter(
            pk=body['category'], certification=res.certification).first()
    res.category = cat
    res.save(update_fields=['category'])
    return JsonResponse({'ok': True})
