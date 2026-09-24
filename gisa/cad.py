# -*- coding: utf-8 -*-
"""작업형 CAD 탭 — 모눈종이 위에 점을 찍고 선·원·호·기호를 이어 도면을 만든다.

모눈종이 도면 PDF(`04 그리드 도면/*.pdf`)는 모두 **빈 눈금 종이**다. 도면마다 다른
것은 좌표 범위와 축척뿐이라 PDF 를 싣지 않고, 아래 SHEETS 의 범위로 화면이 눈금을
직접 그린다(눈금 라벨 간격 = step, 가는 눈금 = step/5).

도면은 회원마다 따로(`CadDrawing`), 라이브러리 기호는 본인 것 + 스태프가 공유한 것
(`CadSymbol`)을 쓴다. 기본 기호(퍼걸러·평의자…)는 화면 코드(`_cad.html`)에 있다.
"""
import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import CadDrawing, CadSymbol, Certification

# 모눈종이 — PDF 의 눈금 라벨을 읽어 옮겼다(파일 이름의 '74x40' 은 부지 크기이고,
# 종이 범위는 그보다 5~10m 넉넉하다). 06 주택정원은 PDF 제목이 '(436)' 이지만
# 파일 이름과 출제 표가 434 라 434 로 둔다.
SHEETS = [
    ('360', '근린공원 360', -5, 80, -5, 45, 5, '1:400'),
    ('428', '생태하천 428', -5, 60, -5, 45, 5, '1:300'),
    ('454', '항일공원 454', -10, 110, -10, 110, 5, '1:800'),
    ('344', '도시미관광장 344', -5, 65, -5, 45, 5, '1:300'),
    ('444', '주차공원 444', -10, 160, -10, 120, 5, '1:800'),
    ('434', '주택정원 434', -5, 30, -5, 30, 5, '1:250'),
    ('318', '주차공원 318 (기본도)', -5, 85, -5, 65, 5, '1:430'),
    ('318-s1', '주차공원 318 (단면도 1/2)', -5, 85, -5, 65, 5, '1:430'),
    ('318-s2', '주차공원 318 (단면도 2/2)', 0, 2, 0, 2, 0.5, '1:20'),
    ('287', '아파트입구 287', -5, 65, -5, 65, 5, '1:430'),
    ('401', '생태공원 401', -5, 95, -5, 65, 5, '1:430'),
    ('478', '야영장 478', -5, 140, -5, 95, 5, '1:600'),
    ('264', '건물중앙광장 264', -5, 85, -5, 65, 5, '1:430'),
    ('412', '근린공원 412', -5, 135, -5, 115, 5, '1:800'),
    ('323', '근린공원 323', -5, 115, -5, 85, 5, '1:600'),
    ('391', '가로소공원 391', -5, 75, -5, 55, 5, '1:400'),
    ('463', '친수공간 463', -5, 85, -5, 85, 5, '1:600'),
    ('365', '어린이주차공원 365', -5, 55, -5, 65, 5, '1:430'),
    ('371', '사적지주변 371', -5, 105, -5, 85, 5, '1:600'),
]
SHEET_KEYS = {s[0] for s in SHEETS} | {'blank'}

MAX_DATA = 600_000          # 도면 JSON 한도(자) — 점 수천 개도 여유 있게 들어간다


def sheets_json():
    return [{'key': k, 'title': t, 'x0': x0, 'x1': x1, 'y0': y0, 'y1': y1,
             'step': st, 'scale': sc} for k, t, x0, x1, y0, y1, st, sc in SHEETS]


def _when(d):
    return timezone.localtime(d.updated_at).strftime('%Y-%m-%d %H:%M')


