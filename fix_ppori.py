"""'뿌리뱅이' → '뽀리뱅이' (표준 국명). 쪽집게 노트와 그 문항 해설에서 고친다.

--apply 없이 돌리면 바뀔 자리만 보여 준다.
"""
import os
import sys

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from django.db.models import Q                      # noqa: E402
from exam.models import Question, StudyNote         # noqa: E402

BAD, GOOD = '뿌리뱅이', '뽀리뱅이'
apply = '--apply' in sys.argv
n_note = n_exp = 0

for note in StudyNote.objects.filter(subject_id=51, content__contains=BAD):
    k = note.content.count(BAD)
    n_note += k
    print(f'노트 {note.order}장 "{note.title}" — {k}건')
    if apply:
        note.content = note.content.replace(BAD, GOOD)
        note.save(update_fields=['content', 'updated_at'])

flt = Q(explanation__contains=BAD)
for f in ('choice_1_exp', 'choice_2_exp', 'choice_3_exp', 'choice_4_exp'):
    flt |= Q(**{f + '__contains': BAD})
for q in Question.objects.filter(subject_id=51).filter(flt):
    fields = []
    for f in ('explanation', 'choice_1_exp', 'choice_2_exp', 'choice_3_exp', 'choice_4_exp'):
        v = getattr(q, f) or ''
        if BAD in v:
            n_exp += v.count(BAD)
            fields.append(f)
            if apply:
                setattr(q, f, v.replace(BAD, GOOD))
    print(f'문항 {q.year}-{q.number} 해설 — {", ".join(fields)}')
    if apply and fields:
        q.save(update_fields=fields)

print(f'\n노트 {n_note}건 · 해설 {n_exp}건' + (' 고쳤습니다.' if apply else ' (미적용 — --apply 로 반영)'))
