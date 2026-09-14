# -*- coding: utf-8 -*-
"""곧게 편 시험지 사진 위에 채점 첨삭을 겹칠 자리를 잡는다.

LLM 에게 좌표를 묻지 않는다. 편 사진(essay_rectify, 10px/mm)에서는 인쇄물이 곧게
서 있으므로 이미지 분석으로 충분하고 흔들리지 않는다.

1. 답안 박스 — 굵은 실선 사각형 가운데 **안에 점선 괘선이 있는 것**(발문의 [box]
   지문 상자는 괘선이 없다).
2. 줄 — 괘선과 박스 윗변·밑변 사이의 띠. 글씨는 괘선 위에 쓰므로 띠 하나가 한 줄이다.
3. 글씨 — 띠 안의 잉크(테두리·괘선을 지운 것). 세로로 쌓아 가로 분포를 만든다.
4. 구절 위치 — 판독문의 줄을 잉크가 있는 띠에 차례로 짝짓고, 띄어쓰기로 나눈 낱말을
   잉크의 큰 틈으로 나눈 덩어리에 짝짓는다. 개수가 안 맞으면 잉크 양에 비례해 나눈다.

판독할 때(essay_ocr) 쪽마다 `page_layout` 을 계산해 `flat_info['layout']` 에 두고,
결과 화면이 첨삭을 요청하면(`build_overlay`) 그 배치와 채점 결과로 자리를 계산한다.
"""
import re

from .essay_rectify import PX_PER_MM

GUIDE_PX = 32 * 25.4 / 96 * PX_PER_MM   # 인쇄 괘선 간격 32px(CSS) = 8.47mm


# ── 1~3. 쪽 배치 ─────────────────────────────────────────────────────────────
def _masks(gray):
    import cv2
    import numpy as np
    bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                               cv2.THRESH_BINARY_INV, 31, 15)
    L = 6 * PX_PER_MM
    solid = cv2.bitwise_or(
        cv2.morphologyEx(bw, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (L, 1))),
        cv2.morphologyEx(bw, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, L))))
    closed = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1)))
    lines = cv2.morphologyEx(closed, cv2.MORPH_OPEN,
                             cv2.getStructuringElement(cv2.MORPH_RECT, (3 * PX_PER_MM, 1)))
    guides = cv2.bitwise_and(lines, cv2.bitwise_not(cv2.dilate(solid, np.ones((5, 5), np.uint8))))
    return bw, solid, guides


