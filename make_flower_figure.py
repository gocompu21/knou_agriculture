# -*- coding: utf-8 -*-
"""노란 꽃 수종 해설 그림을 만든다 — 위키미디어 공용 사진을 격자로 붙인다.

조경산업기사 2023-1 3번(노란 꽃 피는 수종 고르기)의 해설에 붙일 그림이다.
꽃 색은 글로 읽는 것보다 한 번 보는 편이 확실히 남는다.

사진은 잡초 카드와 같은 길을 쓴다 — **학명으로** 위키미디어 공용을 찾고
(한국어 이름으로는 거의 안 나온다), CC 라이선스라 저작자·라이선스를 그림 아래에
적는다. 받아 온 사진은 반드시 눈으로 확인한 뒤 쓴다.

  python make_flower_figure.py --list          후보를 뽑아 본다
  python make_flower_figure.py --build         고른 사진으로 격자를 만든다
  python make_flower_figure.py --build --apply DB 의 reference_image 에 연결
"""
import argparse
import io
import json
import os
import sys
import urllib.request

import django

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from PIL import Image, ImageDraw, ImageFont      # noqa: E402

from gisa.models import GisaEssayQuestion        # noqa: E402
from main.views import _weed_web_photos          # noqa: E402

# 문제의 답 네 종. 학명을 줘야 제대로 찾는다.
SPECIES = [
    ('산수유', 'Cornus officinalis'),
    ('생강나무', 'Lindera obtusiloba'),
    ('모감주나무', 'Koelreuteria paniculata'),
    ('히어리', 'Corylopsis coreana'),
]
CACHE = '_flower_cand.json'
PICK = '_flower_pick.json'          # {종명: 후보 번호} — 눈으로 고른 결과
OUT = '_flower_yellow.png'
UA = 'Mozilla/5.0 (hanulstudy; +https://hanulstudy.kr)'


def fetch(url, path):
    req = urllib.request.Request(url, headers={
        'User-Agent': UA, 'Referer': 'https://commons.wikimedia.org/'})
    with urllib.request.urlopen(req, timeout=20) as r, open(path, 'wb') as f:
        f.write(r.read())


def cmd_list():
    cand = {}
    for name, sci in SPECIES:
        rows = _weed_web_photos(name, sci, limit=6)
        cand[name] = rows
        print(f'\n== {name} ({sci}) — {len(rows)}장')
        for i, r in enumerate(rows):
            print(f'  [{i}] {r.get("title", "")[:64]}')
            print(f'      {r.get("thumb")}')
    json.dump(cand, io.open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'\n{CACHE} 에 담았다. 썸네일을 받아 눈으로 고른 뒤 {PICK} 에 번호를 적는다.')


def cmd_thumbs():
    """후보를 한 장에 붙여 눈으로 고를 수 있게 한다."""
    cand = json.load(io.open(CACHE, encoding='utf-8'))
    os.makedirs('_flower_tmp', exist_ok=True)
    cols = max(len(v) for v in cand.values())
    cw, ch = 240, 200
    sheet = Image.new('RGB', (cols * cw, len(cand) * (ch + 22)), 'white')
    d = ImageDraw.Draw(sheet)
    font = _font(15)
    for r, (name, rows) in enumerate(cand.items()):
        d.text((4, r * (ch + 22) + 2), name, fill='black', font=font)
        for c, row in enumerate(rows):
            p = f'_flower_tmp/{name}_{c}.jpg'
            if not os.path.exists(p):
                try:
                    fetch(row['thumb'], p)
                except Exception as e:
                    print('실패', name, c, e)
                    continue
            im = Image.open(p).convert('RGB')
            im.thumbnail((cw - 8, ch - 8))
            sheet.paste(im, (c * cw + 4, r * (ch + 22) + 20))
            d.text((c * cw + 6, r * (ch + 22) + 4), f'[{c}]', fill='red', font=font)
    sheet.save('_flower_cand.png')
    print('_flower_cand.png — 눈으로 고른 뒤 번호를 적는다')


