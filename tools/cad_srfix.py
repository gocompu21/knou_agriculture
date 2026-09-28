import json, math, copy, sys
SR_Z, SR_RUN, SR_W = 8.5, 300.0, 14.5; SR_L = SR_Z*2 + SR_RUN; SR_MARK = 0.75
SRG = {100,200,300,400,500,600}
FACES = [(100,200),(300,400),(500,600)]
def nice(v):
    p = 10 ** math.floor(math.log10(v)); 
    for m in (1,2,5,10):
        if v <= m*p + 1e-9: return m*p
def srRun(S):
    if S in SRG: return SR_RUN
    perM = 1000/S; lab = nice(12/perM)
    return math.floor(SR_RUN/perM/lab + 1e-9) * lab * perM
def view(s):
    if s.get('custom'): return s['custom'], s['custom']
    r = s.get('roll', 2); A = FACES[(r+1)%3]; B = FACES[(r+2)%3]
    return A[0], B[1]
def sr_map(s, k, u, v):
    a = math.radians((s.get('rot') or 0) + (180 if s.get('swap') else 0))
    cx, cy = s['x'] + SR_L*k/2, s['y'] + SR_W*k/2
    du, dv = (u - SR_L/2)*k, (v - SR_W/2)*k
    return cx + du*math.cos(a) - dv*math.sin(a), cy + du*math.sin(a) + dv*math.cos(a)
def edges(s, k):
    top, bot = view(s)
    return [(0.0, top, SR_Z, 1), (SR_W, bot, SR_Z + srRun(bot), -1)]
def place(P0, a_deg, k):
    a = math.radians(a_deg); du, dv = (SR_Z - SR_L/2)*k, (0 - SR_W/2)*k
    cx = P0[0] - (du*math.cos(a) - dv*math.sin(a)); cy = P0[1] - (du*math.sin(a) + dv*math.cos(a))
    return round(cx - SR_L*k/2, 4), round(cy - SR_W*k/2, 4)
