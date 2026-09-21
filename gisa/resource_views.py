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

    added, msgs, new_ids = 0, [], []
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
        obj = GisaResource.objects.create(
            certification=cert, subject=subject, part=part,
            kind=meta.get('kind') or ('youtube' if meta.get('video_id') else 'site'),
            url=url, title=meta.get('title', ''), author=meta.get('author', ''),
            video_id=meta.get('video_id', ''), start_sec=meta.get('start_sec', 0),
            note=note, order=order, is_dead=bool(meta.get('dead')),
            embeddable=meta.get('embeddable', True), category=category,
        )
        added += 1
        # 화면이 그 카드를 찾아가 반전시킬 수 있게 id 를 함께 돌려준다 — 새 영상은
        # 목록 아래쪽('분류 없음' 이면 맨 밑)에 생겨 어디 붙었는지 안 보인다
        new_ids.append(obj.pk)
        tail = f" ({meta['info']})" if meta.get('info') else ''
        msgs.append(f"등록 — {meta.get('title') or url[:60]}{tail}")
    return JsonResponse({'added': added, 'ids': new_ids,
                         'message': '\n'.join(msgs)})


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
    """동영상 탭 — 분류 트리와 그 아래 영상.

    **깊이를 정해 두지 않는다.** 처음에는 대분류 > 중분류 두 층으로 못 박았는데,
    관리 화면을 목차꼴(1 · 1.1 · 1.2.1)로 바꾸면서 '자식 추가'가 어느 줄에나 있어야
    자연스러워졌다. 모델의 `parent` 는 본래 self-FK 라 깊이 제한이 없었고, 화면만
    재귀로 그리면 된다(`_video_node.html` 이 자기를 include 한다).

    분류가 없는 영상은 '분류 없음' 묶음에 모아, 등록만 해 두고 나중에 정리할 수
    있게 한다 — 분류를 먼저 만들게 강요하면 URL 을 붙여넣다 말게 된다.
    """
    cats = list(GisaVideoCategory.objects.filter(certification=cert, part=part))
    kids = {}
    for c in cats:
        kids.setdefault(c.parent_id, []).append(c)

    vids = list(GisaResource.objects
                .filter(certification=cert, part=part, kind='youtube',
                        is_active=True, is_dead=False)
                .select_related('category'))
    # 요약은 마크다운 비슷한 평문이라 서버에서 한 번만 HTML 로 만든다 — 카드마다
    # 템플릿 필터를 부르면 목록 하나에 수십 번 돈다
    from .video_summary import render as _render_summary
    for v in vids:
        v.summary_html = _render_summary(v.summary) if v.summary else ''

    by_cat = {}
    loose = []
    for v in vids:
        if v.category_id:
            by_cat.setdefault(v.category_id, []).append(v)
        else:
            loose.append(v)

    def build(parent_id, depth, prefix):
        """`1`·`1.2`·`1.2.1` 목차 번호를 붙여 가며 내려간다."""
        out = []
        for i, c in enumerate(kids.get(parent_id, []), 1):
            code = f'{prefix}{i}'
            children = build(c.id, depth + 1, code + '.')
            videos = by_cat.get(c.id, [])
            out.append({
                'cat': c, 'code': code, 'depth': depth,
                'children': children, 'videos': videos,
                # 아래 가지의 영상까지 센다 — 접힌 채로도 몇 편인지 보이게
                'count': len(videos) + sum(n['count'] for n in children),
            })
        return out

    tree = build(None, 0, '')

    # 관리 화면(목차꼴 표)과 '옮길 자리' 셀렉트는 같은 트리를 평평하게 편 것이다
    outline, choices = [], []
    def walk(nodes, path):
        for n in nodes:
            c = n['cat']
            choices.append((c.id, ' › '.join(path + [c.name])))
            # 셈은 템플릿에서 짜깁기하지 않고 여기서 한 문장으로 만든다 —
            # `{% if %}` 로 이어 붙였더니 영상이 없는 줄에 가운뎃점이 앞에 남았다
            own, below = len(n['videos']), n['count'] - len(n['videos'])
            bits = ([f'영상 {own}'] if own else []) + ([f'아래 {below}'] if below else [])
            outline.append({
                'id': c.id, 'name': c.name, 'code': n['code'], 'depth': n['depth'],
                'parent': c.parent_id or '', 'own': own,
                'label': ' · '.join(bits), 'has_children': bool(n['children']),
            })
            walk(n['children'], path + [c.name])
    walk(tree, [])

    return {
        'vid_tree': tree,
        'vid_loose': loose,
        'vid_total': len(vids),
        'vid_part': part,
        'vid_choices': choices,
        'vid_outline': outline,
        'vid_drawings': drawing_choices(cert) if part == 'work' else [],
    }


