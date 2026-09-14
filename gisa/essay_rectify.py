# -*- coding: utf-8 -*-
"""시험지 사진을 A4 한 쪽으로 곧게 편다.

휴대폰으로 찍은 시험지는 기울고(원근), 종이가 휜다. 판독 정확도와 나중에
사진 위에 첨삭을 겹쳐 그릴 때의 위치가 모두 여기에 달려 있다.

세 단계로 시도한다.

1. **ArUco 마커** — 인쇄 시험지 네 모서리에 번호가 박힌 마커(0 왼위, 1 오른위,
   2 오른아래, 3 왼아래)를 찍어 둔다. 무늬를 해독하므로 글씨·얼룩을 마커로
   오인하지 않고, 번호로 방향을 알며, 두 개만 보여도 편다(마커 하나가 모서리
   네 점을 준다).
2. **종이 가장자리** — 마커가 없는 옛 시험지나 문서 스캔 앱으로 잘라 온 사진.
   밝고 색이 옅은 영역을 종이로 보고 그 네 꼭짓점을 A4 로 편다.
3. 둘 다 안 되면 원본을 그대로 쓴다(EXIF 회전만 바로잡는다).

1·2 로 편 뒤에는 **휜 종이를 한 번 더 맞춘다**(`_refine`). 네 점 보정은 평면만
펴므로 종이가 뜬 가운데서 몇 mm 가 남는다. 답안 박스의 굵은 테두리는 곧은
선이어야 하므로, 테두리가 휜 만큼을 변위장으로 만들어 되돌린다.

OpenCV 는 이 모듈 안에서만 불러온다 — 시험지 인쇄 화면은 마커 무늬만 쓰므로
OpenCV 없이 돌아야 한다.
"""
import io

# ── 인쇄 규격 (essay_sheet.html 의 @page·마커 CSS 와 짝이 맞아야 한다) ──────
PAGE_MM = (210.0, 297.0)
MARGIN_TOP_MM = 10.0
MARGIN_SIDE_MM = 10.0
MARGIN_BOTTOM_MM = 12.0
MARKER_MM = 9.0
PX_PER_MM = 10              # 편 쪽의 해상도 → 2100 × 2970

# cv2.aruco DICT_4X4_50 의 0~3번. 6×6 칸(바깥 1칸은 검은 테), '1' = 흰 칸.
# 시험지 화면이 OpenCV 없이 그리도록 무늬를 박아 둔다.
MARKER_BITS = {
    0: ['000000', '010110', '001010', '000110', '000100', '000000'],
    1: ['000000', '000000', '011110', '010010', '010100', '000000'],
    2: ['000000', '000110', '000110', '000100', '011010', '000000'],
    3: ['000000', '010010', '010010', '001000', '001100', '000000'],
}
MARKER_POS = {0: 'tl', 1: 'tr', 2: 'br', 3: 'bl'}

METHOD_LABELS = {'marker': '마커로 폄', 'edge': '가장자리로 폄',
                 'none': '펴지 못함'}


def marker_svgs():
    """시험지에 찍을 마커 SVG 4개 — [{'id', 'pos', 'svg'}]."""
    out = []
    for mid, rows in MARKER_BITS.items():
        rects = []
        for y, row in enumerate(rows):
            x = 0
            while x < 6:
                if row[x] == '0':
                    w = 1
                    while x + w < 6 and row[x + w] == '0':
                        w += 1
                    rects.append(f'<rect x="{x}" y="{y}" width="{w}" height="1"/>')
                    x += w
                else:
                    x += 1
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 6 6" '
               'shape-rendering="crispEdges" fill="#000">' + ''.join(rects) + '</svg>')
        out.append({'id': mid, 'pos': MARKER_POS[mid], 'svg': svg})
    return out


def _marker_corners_mm(mid):
    """마커 mid 의 네 꼭짓점(왼위·오른위·오른아래·왼아래) 종이 좌표(mm)."""
    w, h = PAGE_MM
    s = MARKER_MM
    x0 = MARGIN_SIDE_MM if MARKER_POS[mid] in ('tl', 'bl') else w - MARGIN_SIDE_MM - s
    y0 = MARGIN_TOP_MM if MARKER_POS[mid] in ('tl', 'tr') else h - MARGIN_BOTTOM_MM - s
    return [(x0, y0), (x0 + s, y0), (x0 + s, y0 + s), (x0, y0 + s)]