def _font(size):
    for p in (r'C:\Windows\Fonts\malgunbd.ttf', r'C:\Windows\Fonts\malgun.ttf'):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def cmd_build(apply_):
    cand = json.load(io.open(CACHE, encoding='utf-8'))
    pick = json.load(io.open(PICK, encoding='utf-8'))
    CW, CH, PAD, LAB = 300, 230, 6, 30
    cols = 2
    rows = (len(SPECIES) + cols - 1) // cols
    W = cols * (CW + PAD) + PAD
    # 출처는 CC 라이선스가 요구하는 표시라 잘리면 안 된다. 폭에 맞춰 접어 쓰므로
    # 줄 수를 먼저 세어 그만큼 아래를 비워 둔다.
    CREDIT_H = 15
    H = rows * (CH + LAB + PAD) + PAD + 10
    sheet = Image.new('RGB', (W, H), 'white')
    d = ImageDraw.Draw(sheet)
    fname, fsrc = _font(19), _font(11)
    credits = []
    for i, (name, _sci) in enumerate(SPECIES):
        row = cand[name][pick[name]]
        p = f'_flower_tmp/{name}_{pick[name]}.jpg'
        if not os.path.exists(p):
            fetch(row['thumb'], p)
        im = Image.open(p).convert('RGB')
        # 가운데를 잘라 칸을 꽉 채운다 — 꽃이 대개 가운데 있다
        sr, dr = im.width / im.height, CW / CH
        if sr > dr:
            w = int(im.height * dr)
            im = im.crop(((im.width - w) // 2, 0, (im.width + w) // 2, im.height))
        else:
            h = int(im.width / dr)
            im = im.crop((0, (im.height - h) // 2, im.width, (im.height + h) // 2))
        im = im.resize((CW, CH), Image.LANCZOS)
        x = PAD + (i % cols) * (CW + PAD)
        y = PAD + (i // cols) * (CH + LAB + PAD)
        sheet.paste(im, (x, y))
        d.rectangle([x, y, x + CW - 1, y + CH - 1], outline='#ccc')
        tw = d.textlength(name, font=fname)
        d.text((x + (CW - tw) / 2, y + CH + 5), name, fill='#1b4332', font=fname)
        author = (row.get('author') or '').strip()
        credits.append(f'{name} {author}' if author else name)
    # 출처 줄 — 폭을 넘으면 낱말 단위로 접는다
    words = ('사진: 위키미디어 공용 (CC) — ' + ' · '.join(credits)).split(' ')
    lines, cur = [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=fsrc) > W - 2 * PAD and cur:
            lines.append(cur)
            cur = w
        else:
            cur = t
    lines.append(cur)
    sheet = sheet.crop((0, 0, W, H + len(lines) * CREDIT_H + 6))
    d = ImageDraw.Draw(sheet)
    for i, ln in enumerate(lines):
        d.text((PAD, H + 2 + i * CREDIT_H), ln, fill='#777', font=fsrc)
    sheet.save(OUT)
    print(f'{OUT} {sheet.size}')

    if apply_:
        from django.core.files import File
        n = 0
        for q in GisaEssayQuestion.objects.filter(
                certification__name='조경산업기사', year=2023, round=1, number=3):
            with open(OUT, 'rb') as f:
                q.reference_image.save('yellow_flowers.png', File(f), save=True)
            n += 1
            print(f'  붙였다: {q.certification.name} {q.year}-{q.round} {q.number}번 '
                  f'→ {q.reference_image.name}')
        print(f'{n}건 반영했다.')


def cmd_attach():
    """만들어 둔 _flower_yellow.png 를 해당 문항의 해설 그림으로 붙인다."""
    from django.core.files import File
    n = 0
    for q in GisaEssayQuestion.objects.filter(
            certification__name='조경산업기사', year=2023, round=1, number=3):
        with open(OUT, 'rb') as f:
            q.reference_image.save('yellow_flowers.png', File(f), save=True)
        n += 1
        print(f'  붙였다: {q.certification.name} {q.year}-{q.round} {q.number}번 '
              f'→ {q.reference_image.name}')
    print(f'{n}건 반영했다.')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--thumbs', action='store_true')
    ap.add_argument('--build', action='store_true')
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    if a.list:
        cmd_list()
    if a.thumbs:
        cmd_thumbs()
    if a.build:
        cmd_build(a.apply)
    elif a.apply:
        # 서버에서는 이미 만들어 둔 그림을 붙이기만 한다 — 자격증 pk 가 달라
        # (로컬 7 / 서버 4) 저장 경로가 다르므로 파일은 git 으로 옮기고 여기서 붙인다.
        cmd_attach()
