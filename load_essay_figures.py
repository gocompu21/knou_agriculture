# -*- coding: utf-8 -*-
"""자체 제작 SVG를 PNG로 변환해 문항 이미지로 교체한다.

SVG를 그대로 쓰지 않고 PNG로 굽는 이유:
  - 기존 ImageField 파이프라인(배포 zip, vurl 캐시 무력화)을 그대로 쓴다
  - 인쇄 시험지에서 SVG 렌더링 차이가 없다
2배 해상도로 구워 고해상도 화면에서도 선명하게 한다.

사용:
  python load_essay_figures.py                # 검증만
  python load_essay_figures.py --apply        # DB 반영
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

import django

sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.files import File          # noqa: E402
from gisa.models import GisaEssayQuestion   # noqa: E402

SRC_DIR = '_figwork'
FIG_DIR = '_figures'
MARK = '[도해 자체제작]'

CHROME_CANDIDATES = [
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
]


def find_browser():
    for c in CHROME_CANDIDATES:
        if os.path.exists(c):
            return c
    return None


def svg_size(path):
    """viewBox에서 폭·높이를 읽는다."""
    import re
    s = open(path, encoding='utf-8').read(2000)
    m = re.search(r'viewBox\s*=\s*"([\d.\s-]+)"', s)
    if m:
        parts = m.group(1).split()
        if len(parts) == 4:
            return int(float(parts[2])), int(float(parts[3]))
    return 900, 400


def render_png(svg_path, out_png, browser, scale=2):
    """headless 브라우저로 SVG → PNG (2배 해상도)."""
    w, h = svg_size(svg_path)
    tmp = tempfile.mkdtemp()
    try:
        shutil.copy2(svg_path, os.path.join(tmp, 'f.svg'))
        html = os.path.join(tmp, 'v.html')
        with open(html, 'w', encoding='utf-8') as fh:
            fh.write('<!doctype html><meta charset="utf-8">'
                     '<body style="margin:0;background:#fff">'
                     f'<img src="f.svg" width="{w}"></body>')
        url = 'file:///' + html.replace('\\', '/')
        subprocess.run([
            browser, '--headless', '--disable-gpu',
            '--user-data-dir=' + os.path.join(tmp, 'prof'),
            f'--screenshot={out_png}',
            f'--window-size={w},{h}',
            '--hide-scrollbars',
            f'--force-device-scale-factor={scale}',
            url,
        ], capture_output=True, timeout=90)
        return os.path.exists(out_png)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default=SRC_DIR)
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    browser = find_browser()
    if not browser:
        print('Chrome/Edge를 찾을 수 없습니다')
        return

    rows = []
    for f in sorted(glob.glob(os.path.join(args.src, '*.json'))):
        try:
            rows += json.load(open(f, encoding='utf-8'))
        except Exception as e:
            print(f'  {os.path.basename(f)} 파싱 실패: {e}')

    done = [r for r in rows if r.get('done') and r.get('svg_name')]
    to_table = [r for r in rows if r.get('to_table')]
    to_delete = [r for r in rows if r.get('to_delete')]
    pending = [r for r in rows
               if not r.get('done') and not r.get('to_table') and not r.get('to_delete')]

    print(f'전체 {len(rows)} | SVG 제작 {len(done)} | '
          f'표 전환 {len(to_table)} | 삭제 {len(to_delete)} | 미처리 {len(pending)}')

    missing = []
    for r in done:
        p = os.path.join(FIG_DIR, r['svg_name'] + '.svg')
        if not os.path.exists(p):
            missing.append((r, p))
    if missing:
        print(f'\n[SVG 파일 없음 {len(missing)}건]')
        for r, p in missing[:10]:
            print(f'  {r["label"]} {r["number"]}번 → {p}')

    if pending:
        print(f'\n[미처리 {len(pending)}건]')
        for r in pending[:10]:
            print(f'  {r["label"]} {r["number"]}번 [{r["qtype"]}] {r["text"][:40]}')

    if not args.apply:
        print('\n[dry-run] --apply 를 붙이면 DB에 반영합니다')
        return

    ok = fail = 0
    tmpdir = tempfile.mkdtemp()
    try:
        for r in done:
            svg = os.path.join(FIG_DIR, r['svg_name'] + '.svg')
            if not os.path.exists(svg):
                fail += 1
                continue
            q = GisaEssayQuestion.objects.filter(pk=r['pk']).first()
            if not q:
                fail += 1
                continue

            # 교체 대상 필드 — answer_image 우선, 없으면 첫 이미지 필드
            field = 'answer_image'
            fields = [i['field'] for i in r.get('images', [])]
            if 'answer_image' not in fields and fields:
                field = fields[0]

            png = os.path.join(tmpdir, r['svg_name'] + '.png')
            if not render_png(svg, png, browser):
                print(f'  렌더 실패: {r["svg_name"]}')
                fail += 1
                continue

            # 교재 원본 백업 (한 번만)
            cur = getattr(q, field)
            if cur and cur.name:
                try:
                    p = cur.path
                    if os.path.exists(p) and not os.path.exists(p + '.orig'):
                        shutil.copy2(p, p + '.orig')
                except Exception:
                    pass

            base = os.path.basename(cur.name) if (cur and cur.name) \
                else f'{r["svg_name"]}.png'
            with open(png, 'rb') as fh:
                getattr(q, field).save(base, File(fh), save=False)
            if MARK not in (q.notes or ''):
                q.notes = ((q.notes or '') + f' {MARK}').strip()
            q.save(update_fields=[field, 'notes'])
            ok += 1
            print(f'  OK {q.label} {q.number}번 ← {r["svg_name"]}')
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print(f'\n교체 완료 {ok} / 실패 {fail}')


if __name__ == '__main__':
    main()
