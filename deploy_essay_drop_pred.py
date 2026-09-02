"""서버에서 예상문제(source='예상')를 걷어낸다.

교재 저자가 만든 문항이라 저작권 부담은 큰데, 최근 7회차 96문항 중
4문항(4%)밖에 예고하지 못해 학습 값어치가 낮았다. 기출만 남긴다.
백업은 로컬 _essay_predicted_removed.json 에 있다.
"""
import os, sys, django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from gisa.models import GisaEssayQuestion, GisaEssaySession, GisaEssayAttempt

pred = GisaEssayQuestion.objects.filter(source='예상')
att = GisaEssayAttempt.objects.filter(question__source='예상').count()
if att:
    # 응시 기록이 있으면 사용자 이력이 사라지므로 손대지 않는다
    print(f'중단: 예상문제 응시 기록이 {att}건 있습니다. 확인 후 진행하세요.')
    sys.exit(1)

GisaEssaySession.objects.filter(source='예상').delete()
n, _ = pred.delete()
print(f'예상문제 {n}건 삭제 / 남은 문항 {GisaEssayQuestion.objects.count()}건')