def _load(data):
    """바이트 → EXIF 회전을 바로잡은 BGR 배열."""
    import numpy as np
    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert('RGB')
    return np.asarray(im)[:, :, ::-1].copy()


def _out_size():
    return int(PAGE_MM[0] * PX_PER_MM), int(PAGE_MM[1] * PX_PER_MM)


# ── 1. ArUco 마커 ────────────────────────────────────────────────────────────
def _by_markers(img):
    import cv2
    import numpy as np

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    scale = min(1.0, 2400.0 / max(gray.shape))
    work = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) \
        if scale < 1 else gray
    params = cv2.aruco.DetectorParameters()
    params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
    det = cv2.aruco.ArucoDetector(
        cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50), params)
    corners, ids, _ = det.detectMarkers(work)
    if ids is None:
        return None, 0
    src, dst, seen = [], [], set()
    for c, mid in zip(corners, ids.ravel()):
        mid = int(mid)
        if mid not in MARKER_BITS or mid in seen:
            continue
        seen.add(mid)
        src.extend((c.reshape(4, 2) / scale).tolist())
        dst.extend([(x * PX_PER_MM, y * PX_PER_MM) for x, y in _marker_corners_mm(mid)])
    # 마커 하나로도 호모그래피는 나오지만, 9mm 짜리 네 점으로 쪽 전체를
    # 늘이면 반대편 끝이 크게 틀어진다. 둘 이상일 때만 쓴다.
    if len(seen) < 2:
        return None, len(seen)
    H, _ = cv2.findHomography(np.float32(src), np.float32(dst), cv2.RANSAC, 8.0)
    if H is None:
        return None, len(seen)
    page = cv2.warpPerspective(img, H, _out_size(), flags=cv2.INTER_AREA,
                               borderValue=(255, 255, 255))
    return page, len(seen)


# ── 2. 종이 가장자리 ─────────────────────────────────────────────────────────
def _by_edges(img):
    import cv2
    import numpy as np

    H0, W0 = img.shape[:2]
    s = 1000.0 / max(H0, W0)
    sm = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(sm, cv2.COLOR_BGR2HSV)
    # 종이 = 밝고 채도가 낮다. 나무 책상·천·손은 채도가 있어 떨어져 나간다.
    mask = ((hsv[:, :, 2] > 150) & (hsv[:, :, 1] < 45)).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    # 책상의 밝은 얼룩이 종이 가장자리에 가늘게 이어 붙는 일이 있다(실제 사진
    # 8장 중 1장). 열기로 그 목을 끊는다.
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((15, 15), np.uint8))
    cs, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cs:
        return None
    c = max(cs, key=cv2.contourArea)
    area = cv2.contourArea(c)
    if area < 0.2 * sm.shape[0] * sm.shape[1]:
        return None
    # 꼭짓점을 근사 다각형이 아니라 볼록껍질의 극점으로 잡는다 — 모서리 그림자나
    # 붙은 얼룩으로 다각형이 5·6각형이 되어도 네 꼭짓점은 그대로 뽑힌다.
    p = cv2.convexHull(c).reshape(-1, 2).astype(np.float32)
    ssum, diff = p.sum(1), np.diff(p, axis=1).ravel()
    quad = np.float32([p[ssum.argmin()], p[diff.argmin()],
                       p[ssum.argmax()], p[diff.argmax()]])
    # 네 꼭짓점이 겹치거나, 사각형이 종이 영역과 크게 다르면 종이가 아니다
    if len({tuple(map(int, q)) for q in quad}) < 4:
        return None
    if not 0.85 < cv2.contourArea(quad) / area < 1.15:
        return None
    quad /= s
    Wd, Hd = _out_size()
    M = cv2.getPerspectiveTransform(quad, np.float32([[0, 0], [Wd, 0], [Wd, Hd], [0, Hd]]))
    return cv2.warpPerspective(img, M, (Wd, Hd), flags=cv2.INTER_AREA,
                               borderValue=(255, 255, 255))