def drawing_choices(cert):
    """작업형 도면 목록 — 영상을 어느 기출 도면에 매달지 고르는 데 쓴다.

    같은 도면이 여러 회차에 나오므로 **번호(없으면 이름)로 하나만** 낸다.
    GisaDrawingRef·GisaDrawingTask 가 쓰는 열쇠와 같아야 기출분석에서 이어진다.
    """
    from .models import GisaDrawingTask

    seen, out = set(), []
    for t in (GisaDrawingTask.objects.filter(certification=cert)
              .order_by('-year', 'round')):
        key = t.code or t.title
        if key in seen:
            continue
        seen.add(key)
        out.append((key, f'{t.title} {t.code}'.strip()))
    return sorted(out, key=lambda x: x[1])


def _reorder(items, obj, direction):
    """이웃과 자리를 맞바꾼다. 되었으면 True.

    **먼저 1..N 으로 번호를 새로 매긴다.** 등록만 하고 순서를 건드린 적이 없으면
    order 가 모두 0 이거나 겹쳐 있어, 값을 맞바꿔도 차례가 그대로다. 한 번 정규화해
    두면 그다음부터는 맞바꾸기만으로 움직인다.
    """
    items = list(items)
    for i, it in enumerate(items, 1):
        if it.order != i:
            it.order = i
            it.save(update_fields=['order'])
    idx = next((i for i, it in enumerate(items) if it.pk == obj.pk), None)
    if idx is None:
        return False
    j = idx - 1 if direction == 'up' else idx + 1
    if j < 0 or j >= len(items):
        return False                      # 맨 위에서 위로, 맨 아래에서 아래로
    a, b = items[idx], items[j]
    a.order, b.order = b.order, a.order
    a.save(update_fields=['order'])
    b.save(update_fields=['order'])
    return True


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
    cat = GisaVideoCategory.objects.create(certification=cert, part=part, parent=parent,
                                           name=name, order=order)
    # 새 분류의 id 를 돌려준다 — 화면이 갱신한 뒤 그 줄을 잠깐 반전시켜 알린다
    return JsonResponse({'ok': True, 'id': cat.pk})


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
    if body.get('move'):
        # 같은 자리끼리만 움직인다 — 대분류는 대분류끼리, 중분류는 제 부모 안에서
        sibs = GisaVideoCategory.objects.filter(
            certification=cat.certification, part=cat.part, parent=cat.parent)
        return JsonResponse({'ok': _reorder(sibs, cat, body['move'])})
    name = (body.get('name') or '').strip()[:60]
    if name:
        if GisaVideoCategory.objects.filter(
                certification=cat.certification, part=cat.part,
                parent=cat.parent, name=name).exclude(pk=cat.pk).exists():
            return JsonResponse({'ok': False, 'message': '같은 이름이 이미 있습니다.'})
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
    fields = []
    # 분류와 도면 번호는 따로 보낸다 — 한 카드에서 셀렉트 두 개가 각각 움직인다
    if 'category' in body:
        res.category = GisaVideoCategory.objects.filter(
            pk=body['category'], certification=res.certification).first()             if body['category'] else None
        fields.append('category')
    if 'drawing' in body:
        res.drawing_code = (body['drawing'] or '')[:20]
        fields.append('drawing_code')
    if body.get('order'):
        # 같은 묶음(같은 분류) 안에서만 움직인다
        sibs = GisaResource.objects.filter(
            certification=res.certification, part=res.part, kind='youtube',
            is_active=True, is_dead=False, category=res.category)
        return JsonResponse({'ok': _reorder(sibs, res, body['order'])})
    if fields:
        res.save(update_fields=fields)
    return JsonResponse({'ok': True})


@login_required
@require_POST
def video_summarize(request, res_id):
    """영상 하나를 AI 로 요약한다(스태프 전용).

    한 편에 20~30초 걸리고 30원쯤 든다. 회원이 누를 수 있게 두면 같은 영상을
    여러 번 요약하게 되므로 관리자만 부르고, 결과는 DB 에 남겨 모두가 읽는다.
    """
    if not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': '권한이 없다'}, status=403)
    res = get_object_or_404(GisaResource, pk=res_id, kind='youtube')
    from .video_summary import summarize
    out = summarize(res)
    return JsonResponse(out, status=200 if out.get('ok') else 400)
