import json, re, copy, sys
DX, DY, K = 24.0, 28.0, 0.5          # 옮김(m), 종이 기준 크기 비율(800→400)
r3 = lambda v: round(v, 3)
def fix_sizes(tl):
    # 원본(1:800 모눈종이, 높이 130m)에서 쓴 자의 실제 크기를 기록 — 재생은 이 값을 쓴다
    if tl.get('tri') and tl['tri'].get('len') is None:
        t = tl['tri']; L = (t.get('pct') or 100) / 100 * 130
        if t.get('kind') == '45': L = max(5, round(L / 5) * 5)
        t['len'] = round(L, 3)
    for k in ('tpl', 'sr', 'ftri'):
        if tl.get(k) and tl[k].get('den') is None: tl[k]['den'] = 800
def conv(d):
    d = copy.deepcopy(d)
    d['sheet'] = 'a2-400'
    for p in d['pts']:
        p['x'] = r3(p['x'] + DX); p['y'] = r3(p['y'] + DY)
    letters = set()
    for o in d['ops']:
        t = o['t']
        if t == 'text':
            o['x'] = r3(o['x'] + DX); o['y'] = r3(o['y'] + DY)
            if o.get('size'): o['size'] = r3(o['size'] * K)      # 종이 위 글자 크기는 그대로
        if t == 'free' and o.get('pts'):
            o['pts'] = [[r3(a + DX), r3(b + DY)] for a, b in o['pts']]
        if o.get('mark'): o['mark']['s'] = 400
        if t == 'fill':
            letters |= set(re.findall(r'[A-Za-z]', o['d']))
            nums = iter(re.findall(r'-?\d+(?:\.\d+)?', o['d']))
            def rep(m, c=[0]):
                v = float(m.group(0)); c[0] += 1
                return str(r3(v + (DX if c[0] % 2 == 1 else DY)))
            o['d'] = re.sub(r'-?\d+(?:\.\d+)?', rep, o['d'])
            if o.get('bb'): b = o['bb']; o['bb'] = [r3(b[0]+DX), r3(b[1]+DY), r3(b[2]+DX), r3(b[3]+DY)]
            if o.get('den'): o['den'] = 400
            if o.get('cuts'): o['cuts'] = [[r3(c[0]+DX), r3(c[1]+DY)] + list(c[2:]) for c in o['cuts']]
        tl = o.get('tl')
        if isinstance(tl, dict):
            fix_sizes(tl)
            if tl.get('bar') is not None: tl['bar'] = r3(tl['bar'] + DY)
            if tl.get('tri') and tl['tri'].get('x') is not None: tl['tri']['x'] = r3(tl['tri']['x'] + DX)
            for k in ('tpl', 'sr', 'ftri'):
                if tl.get(k):
                    tl[k]['x'] = r3(tl[k]['x'] + DX); tl[k]['y'] = r3(tl[k]['y'] + DY)
    return d, letters
if __name__ == '__main__':
    j = json.load(open(sys.argv[1], encoding='utf-8'))
    nd, letters = conv(j['d'])
    print('path letters', letters)
    xs = [p['x'] for p in nd['pts']]; ys = [p['y'] for p in nd['pts']]
    print('pts range', min(xs), max(xs), min(ys), max(ys))
    json.dump({'t': '주차공원444(1:400)', 's': 'a2-400', 'd': nd}, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False)