# ── 휜 종이 맞추기 ───────────────────────────────────────────────────────────
def _smooth_outliers(pts, tol=1.0 * PX_PER_MM):
    """선 표본 가운데 이웃(앞뒤 2개씩)의 중앙값에서 1mm 넘게 튄 것을 버린다.

    글씨가 테두리에 닿으면 그 자리의 표본이 획 쪽으로 끌려간다. 종이의 휨은
    3mm 간격에서 1mm 씩 꺾이지 않으므로 튄 표본은 글씨로 본다.
    """
    import numpy as np
    if len(pts) < 5:
        return pts
    v = np.float32([p[1] for p in pts])
    keep = []
    for i, p in enumerate(pts):
        lo, hi = max(0, i - 2), min(len(pts), i + 3)
        if abs(v[i] - np.median(v[lo:hi])) <= tol:
            keep.append(p)
    return keep


def _line_samples(page):
    """굵은 테두리의 가로선·세로선에서 표본점을 뽑는다.

    반환: (가로 표본 [(x, y관측, y목표)], 세로 표본 [(y, x관측, x목표)])
    가로선은 제 중앙값 높이로, 세로선은 같은 x 무리(쪽 왼쪽 테두리들, 오른쪽
    테두리들)의 중앙값으로 곧게 선다.
    """
    import cv2
    import numpy as np

    gray = cv2.cvtColor(page, cv2.COLOR_BGR2GRAY)
    bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                               cv2.THRESH_BINARY_INV, 31, 15)
    H, W = bw.shape
    # 3mm — 점선 괘선의 파선 조각(1mm 안팎)은 여기서 떨어진다. 더 길게 잡으면
    # 휜 종이에서 기울기가 급한 구간의 테두리가 끊겨 표본이 비는데(6mm 로 해 보니
    # 휨 4mm 에서 물결이 그대로 남았다), 그 자리가 가장 고쳐야 할 곳이다.
    # 글씨의 가로획은 이 길이를 넘기도 하지만 아래 '쪽 폭의 35%' 조건에서 떨어진다.
    L = 3 * PX_PER_MM

    hs = []
    # 가로선은 답안 박스 안의 점선 괘선까지 쓴다 — 글씨가 바로 그 위에 있어,
    # 테두리만 쓰면 박스 가운데의 휨이 남는다. 파선 틈을 가로로 이어 붙인 뒤 뽑는다.
    closed = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1)))
    hmask = cv2.morphologyEx(closed, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (L, 1)))
    n, lab, st, _ = cv2.connectedComponentsWithStats(hmask, connectivity=8)
    for i in range(1, n):
        x, y, w, h, _a = st[i]
        # 높이 한도는 휜 선의 출렁임까지 받아야 한다(4mm 로 두니 휜 테두리가 통째로 빠졌다)
        if w < 0.35 * W or h > 12 * PX_PER_MM:
            continue
        pts = []
        for xx in range(x + 10, x + w - 10, 3 * PX_PER_MM):
            ys = np.nonzero(lab[y:y + h, xx] == i)[0]
            if len(ys):
                pts.append((xx, y + float(ys.mean())))
        pts = _smooth_outliers(pts)
        if len(pts) < 5:
            continue
        target = float(np.median([p[1] for p in pts]))
        hs.extend((px, py, target) for px, py in pts)

    vcomps = []
    vmask = cv2.morphologyEx(bw, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, L)))
    n, lab, st, _ = cv2.connectedComponentsWithStats(vmask, connectivity=8)
    for i in range(1, n):
        x, y, w, h, _a = st[i]
        if h < 15 * PX_PER_MM or w > 12 * PX_PER_MM:
            continue
        pts = []
        for yy in range(y + 10, y + h - 10, 3 * PX_PER_MM):
            xs = np.nonzero(lab[yy, x:x + w] == i)[0]
            if len(xs):
                pts.append((yy, x + float(xs.mean())))
        pts = _smooth_outliers(pts)
        if len(pts) >= 4:
            vcomps.append(pts)
    # x 가 가까운(4mm 안) 세로선끼리 한 무리 — 답안 박스들의 왼쪽 테두리는 모두
    # 같은 x 에 인쇄된다
    vs = []
    vcomps.sort(key=lambda pts: np.median([p[1] for p in pts]))
    group, last = [], None
    for pts in vcomps + [None]:
        mx = None if pts is None else float(np.median([p[1] for p in pts]))
        if pts is None or (last is not None and mx - last > 4 * PX_PER_MM):
            if group:
                target = float(np.median([p[1] for g in group for p in g]))
                vs.extend((py, px, target) for g in group for py, px in g)
            group = []
        if pts is not None:
            group.append(pts)
            last = mx
    return hs, vs


