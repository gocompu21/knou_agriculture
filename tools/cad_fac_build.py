import os, sys, re, json
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
SP = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(SP, 'fac_rows.json'), encoding='utf-8'))
rows = [r for r in rows if r['unit'] != 'm']          # 선 시설(배관·배선·펜스)은 넣는 기호가 아니다
def num(s): return float(s.replace(',', ''))
def size(spec, name):
    sp = spec.replace(' ', '')
    m = re.match(r'([\d,]+)×([\d,]+)', sp)
    if m: return num(m.group(1)) / 1000, num(m.group(2)) / 1000, 'box'
    m = re.search(r'[ØD]([\d,]+)', sp)
    if m and not re.search(r'L[\d,]', sp): d = num(m.group(1)) / 1000; return d, d, 'box'
    m = re.search(r'L([\d,]+)', sp)
    if m: return num(m.group(1)) / 1000, None, 'w'
    m = re.search(r'W=?([\d,]+)', sp)
    if m and '인용' not in name: return num(m.group(1)) / 1000, None, 'w'
    if '4m²' in sp: return 2, 2, 'box'
    if '인용' in name: return 1.8, None, 'w'
    if re.search(r'H', sp):                             # 높이만 적힌 것 — 평면 크기는 모른다: 등·표지류는 작게
        return (0.6 if ('등' in name or '안내' in name or '표' in name) else 1.5), None, 'w'
    if any(k in name for k in ('놀이', '미끄럼', '시소', '정글', '철봉', '그네', '래더', '회전')): return 3, None, 'w'
    return 1.5, None, 'w'
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome'); pg = b.new_page()
    out = []
    for i, r in enumerate(rows):
        svg = re.sub(r'stroke-width="[\d.]+"', 'stroke-width="1.1"', r['svg'])
        svg = re.sub(r'<(line|path|rect|circle|ellipse|polyline|polygon)\b', r'<\1 vector-effect="non-scaling-stroke"', svg)
        pg.set_content(f'<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><g id="g">{svg}</g></svg>')
        bb = pg.evaluate("(()=>{const b=document.getElementById('g').getBBox();return [b.x,b.y,b.width,b.height]})()")
        w, h, mode = size(r['spec'], r['name'])
        if h is None: h = w * bb[3] / bb[2] if bb[2] else w
        out.append({'id': 'f:' + r['name'], 'name': r['name'], 'spec': r['spec'], 'code': r['code'],
                    'items': [{'t': 'svg', 'svg': svg, 'bb': [round(v, 2) for v in bb], 'w': round(w, 3), 'h': round(h, 3)}]})
    b.close()
json.dump(out, open(os.path.join(SP, 'fac_lib.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(len(out), os.path.getsize(os.path.join(SP, 'fac_lib.json')))
for o in out[:80]: print(o['name'], o['spec'], o['items'][0]['w'], o['items'][0]['h'], o['items'][0]['bb'])