def _body(request):
    try:
        return json.loads(request.body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return None


def _err(msg, status=400):
    return JsonResponse({'ok': False, 'error': msg}, status=status)


@login_required
def drawing_list(request, cert_id):
    rows = CadDrawing.objects.filter(certification_id=cert_id, owner=request.user)
    return JsonResponse({'ok': True, 'items': [
        {'id': d.pk, 'title': d.title, 'sheet': d.sheet,
         'updated': _when(d)} for d in rows]})


@login_required
def drawing_get(request, cert_id, pk):
    d = get_object_or_404(CadDrawing, pk=pk, certification_id=cert_id, owner=request.user)
    return JsonResponse({'ok': True, 'id': d.pk, 'title': d.title, 'sheet': d.sheet,
                         'data': d.data})


@login_required
@require_POST
def drawing_save(request, cert_id):
    """id 가 있으면 그 도면을 고치고, 없으면 새로 만든다."""
    cert = get_object_or_404(Certification, pk=cert_id)
    body = _body(request)
    if not isinstance(body, dict):
        return _err('본문을 읽지 못했습니다.')
    title = str(body.get('title') or '').strip()[:100] or '제목 없음'
    sheet = str(body.get('sheet') or '')
    data = body.get('data')
    if sheet not in SHEET_KEYS:
        return _err('모르는 모눈종이입니다.')
    if not isinstance(data, dict):
        return _err('도면 자료가 없습니다.')
    if len(json.dumps(data, ensure_ascii=False)) > MAX_DATA:
        return _err('도면이 너무 큽니다.')
    if body.get('id'):
        d = get_object_or_404(CadDrawing, pk=body['id'], certification=cert, owner=request.user)
        d.title, d.sheet, d.data = title, sheet, data
        d.save()
    else:
        d = CadDrawing.objects.create(certification=cert, owner=request.user,
                                      title=title, sheet=sheet, data=data)
    return JsonResponse({'ok': True, 'id': d.pk,
                         'updated': _when(d)})


@login_required
@require_POST
def drawing_delete(request, cert_id, pk):
    d = get_object_or_404(CadDrawing, pk=pk, certification_id=cert_id, owner=request.user)
    d.delete()
    return JsonResponse({'ok': True})


def _sym_row(s, user):
    return {'id': f'u{s.pk}', 'pk': s.pk, 'name': s.name, 'items': (s.data or {}).get('items', []),
            'shared': s.shared, 'mine': s.owner_id == user.pk}


@login_required
def symbol_list(request):
    from django.db.models import Q
    rows = CadSymbol.objects.filter(Q(owner=request.user) | Q(shared=True))
    return JsonResponse({'ok': True, 'items': [_sym_row(s, request.user) for s in rows],
                         'staff': request.user.is_staff})


@login_required
@require_POST
def symbol_save(request):
    """새 기호 등록. pk 가 있으면 이름·공유만 고친다(모양은 다시 등록해 바꾼다)."""
    body = _body(request)
    if not isinstance(body, dict):
        return _err('본문을 읽지 못했습니다.')
    name = str(body.get('name') or '').strip()[:60]
    if body.get('pk'):
        s = get_object_or_404(CadSymbol, pk=body['pk'])
        if s.owner_id != request.user.pk and not request.user.is_staff:
            return _err('권한이 없습니다.', 403)
        if name:
            s.name = name
        if 'shared' in body and request.user.is_staff:
            s.shared = bool(body['shared'])
        s.save()
        return JsonResponse({'ok': True, 'item': _sym_row(s, request.user)})
    items = body.get('items')
    if not name:
        return _err('이름을 적어 주세요.')
    if not isinstance(items, list) or not items:
        return _err('기호에 담을 객체가 없습니다.')
    if len(json.dumps(items, ensure_ascii=False)) > 100_000:
        return _err('기호가 너무 큽니다.')
    s = CadSymbol.objects.create(owner=request.user, name=name, data={'items': items},
                                 shared=bool(body.get('shared')) and request.user.is_staff)
    return JsonResponse({'ok': True, 'item': _sym_row(s, request.user)})


@login_required
@require_POST
def symbol_delete(request, pk):
    s = get_object_or_404(CadSymbol, pk=pk)
    if s.owner_id != request.user.pk and not request.user.is_staff:
        return _err('권한이 없습니다.', 403)
    s.delete()
    return JsonResponse({'ok': True})
