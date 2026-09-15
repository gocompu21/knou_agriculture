# -*- coding: utf-8 -*-
"""조경 실기 학습자료 「필답 요약(빈칸 암기)」을 넣는다.

원본은 수험생이 한글로 만든 12쪽 요약본(■ 필답 요약_241031.pdf)이다. 빈칸 문장
아래 점선 뒤에 답을 몰아 적은 꼴이라, 답을 빈칸 자리에 `⟦답⟧` 로 되돌려 넣었다.
화면(essay_note)은 `⟦답⟧` 을 누르면 드러나는 빈칸으로 그린다.

- 사진 114장(병해 20·꽃 46·열매 34·단풍 13·참나무 잎 1)은 PDF 에 들어 있던 이미지를
  그대로 뽑아 `media/gisa/essay_notes/ls_summary/` 에 두었다. 이름표는 사진 아래 글자에서
  읽었다(`_ls_summary_photos.json`). 본문의 `[[사진:키]]` 가 그 묶음의 격자로 바뀐다.
  **media 는 git 밖이다** — 서버에는 따로 올린다
- 원문에서 분명한 오기는 고쳤다: 모래 입경(0.005 → 0.05mm), 벽돌 매수 식(1 ÷ 줄눈 포함
  한 장 넓이), 교호수준측량 식, "소나무 주요 해충 3가지" → 우리나라 3대 산림해충,
  "시설물 면적 비율이 가장 높은 공원" → 비율 상한이 가장 낮은 공원(소공원·묘지공원 20%)

  python load_ls_summary.py            # 검사만
  python load_ls_summary.py --apply    # 조경기사·조경산업기사 두 급수에 넣는다
"""
import io
import json
import os
import re
import sys

import django

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings  # noqa: E402
from django.utils.html import escape  # noqa: E402

from gisa.models import Certification, GisaEssayNote  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '_ls_summary.md')
PHOTOS = os.path.join(HERE, '_ls_summary_photos.json')
MEDIA_DIR = 'gisa/essay_notes/ls_summary'
SLUG, TITLE, ORDER = 'summary', '필답 요약(빈칸 암기)', 2


def photo_grid(key, photos):
    items = photos[key]
    wide = ' wide' if len(items) == 1 else ''
    figs = []
    for it in items:
        src = f'{settings.MEDIA_URL}{MEDIA_DIR}/{it["file"]}'
        cap = escape(it['cap'])
        figs.append(f'<figure><img src="{src}" alt="{cap}" loading="lazy">'
                    + (f'<figcaption>{cap}</figcaption>' if cap else '') + '</figure>')
    return f'<div class="nt-photos{wide}">' + ''.join(figs) + '</div>'


def main():
    apply_ = '--apply' in sys.argv
    text = io.open(SRC, encoding='utf-8').read()
    photos = json.load(io.open(PHOTOS, encoding='utf-8'))

    errors = []
    used = set(re.findall(r'\[\[사진:([a-z_]+)\]\]', text))
    errors += [f'없는 사진 묶음: {k}' for k in used - set(photos)]
    for k, items in photos.items():
        for it in items:
            if not os.path.exists(os.path.join(settings.MEDIA_ROOT, MEDIA_DIR, it['file'])):
                errors.append(f'사진 파일 없음: {it["file"]}')
    if text.count('⟦') != text.count('⟧'):
        errors.append('빈칸 괄호 짝이 맞지 않는다')
    if errors:
        print('\n'.join(errors[:20]))
        return 1

    # 사진 격자는 앞뒤를 빈 줄로 띄워야 마크다운이 HTML 덩어리로 둔다
    content = re.sub(r'\[\[사진:([a-z_]+)\]\]', lambda m: '\n' + photo_grid(m.group(1), photos) + '\n', text)
    sections = len(re.findall(r'^## ', content, re.M))
    print(f'절 {sections}개 · 빈칸 {text.count("⟦")}개 · 사진 {sum(len(photos[k]) for k in used)}장 · {len(content):,}자')
    if not apply_:
        print('검사만 했습니다 (--apply 로 반영)')
        return 0
    for cert in Certification.objects.filter(name__in=('조경기사', '조경산업기사')):
        _, created = GisaEssayNote.objects.update_or_create(
            certification=cert, slug=SLUG,
            defaults={'title': TITLE, 'content': content, 'order': ORDER,
                      'summary': '출제 비중 순 핵심 요약 — 빈칸을 눌러 답 확인, 수종·병해 사진'})
        print(f'  {cert.name}: {"생성" if created else "갱신"}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