def _boxes(solid, guides):
    """답안 박스 [(x0, y0, x1, y1, [괘선 y…])] — 위에서 아래로."""
    import cv2
    import numpy as np
    H, W = solid.shape
    cs, _ = cv2.findContours(cv2.dilate(solid, np.ones((3, 3), np.uint8)),
                             cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    rects = []
    for c in cs:
        x, y, w, h = cv2.boundingRect(c)
        if w < 0.6 * W or h < 6 * PX_PER_MM or h > 0.9 * H:
            continue
        # 같은 테두리의 안쪽·바깥쪽 윤곽이 둘 다 잡힌다 — 거의 같은 사각형은 하나로
        if any(abs(x - a) < 15 and abs(y - b) < 15 and abs(x + w - c2) < 15 and abs(y + h - d) < 15
               for a, b, c2, d in rects):
            continue
        rects.append((x, y, x + w, y + h))
    out = []
    for x0, y0, x1, y1 in sorted(rects, key=lambda r: r[1]):
        sub = guides[y0 + 8:y1 - 8, x0 + 20:x1 - 20]
        if sub.size == 0:
            continue
        cover = (sub > 0).mean(1)
        rows = np.nonzero(cover > 0.35)[0]
        ys, grp = [], []
        for r in rows:
            if grp and r - grp[-1] > 3:
                ys.append(y0 + 8 + float(np.mean(grp)))
                grp = []
            grp.append(r)
        if grp:
            ys.append(y0 + 8 + float(np.mean(grp)))
        if ys:                          # 괘선이 없으면 발문의 지문 상자다
            out.append((x0, y0, x1, y1, ys))
    return out


def _band_ink(ink, x0, x1, ya, yb):
    """띠 하나의 잉크 요약. 잉크가 거의 없으면 None."""
    import numpy as np
    sub = ink[int(ya):int(yb), x0:x1]
    col = (sub > 0).sum(0)
    if col.sum() < 120:
        return None
    xs = np.nonzero(col)[0]
    a, b = int(xs[0]), int(xs[-1]) + 1
    prof = col[a:b]
    # 1.2mm 넘는 빈틈 — 낱말 사이를 가를 후보
    gaps, run = [], None
    for i, v in enumerate(prof):
        if v == 0 and run is None:
            run = i
        elif v != 0 and run is not None:
            if i - run >= 12:
                gaps.append([x0 + a + run, x0 + a + i])
            run = None
    cum = np.cumsum(prof).astype(np.float64)
    step = 8
    cum8 = [int(round(1000 * cum[min(i, len(cum) - 1)] / cum[-1])) for i in range(0, len(cum), step)]
    return {'x0': x0 + a, 'x1': x0 + b, 'gaps': gaps, 'cum8': cum8, 'mass': int(col.sum())}


def page_layout(flat_bgr, answers):
    """편 쪽 한 장의 배치. answers = [{'qid', 'number', 'text', 'box': [ymin,xmin,ymax,xmax] 0~1000 또는 None}]

    반환 {qid(str): {'number', 'box': [x0,y0,x1,y1], 'bands': [{'y0','y1','ink'|None}], 'text'}}
    """
    import cv2
    import numpy as np
    gray = cv2.cvtColor(flat_bgr, cv2.COLOR_BGR2GRAY)
    H, W = gray.shape
    bw, solid, guides = _masks(gray)
    boxes = _boxes(solid, guides)
    # 글씨 = 잉크에서 테두리·괘선을 지운 것. 점 같은 잡티는 버린다
    ink = cv2.bitwise_and(bw, cv2.bitwise_not(cv2.dilate(cv2.bitwise_or(solid, guides),
                                                          np.ones((5, 5), np.uint8))))
    n, lab, st, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    small = np.isin(lab, np.nonzero(st[:, cv2.CC_STAT_AREA] < 12)[0])
    ink[small] = 0

    # 답 ↔ 박스 짝짓기: 판독이 준 박스 위치와 가장 많이 겹치는 것, 없으면 차례대로
    used, pick = set(), {}

    def iou(a, b):
        ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
        iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
        inter = ix * iy
        u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
        return inter / u if u else 0

    for ans in answers:
        bx = ans.get('box') or []
        if len(bx) == 4:
            r = (bx[1] * W / 1000, bx[0] * H / 1000, bx[3] * W / 1000, bx[2] * H / 1000)
            best = max(((iou(r, b[:4]), i) for i, b in enumerate(boxes) if i not in used), default=(0, None))
            if best[1] is not None and best[0] > 0.3:
                pick[ans['qid']] = best[1]
                used.add(best[1])
    rest = [i for i in range(len(boxes)) if i not in used]
    for ans in sorted((a for a in answers if a['qid'] not in pick), key=lambda a: a['number']):
        if rest:
            pick[ans['qid']] = rest.pop(0)

    out = {}
    for ans in answers:
        if ans['qid'] not in pick:
            continue
        x0, y0, x1, y1, ys = boxes[pick[ans['qid']]]
        edges = [y0] + ys + [y1]
        bands = []
        for ya, yb in zip(edges, edges[1:]):
            # 글씨는 괘선 **위에** 앉으므로 띠의 아래쪽을 본다. 위쪽 35% 에는 윗줄의
            # 받침·꼬리가 내려와 있어, 그것까지 세면 빈 띠가 '쓴 줄'로 잡혀 판독문의
            # 줄과 띠의 짝이 한 칸씩 밀렸다.
            bands.append({'y0': round(ya), 'y1': round(yb),
                          'ink': _band_ink(ink, x0 + 10, x1 - 10, ya + 0.35 * (yb - ya), yb + 3)})
        # 다른 줄보다 잉크가 훨씬 적은 띠(꼬리 한두 획)는 빈 줄로 본다
        mass = [b['ink']['mass'] for b in bands if b['ink']]
        if mass:
            floor = 0.2 * float(np.median(mass))
            for b in bands:
                if b['ink'] and b['ink']['mass'] < floor:
                    b['ink'] = None
        out[str(ans['qid'])] = {'number': ans['number'], 'box': [x0, y0, x1, y1],
                                'bands': bands, 'text': ans.get('text', '')}
    return out


# ── 4. 구절 위치 ─────────────────────────────────────────────────────────────
def _word_groups(ink, nwords):
    """잉크를 낱말 수만큼 덩어리로 가른다. 큰 틈이 뚜렷하지 않으면 None."""
    gaps = sorted(ink['gaps'], key=lambda g: g[1] - g[0], reverse=True)
    if nwords <= 1:
        return [[ink['x0'], ink['x1']]]
    if len(gaps) < nwords - 1:
        return None
    k = nwords - 1
    wk = gaps[k - 1][1] - gaps[k - 1][0]
    nxt = gaps[k][1] - gaps[k][0] if len(gaps) > k else 0
    if wk < 18 or (nxt and wk < 1.4 * nxt):
        return None
    cut = sorted(gaps[:k])
    groups, a = [], ink['x0']
    for g in cut:
        groups.append([a, g[0]])
        a = g[1]
    groups.append([a, ink['x1']])
    return groups


def _x_at(ink, frac):
    """잉크 누적량이 frac(0~1)에 이르는 x."""
    cum = ink['cum8']
    t = frac * 1000
    for i, v in enumerate(cum):
        if v >= t:
            return ink['x0'] + i * 8
    return ink['x1']


def _span_in_line(line, s, e, ink):
    """판독문 한 줄의 글자 구간 [s, e) → 사진의 x 구간."""
    words = [(m.start(), m.end()) for m in re.finditer(r'\S+', line)]
    groups = _word_groups(ink, len(words)) if words else None
    if groups:
        def x(pos, end):
            for (ws, we), (gx0, gx1) in zip(words, groups):
                if ws <= pos <= we:
                    f = (pos - ws) / max(1, we - ws)
                    return gx0 + f * (gx1 - gx0)
            return groups[-1][1] if end else groups[0][0]
        return x(s, False), x(e, True)
    # 낱말로 못 가르면 공백을 뺀 글자 수를 잉크 양에 비례시킨다
    nonsp = [i for i, ch in enumerate(line) if not ch.isspace()]
    tot = max(1, len(nonsp))
    before_s = sum(1 for i in nonsp if i < s)
    before_e = sum(1 for i in nonsp if i < e)
    return _x_at(ink, before_s / tot), _x_at(ink, before_e / tot)


def _pairs(item):
    """판독문의 줄 ↔ 잉크가 있는 띠. 개수가 다르면 앞에서부터 짝짓고 남는 줄은 마지막 띠로."""
    lines = [l for l in (item.get('text') or '').replace('\r', '').split('\n') if l.strip()]
    inked = [b for b in item['bands'] if b['ink']]
    if not lines or not inked:
        return []
    if len(lines) > len(inked):
        # 줄 사이에 작게 끼워 쓴 글("의 결합" 같은 덧말)은 판독문에서는 한 줄인데
        # 사진에서는 띠를 채우지 못한다. 가장 짧은 줄부터 윗줄에 붙인다 — 끝줄끼리
        # 붙이면 그 뒤 줄이 모두 한 칸씩 밀린다.
        while len(lines) > len(inked):
            i = min(range(len(lines)), key=lambda j: len(lines[j].strip()))
            j = i - 1 if i > 0 else 1
            a, b = sorted((i, j))
            lines[a:b + 1] = [lines[a].rstrip() + ' ' + lines[b].strip()]
    elif len(lines) < len(inked):
        # 판독이 줄을 합쳤다(긴 줄이 두 띠로 넘어간 경우) — 줄을 띠에 나눠 싣는다
        return _spread(lines, inked)
    return list(zip(lines, inked))


def _spread(lines, inked):
    """줄 수 < 띠 수: 각 줄을 글자 수 비율로 연속된 띠에 나눠 싣는다."""
    total_ink = sum(b['ink']['x1'] - b['ink']['x0'] for b in inked)
    total_chars = sum(len(l) for l in lines)
    pairs, bi = [], 0
    for li, line in enumerate(lines):
        need = len(line) / max(1, total_chars) * total_ink
        start = 0
        while bi < len(inked):
            b = inked[bi]
            w = b['ink']['x1'] - b['ink']['x0']
            take = len(line) - start if li == len(lines) - 1 and bi == len(inked) - 1 \
                else min(len(line) - start, max(1, round(len(line) * min(1, w / max(1, need)))))
            pairs.append((line[start:start + take], b))
            start += take
            bi += 1
            need -= w
            if start >= len(line) or need <= 0:
                break
    return pairs


def _fuzzy_find(norm, q):
    """norm 에서 q 와 가장 비슷한 구간 (시작, 길이). 비슷한 것이 없으면 (-1, 0)."""
    from difflib import SequenceMatcher
    best = (0.0, -1, 0)
    for n in {len(q), max(1, round(len(q) * 0.8)), round(len(q) * 1.2)}:
        for k in range(0, max(1, len(norm) - n + 1)):
            r = SequenceMatcher(None, norm[k:k + n], q, autojunk=False).ratio()
            if r > best[0]:
                best = (r, k, n)
    return (best[1], best[2]) if best[0] >= 0.6 else (-1, 0)


def _norm_map(text):
    keep = [(i, ch) for i, ch in enumerate(text) if not ch.isspace()]
    return ''.join(ch for _, ch in keep), [i for i, _ in keep]


def locate(item, quote):
    """구절 → [[x0, y0, x1, y1], …] (줄마다 하나). 못 찾으면 []."""
    pairs = _pairs(item)
    if not pairs or not quote:
        return []
    full = '\n'.join(l for l, _ in pairs)
    norm, idx = _norm_map(full)
    q, _ = _norm_map(quote)
    if not q:
        return []
    k, n = norm.find(q), len(q)
    if k < 0:
        # 회원이 판독문을 고친 뒤 채점하면 구절이 판독문과 조금 다르다. 가장 비슷한
        # 구간을 찾되, 많이 달라졌으면 자리를 짐작하지 않는다.
        k, n = _fuzzy_find(norm, q)
        if k < 0:
            return []
    s, e = idx[k], idx[k + n - 1] + 1
    rects, off = [], 0
    for line, band in pairs:
        ls, le = off, off + len(line)
        a, b = max(s, ls), min(e, le)
        if a < b:
            x0, x1 = _span_in_line(line, a - ls, b - ls, band['ink'])
            rects.append([round(x0), band['y0'], round(max(x1, x0 + 20)), band['y1']])
        off = le + 1
    return rects


# ── 결과 화면용 ─────────────────────────────────────────────────────────────
def ink_grid(flat_bgr):
    """쪽의 1mm 칸마다 잉크가 있는지(210×297) — packbits 를 base64 로.

    결과 화면이 첨삭 글을 **빈 자리에** 적을 때 쓴다. 인쇄 글·테두리·손글씨는 잉크로
    치고, 답안 박스의 점선 괘선은 뺀다(괘선 위에 글을 쓰는 것은 자연스럽다).
    """
    import base64
    import cv2
    import numpy as np
    gray = cv2.cvtColor(flat_bgr, cv2.COLOR_BGR2GRAY)
    bw, solid, guides = _masks(gray)
    ink = cv2.bitwise_and(bw, cv2.bitwise_not(cv2.dilate(guides, np.ones((5, 5), np.uint8))))
    n, lab, st, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    ink[np.isin(lab, np.nonzero(st[:, cv2.CC_STAT_AREA] < 12)[0])] = 0
    gw, gh = int(PAGE_MM_W), int(PAGE_MM_H)
    cells = cv2.resize(ink, (gw, gh), interpolation=cv2.INTER_AREA)
    occ = (cells > 6).astype(np.uint8)
    return base64.b64encode(np.packbits(occ.ravel()).tobytes()).decode()


PAGE_MM_W, PAGE_MM_H = 210, 297


def _grid_of(up):
    """업로드의 잉크 칸 — 없으면 계산해 flat_info 에 저장한다(이 기능 전에 판독한 쪽)."""
    info = up.flat_info or {}
    if info.get('grid'):
        return info['grid']
    import cv2
    import numpy as np
    img = cv2.imdecode(np.fromfile(up.flat_image.path, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return ''
    info = dict(info)
    info['grid'] = ink_grid(img)
    up.flat_info = info
    up.save(update_fields=['flat_info'])
    return info['grid']


def build_overlay(session):
    """세션의 편 사진마다 첨삭 재료 — 결과 화면이 빈 자리를 찾아 SVG 로 그린다."""
    atts = {a.question_id: a for a in session.attempts.select_related('question')}
    pages, drawn_score = [], set()
    for up in session.uploads.filter(transcribed=True).order_by('page_no'):
        layout = (up.flat_info or {}).get('layout')
        if not up.flat_image or not layout:
            continue
        answers = []
        for qid, item in sorted(layout.items(), key=lambda kv: kv[1]['box'][1]):
            att = atts.get(int(qid))
            if not att:
                continue
            fb = att.feedback or {}
            marks, unplaced = [], []
            for m in fb.get('marks') or []:
                rects = locate(item, m.get('quote', ''))
                if rects:
                    marks.append({'kind': m.get('kind'), 'note': m.get('note', ''), 'rects': rects})
                elif m.get('note'):
                    unplaced.append({'kind': m.get('kind'), 'note': m.get('note', '')})
            inked = [b for b in item['bands'] if b['ink']]
            first = int(qid) not in drawn_score
            drawn_score.add(int(qid))
            answers.append({
                'number': item['number'], 'box': item['box'], 'marks': marks,
                'unplaced': unplaced,
                'last_ink': [inked[-1]['ink']['x1'], inked[-1]['y1']] if inked else None,
                'missing': (fb.get('missing') or []) if first else [],
                'summary': (fb.get('summary') or '') if first else '',
                'score': att.score if first else None,
                'points': att.question.points,
                'graded': bool(fb),
            })
        pages.append({'page_no': up.page_no, 'url': up.flat_image.url,
                      'w': PAGE_MM_W * PX_PER_MM, 'h': PAGE_MM_H * PX_PER_MM,
                      'grid': _grid_of(up), 'answers': answers})
    return pages
