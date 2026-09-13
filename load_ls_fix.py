# -*- coding: utf-8 -*-
"""조경 실기 문항의 손본 내용을 서버에 반영한다 (`_ls_fix_deploy.json`).

`_ls_frac_deploy.json` 은 답 항목만 나르지만 이쪽은 **문제문·답 항목·답 서술을
함께** 나른다. 그림을 문제문에서 답으로 옮기는 것처럼 여러 필드가 한꺼번에
바뀌는 수정에 쓴다.

**자격증 pk 가 로컬과 서버에서 다르므로** pk 가 아니라
(자격증명, source, year, round, number) 로 문항을 찾는다.

  python load_ls_fix.py           # 검증만
  python load_ls_fix.py --apply   # DB 반영
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

FIELDS = ('text', 'answer_items', 'answer_text')


def main():
    apply_ = '--apply' in sys.argv
    rows = json.load(io.open('_ls_fix_deploy.json', encoding='utf-8'))
    upd = same = miss = 0
    for r in rows:
        q = GisaEssayQuestion.objects.filter(
            certification__name=r['cert'], source=r['source'],
            year=r['year'], round=r['round'], number=r['number']).first()
        label = f"{r['cert']} {r['source']} {r['year']}-{r['round']} {r['number']}번"
        if not q:
            miss += 1
            print(f'  !! 문항 없음: {label}')
            continue
        diff = [f for f in FIELDS if f in r and getattr(q, f) != r[f]]
        if not diff:
            same += 1
            continue
        upd += 1
        print(f'  {"고침" if apply_ else "고칠 것"}: {label} — {", ".join(diff)}')
        if apply_:
            for f in diff:
                setattr(q, f, r[f])
            q.save(update_fields=diff)
    print(f'\n{upd}건 수정 · {same}건 그대로 · {miss}건 없음'
          + (' — 반영했다.' if apply_ else ' (미반영 — --apply 로 넣는다)'))
    return 1 if miss else 0


if __name__ == '__main__':
    sys.exit(main())
