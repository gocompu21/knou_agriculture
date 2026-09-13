# -*- coding: utf-8 -*-
"""Chapter 01(구유형 적산) 문항의 그림을 서버에 반영한다.

로컬에서 `add_ls_ch1_figures.py --apply` 로 넣은 결과를 `_ls_ch1_fig_deploy.json`
으로 내보내 두었다. SVG 본문이 통째로 들어 있어 서버에서는 그림을 다시 그리지
않고 그대로 싣는다.

**자격증 pk 가 로컬과 서버에서 다르므로** pk 가 아니라 (source='적산', number)
로 문항을 찾는다.

  python load_ls_ch1_figs.py           # 검증만
  python load_ls_ch1_figs.py --apply   # DB 반영

`load_ls_ch1.py`(문항 본문) 뒤에 돌린다 — 순서가 바뀌면 본문 쪽 자리표시가
그림을 덮는다. 그래서 load_ls_ch1.py 에도 덮어쓰기 막이를 두었다.
"""
import io
import json
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.getcwd())
sys.stdout.reconfigure(encoding='utf-8')

import django  # noqa: E402

django.setup()

from gisa.models import GisaEssayQuestion  # noqa: E402

CERT, SOURCE = '조경기사', '적산'
FIELDS = ('text', 'answer_items', 'answer_text')


def main():
    apply_ = '--apply' in sys.argv
    rows = json.load(io.open('_ls_ch1_fig_deploy.json', encoding='utf-8'))
    upd = same = miss = drawn = 0
    for r in rows:
        q = GisaEssayQuestion.objects.filter(
            certification__name=CERT, source=SOURCE, number=r['number']).first()
        if not q:
            miss += 1
            print(f'  !! {r["number"]}번 문항이 없다')
            continue
        if '<svg' in r['text'] or '<svg' in (r['answer_text'] or ''):
            drawn += 1
        diff = [f for f in FIELDS if getattr(q, f) != r[f]]
        if not diff:
            same += 1
            continue
        upd += 1
        print(f'  {"고침" if apply_ else "고칠 것"}: {r["number"]}번 — {", ".join(diff)}')
        if apply_:
            for f in diff:
                setattr(q, f, r[f])
            q.save(update_fields=diff)
    print(f'\n{upd}건 수정 · {same}건 그대로 · {miss}건 없음 '
          f'(그림이 그려진 문항 {drawn}/{len(rows)})'
          + (' — 반영했다.' if apply_ else ' (미반영 — --apply 로 넣는다)'))
    return 1 if miss else 0


if __name__ == '__main__':
    sys.exit(main())
