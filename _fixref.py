import os, sys, django
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings'); django.setup()
from gisa.models import GisaEssayQuestion
q = GisaEssayQuestion.objects.get(certification__name='조경기사', year=2024, round=3, number=7)
add = ' 아래 사진에는 공용에 수피 사진이 없는 모과나무만 빠져 있습니다.'
if add.strip() not in q.reference:
    q.reference = q.reference.rstrip() + add
    q.save(update_fields=['reference'])
    print('더했다:', q.reference[-60:])
else:
    print('이미 있다')
