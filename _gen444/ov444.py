"""평면 렌더 위에 CAD 도면 선을 빨갛게 얹어 어긋남을 본다.  python ov444.py t.png out.png"""
import json, sys, math
from PIL import Image, ImageDraw
src, out = sys.argv[1], sys.argv[2]
im = Image.open(src).convert('RGB')
W, H = im.size
k = W / 190.0                       # px/m — TOP_VIEW ortho_scale 168 (가로 기준)
cx, cy = 73.0, 107.0 - 54.5        # 카메라 중심(도면 좌표)
d = json.load(open('d444.json', encoding='utf-8'))
P = {p['n']: (p['x'], p['y']) for p in d['pts']}
T = lambda x, y: (W / 2 + (x - cx) * k, H / 2 + (y - cy) * k)
dr = ImageDraw.Draw(im)
for o in d['ops']:
    if o.get('mark') or o.get('ls') == 'aux':
        continue
    if o['t'] == 'line':
        a, b = P[o['a']], P[o['b']]
        dr.line([T(*a), T(*b)], fill=(255, 0, 0), width=2)
    elif o['t'] == 'circle':
        c = P[o['c']]; r = (o.get('v') or 1) / (2 if o.get('mode') == 'd' else 1) * k
        x, y = T(*c); dr.ellipse([x - r, y - r, x + r, y + r], outline=(255, 0, 0), width=2)
im.save(out)
print('ok', W, H, k)
