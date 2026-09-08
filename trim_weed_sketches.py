"""손그림 이미지의 바깥 여백을 다듬는다.

추출 영역이 슬라이드 좌표라 가장자리에 연녹색 판이 남는다. 바깥에서 안으로
훑으며 '거의 전부 연녹색인 줄'을 걷어낸 뒤, 종이 영역에 맞춰 다시 자른다.
원본은 k_src/ 에 있으므로 반복 실행해도 조금씩 깎이지 않는다.

  python trim_sketch.py            # 얼마나 잘리는지만
  python trim_sketch.py --write    # 저장
"""
import sys, os, json
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
DIR = os.path.join('media', 'weeds', 's51')
SRC = os.path.join(DIR, 'k_src')
PAD = 8


def greenish(a):
    """슬라이드 연녹색 판인 화소."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return (r > 160) & (r < 248) & (g > 190) & (g < 253) & (b > 110) & (b < 230) & (g > r) & (r > b)


def strip_panel(a, thr=0.5):
    """바깥에서 안으로, 연녹색이 thr 넘는 줄을 걷어낸다.

    연녹이 몇 줄 건너 다시 나오는 경우가 있어 흰 줄 몇 개는 건너뛰고 이어 본다.
    """
    gr = greenish(a)
    h, w = gr.shape
    x0, x1, y0, y1 = 0, w, 0, h

    def scan(get, lo, hi, step):
        """lo 에서 hi 방향으로, 연녹 줄을 지나며 마지막 연녹 위치+1 을 돌려준다."""
        pos, last = lo, lo
        while (pos - hi) * step < 0:
            if get(pos) > thr:
                last = pos + (1 if step > 0 else 0)
            elif abs(pos - last) > 6:     # 흰 줄이 6개 넘게 이어지면 그만
                break
            pos += step
        return last

    x0 = scan(lambda x: gr[:, x].mean(), 0, int(w * 0.35), 1)
    x1 = scan(lambda x: gr[:, x - 1].mean(), w, int(w * 0.65), -1)
    y0 = scan(lambda y: gr[y, x0:x1].mean(), 0, int(h * 0.35), 1)
    y1 = scan(lambda y: gr[y - 1, x0:x1].mean(), h, int(h * 0.65), -1)
    return x0, y0, x1, y1


def paper_box(a):
    """종이(밝고 채도 낮은 영역)의 사각형. 못 찾으면 None."""
    mx, mn = a.max(axis=2), a.min(axis=2)
    paper = (mx > 165) & (mx - mn < 42)
    if paper.mean() < 0.15:
        return None
    ys = np.where(paper.mean(axis=1) > 0.55)[0]
    xs = np.where(paper.mean(axis=0) > 0.55)[0]
    if len(ys) < 8 or len(xs) < 8:
        return None
    return xs[0], ys[0], xs[-1] + 1, ys[-1] + 1


def main():
    write = '--write' in sys.argv
    cards = json.load(open('_weed_cards.json', encoding='utf-8'))
    done, skip = 0, []
    for c in cards:
        src = os.path.join(SRC, 'k%03d.jpg' % c['card_no'])
        if not os.path.exists(src):
            continue
        im = Image.open(src).convert('RGB')
        a = np.asarray(im).astype(int)

        x0, y0, x1, y1 = strip_panel(a)          # 1) 연녹 판 제거
        im = im.crop((x0, y0, x1, y1))
        a = np.asarray(im).astype(int)

        box = paper_box(a)                        # 2) 종이 영역에 맞추기
        if box and (box[2] - box[0]) > im.width * 0.4 and (box[3] - box[1]) > im.height * 0.4:
            im = im.crop(box)
        else:
            skip.append(c['name'])

        a = np.asarray(im).astype(int)            # 3) 그래도 남은 판 줄 걷어내기
        x0, y0, x1, y1 = strip_panel(a)
        im = im.crop((x0, y0, x1, y1))

        out = Image.new('RGB', (im.width + PAD * 2, im.height + PAD * 2), 'white')
        out.paste(im, (PAD, PAD))
        done += 1
        if write:
            out.save(os.path.join(DIR, 'k%03d.jpg' % c['card_no']), quality=90, optimize=True)
    print('다듬음', done, '장 | 종이 판정 실패', len(skip), skip)


main()
