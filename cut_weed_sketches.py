"""답 슬라이드에서 손그림 스케치만 잘라낸다.

스케치는 PDF 에 별도 이미지 객체로 들어 있다. 슬라이드 아래쪽 오른편에 놓이며,
같은 영역에 설명 텍스트 상자가 함께 잡히는 카드는 더 아래에 있는 것이 스케치다.

  python cut_sketch.py            # 좌표만 훑어 보기
  python cut_sketch.py --write    # media/weeds/s51/k###.jpg 로 저장
"""
import fitz, sys, os, json, io
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
PDF = r"N:\개인\방송대\4-2. 잡초방제학(영상)\02. 잡초방제학 카드(방송대).pdf"
OUT = os.path.join('media', 'weeds', 's51')
PAD = 6


def sketch_rect(page):
    """스케치 이미지 객체의 사각형. 없으면 None."""
    W, H = page.rect.width, page.rect.height
    cand = []
    for img in page.get_images(full=True):
        for r in page.get_image_rects(img[0]):
            if (r.width * r.height) / (W * H) > 0.9:      # 슬라이드 배경
                continue
            if r.y0 / H * 100 > 45 and r.x1 / W * 100 > 60:
                cand.append(r)
    if not cand:
        return None
    return max(cand, key=lambda r: r.y0)                  # 가장 아래가 스케치


def main():
    write = '--write' in sys.argv
    cards = json.load(open('_weed_cards.json', encoding='utf-8'))
    d = fitz.open(PDF)
    got, miss = 0, []
    for c in cards:
        p = d[c['a_page'] - 1]
        r = sketch_rect(p)
        if r is None:
            miss.append(c['name'])
            continue
        got += 1
        if not write:
            continue
        # 스케치 영역만 300dpi 로 렌더 (원본 객체는 회전·잘림이 있을 수 있어 화면 그대로가 안전)
        clip = fitz.Rect(max(r.x0 - 2, 0), max(r.y0 - 2, 0),
                         min(r.x1 + 2, p.rect.width), min(r.y1 + 2, p.rect.height))
        pix = p.get_pixmap(dpi=300, clip=clip)
        im = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
        out = Image.new('RGB', (im.width + PAD * 2, im.height + PAD * 2), 'white')
        out.paste(im, (PAD, PAD))
        if out.width > 700:
            out = out.resize((700, round(out.height * 700 / out.width)), Image.LANCZOS)
        name = 'k%03d.jpg' % c['card_no']
        out.save(os.path.join(OUT, name), quality=90, optimize=True)
    print('스케치', got, '장 | 없는 카드', len(miss), miss)


main()