K_OLD, K_NEW, S_NEW = 0.8, 0.4, 400
RUN_M = srRun(S_NEW) * K_NEW            # 120m
STEP = 100.0                            # 한 번에 재는 최대 길이 — 눈금 끝(120)까지 가지 않고 100m 에서 옮긴다
def fix(d):
    P = {p['n']: p for p in d['pts']}
    nmax = max(P); seq = d.get('seq', max(o['id'] for o in d['ops']) + 1)
    out_ops = []; nsplit = 0; nmark = 0; made = {}
    for p in d['pts']: made.setdefault((round(p['x'],2), round(p['y'],2)), p['n'])
    for o in d['ops']:
        if not (o.get('mark') and o.get('p') in P and isinstance(o.get('tl'), dict) and o['tl'].get('sr')):
            out_ops.append(o); continue
        nmark += 1
        s = o['tl']['sr']; M = (P[o['p']]['x'], P[o['p']]['y']); r = float(o['mark']['r'])
        # 원래 자에서 이 마킹이 놓인 모서리와 0 자리(원래 자는 1:800 크기)
        best = None
        for v, S, u0, du in edges(s, K_OLD):
            e0 = sr_map(s, K_OLD, 0, v); e1 = sr_map(s, K_OLD, SR_L, v)
            ex, ey = e1[0]-e0[0], e1[1]-e0[1]; n = math.hypot(ex, ey); ex, ey = ex/n, ey/n
            dist = abs((M[0]-e0[0])*ey - (M[1]-e0[1])*ex)
            if best is None or dist < best[0]:
                Z = sr_map(s, K_OLD, u0, v); dirv = (ex*du, ey*du)
                best = (dist, Z, dirv)
        _, Z, dv = best
        if r > 1e-6: dv = ((M[0]-Z[0])/r, (M[1]-Z[1])/r); nn = math.hypot(*dv); dv = (dv[0]/nn, dv[1]/nn)
        ang = math.degrees(math.atan2(dv[1], dv[0])) % 180
        horiz = min(ang, 180 - ang) < 3; vert = abs(ang - 90) < 3
        # 거의 가로·세로면 정확히 세운다 — 원래 0 자리와 마킹 점이 1m 남짓 어긋나 있어 자가 89°로 기울었다(대표님)
        if vert: Z = (M[0], Z[1]); dv = (0.0, 1.0 if M[1] >= Z[1] else -1.0); r = abs(M[1] - Z[1]) if r > 1e-6 else r
        if horiz: Z = (Z[0], M[1]); dv = (1.0 if M[0] >= Z[0] else -1.0, 0.0); r = abs(M[0] - Z[0]) if r > 1e-6 else r
        a_deg = 0 if horiz else 90 if vert else round(math.degrees(math.atan2(dv[1], dv[0])), 3)
        ax = (math.cos(math.radians(a_deg)), math.sin(math.radians(a_deg)))
        outv = (math.sin(math.radians(a_deg)), -math.cos(math.radians(a_deg)))
        # Z 에서 M 까지를 STEP 씩 끊는다
        stops = []; t = STEP
        while r > RUN_M + 1e-6 and t < r - 1e-6: stops.append(t); t += STEP
        pts_chain = [Z] + [(Z[0]+dv[0]*t, Z[1]+dv[1]*t) for t in stops] + [M]
        for i in range(1, len(pts_chain)):
            S0, E0 = pts_chain[i-1], pts_chain[i]
            zero = S0 if (E0[0]-S0[0])*ax[0] + (E0[1]-S0[1])*ax[1] >= 0 else E0
            x, y = place(zero, a_deg, K_NEW)
            ns = {'x': x, 'y': y, 'rot': a_deg, 'roll': 2, 'custom': S_NEW, 'den': S_NEW}
            tl = copy.deepcopy(o['tl']); tl['sr'] = ns
            if horiz: tl['bar'] = round(y + SR_W*K_NEW, 4)       # 자를 I자 윗날에 붙인다
            reading = round(stops[i-1] if i-1 < len(stops) else r, 4)
            tick = [[round(E0[0],4), round(E0[1],4)], [round(E0[0]+outv[0]*SR_MARK*K_NEW,4), round(E0[1]+outv[1]*SR_MARK*K_NEW,4)]]
            if i < len(pts_chain) - 1 and (round(E0[0],2), round(E0[1],2)) in made:
                continue                                        # 이미 표시한 자리 — 자만 옮겨 이어 잰다
            if i < len(pts_chain) - 1:                          # 중간 표시 — 새 마킹 점
                nmax += 1; d['pts'].append({'n': nmax, 'x': round(E0[0],3), 'y': round(E0[1],3)}); made[(round(E0[0],2), round(E0[1],2))] = nmax
                out_ops.append({'id': seq, 't': 'free', 'pts': tick, 'ls': o.get('ls','solid'), 'w': o.get('w','p9'),
                                'mark': {'s': S_NEW, 'r': reading}, 'p': nmax, 'tl': tl}); seq += 1; nsplit += 1
            else:
                o['tl'] = tl; o['pts'] = tick; o['mark'] = {'s': S_NEW, 'r': r}; out_ops.append(o)
    # 마킹이 아닌 작도의 스케일자 기록도 1:400 자로
    for o in out_ops:
        tl = o.get('tl')
        if isinstance(tl, dict) and tl.get('sr') and not o.get('mark'):
            tl['sr']['custom'] = S_NEW; tl['sr']['den'] = S_NEW
    d['ops'] = out_ops; d['seq'] = seq
    return nmark, nsplit
if __name__ == '__main__':
    j = json.load(open(sys.argv[1], encoding='utf-8'))
    nm, ns = fix(j['d'])
    print('marks', nm, 'added intermediate marks', ns, 'ops', len(j['d']['ops']), 'run m', RUN_M)
    json.dump(j, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False)
