# -*- coding: utf-8 -*-
"""교재 이미지를 쓰는 문항을 배치로 뽑는다 (자체 도해 제작용).

각 배치에 문항 정보(문제·답·이미지 경로)를 담아 두면, 작업자가
이미지를 직접 보고 답 텍스트를 근거로 SVG를 새로 그릴 수 있다.

사용:
  python dump_essay_figures.py                     # 현황
  python dump_essay_figures.py --out-dir _figwork  # 배치 생성
"""
import argparse
import json
import os
import sys
from collections import Counter

import django

sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from gisa.models import Certification, GisaEssayQuestion   # noqa: E402

FIELDS = ['text_image', 'answer_image', 'reference_image']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cert', default='자연생태복원기사')
    ap.add_argument('--out-dir', default='')
    ap.add_argument('--batch-size', type=int, default=8)
    args = ap.parse_args()

    cert = Certification.objects.filter(name=args.cert).first()
    if not cert:
        print(f'자격증 없음: {args.cert}')
        return

    rows = []
    for q in GisaEssayQuestion.objects.filter(certification=cert).order_by(
            'source', 'section', '-year', '-round', 'number'):
        imgs = []
        for f in FIELDS:
            v = getattr(q, f)
            if v and v.name:
                imgs.append({'field': f, 'path': v.path.replace('\\', '/')})
        if not imgs:
            continue
        # 이미 자체 제작한 것은 건너뜀
        if '[도해 자체제작]' in (q.notes or ''):
            continue
        rows.append({
            'pk': q.pk,
            'label': q.label,
            'number': q.number,
            'qtype': q.qtype,
            'text': q.text,
            'answer_items': q.answer_items or [],
            'answer_text': q.answer_text or '',
            'images': imgs,
            'svg_name': '',      # 작업자가 채운다: _figures/<이름>.svg
            'done': False,
        })

    print(f'이미지 보유 문항 {len(rows)}건 (자체제작 완료분 제외)')
    print('[유형]', dict(Counter(r['qtype'] for r in rows)))
    grp = Counter()
    for r in rows:
        grp[r['label'] if '년' in str(r['label']) else r['label']] += 1
    print('[영역·회차]', dict(sorted(grp.items(), key=lambda x: -x[1])))

    if not args.out_dir:
        print('\n--out-dir 을 주면 배치 파일을 만듭니다')
        return

    os.makedirs(args.out_dir, exist_ok=True)
    n = 0
    for i in range(0, len(rows), args.batch_size):
        chunk = rows[i:i + args.batch_size]
        name = f'fig_{i // args.batch_size + 1:02d}.json'
        with open(os.path.join(args.out_dir, name), 'w', encoding='utf-8') as f:
            json.dump(chunk, f, ensure_ascii=False, indent=1)
        n += 1
    print(f'\n배치 {n}개 생성 → {args.out_dir}')


if __name__ == '__main__':
    main()
