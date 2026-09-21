# -*- coding: utf-8 -*-
"""동영상을 기출 도면에 잇는다 — 분류 이름 끝의 도면 번호를 `drawing_code` 로 옮긴다.

작업형 동영상은 이미 `호안생태공원 428` · `주차장설계 444` 처럼 **분류 이름에 도면
번호가 들어 있다**. 제목으로 맞히려 들 것 없이 그 번호를 쓰면 정확하다 — 분류는
사람이 직접 지은 것이다.

이어 두면 기출분석 탭의 그 도면 줄에 **동영상 탭**이 생긴다(`essay_views.vids_of`).
분류에 번호가 없는 것(기본2 · 일반 · 도시공원)은 잇지 않는다.

    python link_ls_drawing_videos.py                 # 무엇이 이어질지 보기만
    python link_ls_drawing_videos.py --apply         # 전부 반영
    python link_ls_drawing_videos.py --apply 428     # 그 도면만
"""
import os
import re
import sys

import django

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from gisa.models import (Certification, GisaDrawingRef,  # noqa: E402
                         GisaDrawingTask, GisaResource)

CERT = '조경기사'
# 분류 이름 끝의 세 자리 번호 — "호안생태공원 428", "묘지공원 및 도시미관광장 344"
CODE_RE = re.compile(r'(?:^|\s)(\d{3})\s*$')


def main():
    apply_ = '--apply' in sys.argv
    only = {a for a in sys.argv[1:] if a.isdigit()}
    cert = Certification.objects.get(name=CERT)

    rows = (GisaResource.objects
            .filter(certification=cert, part='work', kind='youtube')
            .select_related('category').order_by('category__name', 'order', 'pk'))

    # 그 번호의 도면이 실제로 있는지 — 분류 이름의 번호가 어긋나면 이어 봐야
    # 화면 어디에도 안 나온다(묘지공원 분류가 344 인데 도면은 345 였다)
    known = set(GisaDrawingTask.objects.filter(certification=cert)
                .exclude(code='').values_list('code', flat=True))
    known |= set(GisaDrawingRef.objects.filter(certification=cert)
                 .exclude(code='').values_list('code', flat=True))

    by_code, skipped, changed = {}, [], 0
    for v in rows:
        name = v.category.name if v.category_id else ''
        m = CODE_RE.search(name)
        if not m:
            skipped.append(name or '(분류 없음)')
            continue
        code = m.group(1)
        if only and code not in only:
            continue
        by_code.setdefault(code, []).append(v)

    unknown = []
    for code in sorted(by_code):
        vids = by_code[code]
        todo = [v for v in vids if v.drawing_code != code]
        if code not in known:
            unknown.append((code, vids[0].category.name, len(vids)))
        print(f"{code} · {vids[0].category.name} — 영상 {len(vids)}편"
              + (f" · 새로 이을 것 {len(todo)}편" if todo else " · 이미 이어져 있음")
              + ('   << 그런 도면이 없다' if code not in known else ''))
        for v in todo:
            print(f"    + {v.title[:58]}"
                  + (f"   (지금 {v.drawing_code})" if v.drawing_code else ''))
        if apply_ and todo:
            for v in todo:
                v.drawing_code = code
            GisaResource.objects.bulk_update(todo, ['drawing_code'])
            changed += len(todo)

    if skipped:
        from collections import Counter
        print('\n번호 없는 분류라 건너뜀:',
              ', '.join(f'{n}({c})' for n, c in Counter(skipped).items()))
    if unknown:
        print('\n⚠ 그런 도면 번호가 없어 화면 어디에도 안 나온다 — 분류 이름의 번호를 고칠 것:')
        for code, name, n in unknown:
            print(f'    {code} · {name} — 영상 {n}편')
    print(f"\n{changed}편 반영" if apply_ else "\n검사만 했습니다 (--apply 로 반영)")


if __name__ == '__main__':
    main()
