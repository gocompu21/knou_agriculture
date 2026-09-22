# -*- coding: utf-8 -*-
"""401 평면 렌더 위에 도면을 빨갛게 얹는다 — 어긋난 곳을 눈으로 찾는다.

평면 렌더는 직교 카메라라 축척이 딱 떨어진다:
    px/m = RES_x / ortho_scale,  부지 한가운데(45, 30)가 화면 한가운데.
도면(SVG)은 같은 px/m 로 그려 부지 네 귀퉁이를 맞춘다.
"""
import io
import os
import re
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
W_SITE, D_SITE = 90.0, 60.0
ORTHO = 94.0                       # make401.py 의 TOP_VIEW ortho_scale


def svg_to_png(svg_path, out_png, ppm):
    """SVG 를 부지 범위(0 0 90 60)만 잘라 ppm(px/m) 으로 그린다 — Playwright."""
    from playwright.sync_api import sync_playwright
    svg = io.open(svg_path, encoding='utf-8').read()
    svg = re.sub(r'viewBox="[^"]*"', 'viewBox="0 0 90 60"', svg, count=1)
    svg = re.sub(r'style="[^"]*"', f'style="width:{int(W_SITE*ppm)}px;height:{int(D_SITE*ppm)}px"', svg, count=1)
    html = ('<!doctype html><meta charset="utf-8">'
            '<style>html,body{margin:0;padding:0;background:#fff}</style>' + svg)
    p = os.path.join(HERE, '_ov.html')
    io.open(p, 'w', encoding='utf-8').write(html)
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel='chrome')
        pg = b.new_page(viewport={'width': int(W_SITE * ppm), 'height': int(D_SITE * ppm)},
                        device_scale_factor=1)
        pg.goto('file:///' + p.replace('\\', '/'))
        pg.wait_for_timeout(700)
        pg.screenshot(path=out_png)
        b.close()


def main():
    render = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 't03.png')
    im = cv2.imread(render)
    h, w = im.shape[:2]
    ppm = w / ORTHO
    # 부지 (0,0) 의 화면 좌표
    x0 = w / 2 + (0 - W_SITE / 2) * ppm
    y0 = h / 2 - (D_SITE / 2 - 0) * ppm
    print(f'{ppm:.3f} px/m · 부지 좌상단 ({x0:.1f}, {y0:.1f})')

    dw = os.path.join(HERE, '_dw.png')
    svg_to_png(os.path.join(HERE, 'grid401.svg'), dw, ppm)
    d = cv2.imread(dw)
    print('도면', d.shape, '→ 부지', int(W_SITE * ppm), 'x', int(D_SITE * ppm))

    ov = im.copy()
    gh, gw = d.shape[:2]
    ys, xs = int(round(y0)), int(round(x0))
    sub = ov[ys:ys + gh, xs:xs + gw]
    g = cv2.cvtColor(d, cv2.COLOR_BGR2GRAY)[:sub.shape[0], :sub.shape[1]]
    mask = g < 150                                  # 도면의 진한 선만
    sub[mask] = (0, 0, 255)
    cv2.imwrite(os.path.join(HERE, 'overlay.png'), ov)
    cv2.imwrite(os.path.join(HERE, 'overlay_view.png'),
                cv2.resize(ov, (1250, int(1250 * h / w)), interpolation=cv2.INTER_AREA))
    print('overlay.png 저장 · 선 화소', int(mask.sum()))


if __name__ == '__main__':
    main()
