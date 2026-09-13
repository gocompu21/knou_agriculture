# -*- coding: utf-8 -*-
"""조경 실기 기출의 한글 분수([frac]) 답 항목을 서버에 반영한다.

로컬에서 `fix_ls_hangul_frac.py --apply` 로 고친 결과를 `_ls_frac_deploy.json`
으로 내보내 두었다. **자격증 pk 가 로컬과 서버에서 다르므로** pk 가 아니라
(자격증명, source, year, round, number) 로 문항을 찾는다.

구유형 적산(source='적산')은 `load_ls_ch1.py` 가 배포하므로 여기 없다.

  python load_ls_frac.py           # 검증만
  python load_ls_frac.py --apply   # DB 반영
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


def main():
    apply_ = '--apply' in sys.argv
    rows = json.load(io.open('_ls_frac_deploy.json', encoding='utf-8'))
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
        if q.answer_items == r['items']:
            same += 1
            continue
        upd += 1
        print(f'  {"고침" if apply_ else "고칠 것"}: {label}')
        if apply_:
            q.answer_items = r['items']
            q.save(update_fields=['answer_items'])
    print(f'\n{upd}건 수정 · {same}건 그대로 · {miss}건 없음'
          + (' — 반영했다.' if apply_ else ' (미반영 — --apply 로 넣는다)'))
    return 1 if miss else 0


if __name__ == '__main__':
    sys.exit(main())
