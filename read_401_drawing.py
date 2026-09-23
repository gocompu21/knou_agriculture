# -*- coding: utf-8 -*-
"""성운 도면을 **부지 좌표(m)** 로 잘라 본다.

경계선을 화소로 재어 잡은 사상 (두 도면 모두 12.89 px/m):
    배식설계도 3_planting.jpg : imgx = 538 + 12.89*X , imgy = 279  + 12.89*Y
    기본설계도 2_plan.jpg     : imgx = 400 + 12.89*X , imgy = 468.5+ 12.89*Y
"""
import io, os, sys
import cv2, numpy as np

ROOT = 'C:/Users/gocom/Documents/Antigravity/Django_BaseCamp/knou_agriculture/.claude/worktrees/plant-protection-engineer-exam-279801/_ls_drawing_refs/401_성운/'
PPM = 12.89
SHEET = {'plan': ('2_plan.jpg', 400.0, 468.5), 'planting': ('3_planting.jpg', 538.0, 279.0)}


def load(which):
    f, ox, oy = SHEET[which]
    im = cv2.imdecode(np.fromfile(ROOT + f, dtype='uint8'), 1)
    return im, ox, oy


def crop(which, a, b, c, d, out, W=1300):
    im, ox, oy = load(which)
    s = im[int(oy + c * PPM):int(oy + d * PPM), int(ox + a * PPM):int(ox + b * PPM)]
    s = cv2.resize(s, (W, int(W * s.shape[0] / s.shape[1])), interpolation=cv2.INTER_CUBIC)
    ok, bb = cv2.imencode('.png', s)
    io.open(out, 'wb').write(bb.tobytes())
    print(out, s.shape, f'{W/((b-a)*PPM):.2f}x')


if __name__ == '__main__':
    which, a, b, c, d, out = sys.argv[1], *[float(v) for v in sys.argv[2:6]], sys.argv[6]
    crop(which, a, b, c, d, out)
