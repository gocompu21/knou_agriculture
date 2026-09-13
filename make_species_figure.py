# -*- coding: utf-8 -*-
"""수종 식별 문항의 해설 그림을 만든다 — 위키미디어 공용 사진을 격자로 붙인다.

꽃 색·열매 색·수피·잎 모양으로 수종을 가르는 문항은 글로 읽는 것보다 한 번
보는 편이 확실히 남는다. 답에 나오는 종을 격자로 붙여 해설 그림
(`reference_image`)으로 넣는다 — 화면은 이미 이 필드를 렌더한다.

사진은 잡초 카드와 같은 길을 쓴다.
  - **학명으로** 찾는다. 한국어 이름으로는 거의 안 나온다
  - 후보를 한 장에 붙여 **눈으로 고른다**. 자동으로 첫 장을 쓰면 잎·수피·세밀화가
    들어간다 — 실제로 6장 중 꽃이 보이는 것은 한둘뿐인 종이 많다
  - CC 라이선스라 저작자를 그림 아래에 적는다

  python make_species_figure.py --fig bloom_a --list     후보 검색
  python make_species_figure.py --fig bloom_a --thumbs   눈으로 고를 시트
  python make_species_figure.py --fig bloom_a --build    고른 사진으로 합성
  python make_species_figure.py --fig bloom_a --build --apply
  python make_species_figure.py --apply-all              만들어 둔 그림을 모두 붙인다
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

GI, SI = '조경기사', '조경산업기사'

# 그림마다 (붙일 문항, 열 수, [(이름, 학명, 아래에 덧붙일 말)])
FIGURES = {
    # 이미 만든 것 (make_flower_figure.py 로 만들었고 여기서도 다시 만들 수 있다)
    'yellow': {
        'target': (SI, 2023, 1, 3), 'cols': 2,
        'species': [
            ('산수유', 'Cornus officinalis', '3~4월'),
            ('생강나무', 'Lindera obtusiloba', '3월'),
            ('모감주나무', 'Koelreuteria paniculata', '6~7월'),
            ('히어리', 'Corylopsis coreana', '3~4월'),
        ],
    },
    # 개화 순서 — 왼쪽부터 피는 차례대로 늘어놓는다
    'bloom_a': {
        'target': (GI, 2024, 1, 8), 'cols': 3,
        'species': [
            ('생강나무', 'Lindera obtusiloba', '3월'),
            ('수수꽃다리', 'Syringa oblata var. dilatata', '4월'),
            ('이팝나무', 'Chionanthus retusus', '5~6월'),
            ('산수국', 'Hydrangea serrata', '7~8월'),
            ('능소화', 'Campsis grandiflora', '8~9월'),
        ],
    },
    'bloom_b': {
        'target': (GI, 2025, 2, 10), 'cols': 2,
        'species': [
            ('산수유', 'Cornus officinalis', '3~4월'),
            ('이팝나무', 'Chionanthus retusus', '5~6월'),
            ('쉬땅나무', 'Sorbaria sorbifolia', '6~7월'),
            ('금목서', 'Osmanthus fragrans var. aurantiacus', '9~10월'),
        ],
    },
    # 붉은 열매
    'redfruit': {
        'target': (GI, 2023, 1, 4), 'cols': 2,
        'species': [
            ('산수유', 'Cornus officinalis fruits', '붉은 핵과'),
            ('자금우', 'Ardisia japonica fruit', '상록 지피 / 겨울 열매'),
            ('팥배나무', 'Sorbus alnifolia fruits', '팥알만 한 열매가 무리로'),
            ('낙상홍', 'Ilex serrata fruits', '잎 진 뒤에도 남는다'),
        ],
    },
    # 수피 색 — 모과나무는 공용에 수피 사진이 없어 뺐다(해설 글에는 남아 있다)
    'bark': {
        'target': (GI, 2024, 3, 7), 'cols': 3,
        'species': [
            ('자작나무', 'Betula pendula bark', '흰색'),
            ('노각나무', 'Stewartia pseudocamellia bark', '얼룩무늬'),
            ('배롱나무', 'Lagerstroemia indica bark', '얼룩무늬'),
            ('벽오동', 'Firmiana simplex bark', '녹색'),
            ('흰말채나무', 'Cornus alba stems', '붉은 가지'),
        ],
    },
    # 참나무 여섯 종 — 잎자루와 잎 모양으로 가른다
    'oak': {
        'target': (GI, 2023, 2, 12), 'cols': 3,
        'species': [
            ('졸참나무', 'Quercus serrata leaves', '잎 작고 잎자루 뚜렷'),
            ('갈참나무', 'Quercus aliena leaves', '잎 작고 잎자루 뚜렷'),
            ('상수리나무', 'Quercus acutissima leaves', '좁고 길다'),
            ('굴참나무', 'Quercus variabilis leaves', '좁고 길다 / 코르크 수피'),
            ('떡갈나무', 'Quercus dentata leaves', '잎 크고 잎자루 없다'),
            ('신갈나무', 'Quercus mongolica leaves', '잎 크고 잎자루 없다'),
        ],
    },
    # 단풍나무과 — 갈라진 수와 가장자리
    'maple': {
        'target': (GI, 2023, 4, 7), 'cols': 3,
        'species': [
            ('복자기', 'Acer triflorum leaves', '소엽 3장 겹잎'),
            ('중국단풍', 'Acer buergerianum leaves', '3갈래 / 가장자리 밋밋'),
            ('신나무', 'Acer ginnala leaves', '3갈래 / 거치 있음'),
        ],
    },
}
UA = 'Mozilla/5.0 (hanulstudy; +https://hanulstudy.kr)'
TMP = '_spec_tmp'


def paths(key):
    return f'_spec_{key}_cand.json', f'_spec_{key}_pick.json', f'_spec_{key}.png'


def fetch(url, path):
    req = urllib.request.Request(url, headers={
        'User-Agent': UA, 'Referer': 'https://commons.wikimedia.org/'})
    with urllib.request.urlopen(req, timeout=20) as r, open(path, 'wb') as f:
        f.write(r.read())


def _font(size, bold=True):
    for p in ([r'C:\Windows\Fonts\malgunbd.ttf'] if bold else []) + [
            r'C:\Windows\Fonts\malgun.ttf',
            '/usr/share/fonts/truetype/nanum/NanumGothic.ttf']:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def cmd_list(key):
    cache, _, _ = paths(key)
    cand = {}
    for name, sci, _sub in FIGURES[key]['species']:
        rows = _weed_web_photos(name, sci, limit=6)
        cand[name] = rows
        print(f'  {name} ({sci}) — {len(rows)}장')
    json.dump(cand, io.open(cache, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{cache} 에 담았다.')


def cmd_thumbs(key):
    cache, _, _ = paths(key)
    cand = json.load(io.open(cache, encoding='utf-8'))
    os.makedirs(TMP, exist_ok=True)
    cols = max((len(v) for v in cand.values()), default=1)
    cw, ch = 230, 190
    sheet = Image.new('RGB', (cols * cw, len(cand) * (ch + 22)), 'white')
    d = ImageDraw.Draw(sheet)
    font = _font(15)
    for r, (name, rows) in enumerate(cand.items()):
        d.text((4, r * (ch + 22) + 2), name, fill='black', font=font)
        for c, row in enumerate(rows):
            p = f'{TMP}/{key}_{name}_{c}.jpg'
            if not os.path.exists(p):
                try:
                    fetch(row['thumb'], p)
                except Exception as e:
                    print('  실패', name, c, e)
                    continue
            try:
                im = Image.open(p).convert('RGB')
            except Exception:
                continue
            im.thumbnail((cw - 8, ch - 8))
            sheet.paste(im, (c * cw + 4, r * (ch + 22) + 20))
            d.text((c * cw + 6, r * (ch + 22) + 4), f'[{c}]', fill='red', font=font)
    out = f'_spec_{key}_cand.png'
    sheet.save(out)
    print(f'{out} — 눈으로 고른 뒤 번호를 적는다')


def cmd_build(key, apply_):
    cache, pickf, out = paths(key)
    spec = FIGURES[key]
    cand = json.load(io.open(cache, encoding='utf-8'))
    pick = json.load(io.open(pickf, encoding='utf-8'))
    CW, CH, PAD, LAB, CREDIT = 280, 210, 6, 46, 15
    cols = spec['cols']
    items = spec['species']
    rows = (len(items) + cols - 1) // cols
    W = cols * (CW + PAD) + PAD
    H = rows * (CH + LAB + PAD) + PAD + 8
    sheet = Image.new('RGB', (W, H), 'white')
    d = ImageDraw.Draw(sheet)
    fname, fsub, fsrc = _font(18), _font(13, False), _font(11, False)
    credits = []
    for i, (name, _sci, sub) in enumerate(items):
        row = cand[name][pick[name]]
        p = f'{TMP}/{key}_{name}_{pick[name]}.jpg'
        if not os.path.exists(p):
            fetch(row['thumb'], p)
        im = Image.open(p).convert('RGB')
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
        d.text((x + (CW - tw) / 2, y + CH + 4), name, fill='#1b4332', font=fname)
        if sub:
            sw = d.textlength(sub, font=fsub)
            d.text((x + (CW - sw) / 2, y + CH + 25), sub, fill='#5a6b60', font=fsub)
        author = (row.get('author') or '').strip()
        credits.append(f'{name} {author}' if author else name)

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
    sheet = sheet.crop((0, 0, W, H + len(lines) * CREDIT + 6))
    d = ImageDraw.Draw(sheet)
    for i, ln in enumerate(lines):
        d.text((PAD, H + 2 + i * CREDIT), ln, fill='#777', font=fsrc)
    sheet.save(out)
    print(f'{out} {sheet.size}')
    if apply_:
        attach(key)


def attach(key):
    """만들어 둔 그림을 해당 문항의 해설 그림으로 붙인다.

    자격증 pk 가 로컬과 서버에서 다르므로(조경산업기사 7 / 4) 저장 경로가 갈린다.
    PNG 를 git 으로 옮기고 서버에서는 이 함수만 돌린다.
    """
    from django.core.files import File
    _, _, out = paths(key)
    name, y, r, n = FIGURES[key]['target']
    q = GisaEssayQuestion.objects.filter(
        certification__name=name, year=y, round=r, number=n).first()
    if not q:
        print(f'  !! 문항 없음: {name} {y}-{r} {n}번')
        return
    with open(out, 'rb') as f:
        q.reference_image.save(f'{key}.png', File(f), save=True)
    print(f'  붙였다: {name} {y}-{r} {n}번 → {q.reference_image.name}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--fig')
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--thumbs', action='store_true')
    ap.add_argument('--build', action='store_true')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--apply-all', action='store_true')
    a = ap.parse_args()
    if a.apply_all:
        for k in FIGURES:
            if os.path.exists(paths(k)[2]):
                attach(k)
    elif a.fig:
        if a.list:
            cmd_list(a.fig)
        if a.thumbs:
            cmd_thumbs(a.fig)
        if a.build:
            cmd_build(a.fig, a.apply)