def _field(points, values, shape, step, sigma):
    """흩어진 변위값을 쪽 전체의 매끄러운 변위장으로 편다(가우스 가중 평균).

    표본에서 멀어지면 0 으로 돌아간다(w0) — 테두리가 없는 여백은 건드리지 않는다.
    """
    import cv2
    import numpy as np

    H, W = shape
    gy, gx = np.mgrid[0:H + step:step, 0:W + step:step].astype(np.float32)
    grid = np.stack([gx.ravel(), gy.ravel()], 1)
    P = np.float32(points)
    V = np.float32(values)
    acc = np.zeros(len(grid), np.float32)
    wsum = np.zeros(len(grid), np.float32)
    for a in range(0, len(grid), 2000):
        g = grid[a:a + 2000]
        d2 = ((g[:, None, :] - P[None, :, :]) ** 2).sum(-1)
        w = np.exp(-d2 / (2 * sigma * sigma))
        acc[a:a + 2000] = (w * V[None, :]).sum(1)
        wsum[a:a + 2000] = w.sum(1)
    f = (acc / (wsum + 0.05)).reshape(gy.shape)
    return cv2.resize(f, (W, H), interpolation=cv2.INTER_CUBIC)[:H, :W]


def _refine(page):
    """테두리가 곧게 서도록 쪽을 다시 맞춘다. 반환: (쪽, 보정량 정보)."""
    import cv2
    import numpy as np

    hs, vs = _line_samples(page)
    H, W = page.shape[:2]
    lim = 5 * PX_PER_MM        # 5mm 넘게 어긋난 표본은 잘못 잡은 선으로 본다
    hs = [p for p in hs if abs(p[1] - p[2]) <= lim]
    vs = [p for p in vs if abs(p[1] - p[2]) <= lim]
    info = {'h_points': len(hs), 'v_points': len(vs)}
    if len(hs) < 10:
        info['refined'] = False
        return page, info
    # 편 결과의 픽셀(목표 자리)이 원래 사진의 어디서 오는가 = 관측 − 목표
    dy = _field([(x, t) for x, _o, t in hs], [o - t for _x, o, t in hs],
                (H, W), 3 * PX_PER_MM, 12 * PX_PER_MM)
    if len(vs) >= 6:
        dx = _field([(t, y) for y, _o, t in vs], [o - t for _y, o, t in vs],
                    (H, W), 3 * PX_PER_MM, 12 * PX_PER_MM)
    else:
        dx = np.zeros((H, W), np.float32)
    info['max_shift_mm'] = round(float(max(np.abs(dy).max(), np.abs(dx).max())) / PX_PER_MM, 2)
    gy, gx = np.mgrid[0:H, 0:W].astype(np.float32)
    out = cv2.remap(page, gx + dx, gy + dy, cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
    info['refined'] = True
    return out, info


def straightness(page):
    """테두리 가로선이 곧은 정도 — 선마다 (최대 − 최소 높이)의 중앙값(mm). 점검용."""
    import numpy as np
    hs, _vs = _line_samples(page)
    by = {}
    for x, y, t in hs:
        by.setdefault(t, []).append(y)
    spans = [max(v) - min(v) for v in by.values() if len(v) >= 5]
    return round(float(np.median(spans)) / PX_PER_MM, 2) if spans else None


def rectify_bytes(data):
    """사진 바이트 → (편 JPEG 바이트, 방법, 정보). OpenCV 가 없으면 방법 'none'."""
    try:
        import cv2
    except ImportError:
        return None, 'none', {'error': 'opencv 미설치'}

    img = _load(data)
    info = {'src': [int(img.shape[1]), int(img.shape[0])]}
    page, n = _by_markers(img)
    info['markers'] = n
    method = 'marker'
    if page is None:
        page = _by_edges(img)
        method = 'edge'
    if page is None:
        method = 'none'
        page = img
    else:
        page, rinfo = _refine(page)
        info.update(rinfo)
    ok, buf = cv2.imencode('.jpg', page, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return (buf.tobytes() if ok else None), method, info
