# -*- coding: utf-8 -*-
"""자연생태복원기사 데이터를 EC2로 배포하기 위한 추출/적재 스크립트.

로컬(추출):
    python deploy_eco.py export
      → _deploy_eco.json  (문항+정답+해설, natural key 기반)
      → _deploy_eco_images.zip  (문항 이미지)

서버(적재):
    python deploy_eco.py load
      → _deploy_eco.json / _deploy_eco_images.zip 을 읽어 DB 반영
"""
import os
import sys
import json
import zipfile

sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.conf import settings
from django.core.files import File
from django.db import transaction
from gisa.models import Certification, GisaSubject, GisaExam, GisaQuestion

CERT_NAME = '자연생태복원기사'
CERT_CATEGORY = '기사'
SUBJECT_ORDER = [
    '환경생태학개론', '환경계획학', '생태복원공학', '경관생태학', '자연환경관계법규',
]
JSON_PATH = '_deploy_eco.json'
ZIP_PATH = '_deploy_eco_images.zip'

IMG_FIELDS = ['text_image', 'choice_1_image', 'choice_2_image',
              'choice_3_image', 'choice_4_image']


def export():
    cert = Certification.objects.get(name=CERT_NAME)
    qs = (GisaQuestion.objects
          .filter(exam__certification=cert)
          .select_related('exam', 'subject')
          .order_by('exam__year', 'exam__round', 'number'))

    rows = []
    img_names = set()
    for q in qs:
        item = {
            'year': q.exam.year,
            'round': q.exam.round,
            'exam_type': q.exam.exam_type,
            'subject': q.subject.name,
            'number': q.number,
            'text': q.text,
            'choice_1': q.choice_1,
            'choice_2': q.choice_2,
            'choice_3': q.choice_3,
            'choice_4': q.choice_4,
            'answer': q.answer,
            'explanation': q.explanation,
            'choice_1_exp': q.choice_1_exp,
            'choice_2_exp': q.choice_2_exp,
            'choice_3_exp': q.choice_3_exp,
            'choice_4_exp': q.choice_4_exp,
        }
        for f in IMG_FIELDS:
            v = getattr(q, f)
            item[f] = v.name if v else ''
            if v:
                img_names.add(v.name)
        rows.append(item)

    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump({'cert': CERT_NAME, 'category': CERT_CATEGORY,
                   'subjects': SUBJECT_ORDER, 'questions': rows},
                  f, ensure_ascii=False)

    # 이미지 zip
    n = 0
    with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as z:
        for name in sorted(img_names):
            src = os.path.join(settings.MEDIA_ROOT, name)
            if os.path.exists(src):
                z.write(src, arcname=name)
                n += 1

    has_exp = sum(1 for r in rows if r['explanation'])
    print('추출 완료')
    print('  문항 %d개 (해설 있음 %d개)' % (len(rows), has_exp))
    print('  이미지 %d개 → %s' % (n, ZIP_PATH))
    print('  JSON → %s (%.1f MB)' % (JSON_PATH, os.path.getsize(JSON_PATH) / 1024 / 1024))


def load():
    if not os.path.exists(JSON_PATH):
        print('JSON 없음:', JSON_PATH)
        return
    with open(JSON_PATH, encoding='utf-8') as f:
        data = json.load(f)

    # 이미지 먼저 풀기
    if os.path.exists(ZIP_PATH):
        with zipfile.ZipFile(ZIP_PATH) as z:
            z.extractall(settings.MEDIA_ROOT)
        print('이미지 압축 해제 완료 →', settings.MEDIA_ROOT)

    cert, _ = Certification.objects.get_or_create(
        name=data['cert'], defaults={'category': data['category']})
    subj_map = {}
    for i, name in enumerate(data['subjects'], start=1):
        s, _ = GisaSubject.objects.get_or_create(
            certification=cert, name=name, defaults={'order': i})
        if s.order != i:
            s.order = i
            s.save(update_fields=['order'])
        subj_map[name] = s

    exam_cache = {}
    n_new = n_upd = 0
    with transaction.atomic():
        for r in data['questions']:
            key = (r['year'], r['round'])
            exam = exam_cache.get(key)
            if exam is None:
                exam, _ = GisaExam.objects.get_or_create(
                    certification=cert, year=r['year'], round=r['round'],
                    exam_type=r.get('exam_type') or '필기')
                exam_cache[key] = exam

            defaults = {
                'subject': subj_map[r['subject']],
                'text': r['text'],
                'choice_1': r['choice_1'], 'choice_2': r['choice_2'],
                'choice_3': r['choice_3'], 'choice_4': r['choice_4'],
                'answer': r['answer'],
                'explanation': r['explanation'],
                'choice_1_exp': r['choice_1_exp'], 'choice_2_exp': r['choice_2_exp'],
                'choice_3_exp': r['choice_3_exp'], 'choice_4_exp': r['choice_4_exp'],
            }
            for f in IMG_FIELDS:
                if r.get(f):
                    defaults[f] = r[f]      # 경로 문자열 그대로 저장

            obj, created = GisaQuestion.objects.update_or_create(
                exam=exam, number=r['number'], defaults=defaults)
            n_new += int(created)
            n_upd += int(not created)

    print('적재 완료: 신규 %d · 갱신 %d (총 %d)' % (n_new, n_upd, len(data['questions'])))


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'export'
    if cmd == 'export':
        export()
    elif cmd == 'load':
        load()
    else:
        print('사용법: python deploy_eco.py [export|load]')
