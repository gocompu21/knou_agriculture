# -*- coding: utf-8 -*-
"""조경(산업)기사 실기 학습자료를 GisaEssayNote 에 넣는다.

교재 PART 6 조경적산의 이론 20쪽(교재 276~283, 293~304)을 읽고 공식·수치만
추려 정리한 것이다. 이론을 그대로 옮기지 않았다 — 적산의 알맹이는 표준품셈의
수치와 원가계산 체계라 **사실**이고, 보호되는 것은 표현과 구성이므로 서술과
표 구성은 새로 썼다.

**두 자격증에 같은 내용을 넣는다.** 필답 출제범위가 거의 같고(산업기사는 조경사만
빠진다) 적산은 완전히 겹친다. 자격증별로 노트를 따로 쓸 값어치가 없다.

  python load_ls_note.py            # 무엇이 바뀌는지만 보여 준다
  python load_ls_note.py --apply
"""
import io
import os
import sys

import django

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from gisa.models import Certification, GisaEssayNote      # noqa: E402

APPLY = '--apply' in sys.argv

NOTES = [
    {
        'slug': 'calc',
        'title': '적산 공식 정리',
        'summary': '토공량·운반·기계화 시공·재료량·수목식재 품·원가계산의 공식과 함정',
        'order': 0,
        'path': '_ls_note_calc.md',
    },
]

for cert in Certification.objects.filter(name__startswith='조경'):
    for spec in NOTES:
        content = io.open(spec['path'], encoding='utf-8').read()
        note = GisaEssayNote.objects.filter(certification=cert, slug=spec['slug']).first()
        old = len(note.content) if note else 0
        if note and note.content == content and note.title == spec['title']:
            print(f'  {cert.name} / {spec["slug"]} — 그대로')
            continue
        print(f'  {cert.name} / {spec["slug"]} — {old}자 → {len(content)}자')
        if APPLY:
            GisaEssayNote.objects.update_or_create(
                certification=cert, slug=spec['slug'],
                defaults={'title': spec['title'], 'summary': spec['summary'],
                          'order': spec['order'], 'content': content})

print('\n반영했다.' if APPLY else '\n미반영 — --apply 로 넣는다.')
