# -*- coding: utf-8 -*-
"""실기 필답형 문항을 EC2로 배포하는 추출/적재 스크립트.

로컬(추출):
    python deploy_essay.py export
      → _deploy_essay.json        (537문항: 문제·답·참고·배점·분류)
      → _deploy_essay_images.zip  (문항 이미지 72장)

서버(적재):
    python deploy_essay.py load
      → 위 두 파일을 읽어 DB 반영 (update_or_create, pk 충돌 없음)

자연키는 (certification, source, section, year, round, number) 이며
이는 모델의 unique_together와 같다.
"""
import io
import json
import os
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django

django.setup()

from django.core.files import File
from django.db import transaction

from gisa.models import Certification, GisaEssayQuestion

CERT_NAME = '자연생태복원기사'
JSON_PATH = '_deploy_essay.json'
ZIP_PATH = '_deploy_essay_images.zip'

IMAGE_FIELDS = ['text_image', 'answer_image', 'reference_image']
PLAIN_FIELDS = [
    'source', 'section', 'year', 'round', 'number', 'qtype',
    'text', 'answer_items', 'answer_text', 'reference',
    'points', 'rubric', 'std_major', 'std_sub', 'notes',
]


def export():
    cert = Certification.objects.filter(name=CERT_NAME).first()
    if not cert:
        print(f'자격증 없음: {CERT_NAME}')
        return

    qs = GisaEssayQuestion.objects.filter(certification=cert).order_by(
        'source', 'section', 'year', 'round', 'number')
    rows, img_count = [], 0

    with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zf:
        for q in qs:
            row = {f: getattr(q, f) for f in PLAIN_FIELDS}
            row['images'] = {}
            for field in IMAGE_FIELDS:
                f = getattr(q, field)
                if not f or not f.name:
                    continue
                try:
                    path = f.path
                except Exception:
                    continue
                if not os.path.exists(path):
                    continue
                arc = f.name.replace('\\', '/')
                zf.write(path, arc)
                row['images'][field] = arc
                img_count += 1
            rows.append(row)

    with open(JSON_PATH, 'w', encoding='utf-8') as fh:
        json.dump({'cert': CERT_NAME, 'questions': rows}, fh,
                  ensure_ascii=False, indent=1)

    size_j = os.path.getsize(JSON_PATH) / 1024 / 1024
    size_z = os.path.getsize(ZIP_PATH) / 1024 / 1024
    print(f'export 완료: {len(rows)}문항 / 이미지 {img_count}장')
    print(f'  {JSON_PATH} ({size_j:.1f}MB)')
    print(f'  {ZIP_PATH} ({size_z:.1f}MB)')


def load():
    if not os.path.exists(JSON_PATH):
        print(f'파일 없음: {JSON_PATH}')
        return

    with open(JSON_PATH, encoding='utf-8') as fh:
        data = json.load(fh)

    cert = Certification.objects.filter(name=data.get('cert', CERT_NAME)).first()
    if not cert:
        print(f'자격증 없음: {data.get("cert")}')
        return

    # 이미지 압축 해제 (MEDIA_ROOT 기준)
    from django.conf import settings
    if os.path.exists(ZIP_PATH):
        with zipfile.ZipFile(ZIP_PATH) as zf:
            zf.extractall(settings.MEDIA_ROOT)
        print(f'이미지 압축 해제 → {settings.MEDIA_ROOT}')

    created = updated = img_linked = 0
    with transaction.atomic():
        for row in data['questions']:
            key = {
                'certification': cert,
                'source': row['source'],
                'section': row['section'],
                'year': row['year'],
                'round': row['round'],
                'number': row['number'],
            }
            defaults = {f: row[f] for f in PLAIN_FIELDS
                        if f not in ('source', 'section', 'year', 'round', 'number')}
            # 이미지 필드는 파일명만 저장하면 된다(파일은 zip으로 이미 배치됨)
            for field, name in (row.get('images') or {}).items():
                defaults[field] = name
                img_linked += 1

            obj, is_new = GisaEssayQuestion.objects.update_or_create(
                defaults=defaults, **key)
            created += is_new
            updated += (not is_new)

    print(f'load 완료: 신규 {created} / 갱신 {updated} / 이미지 연결 {img_linked}')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'export'
    if cmd == 'export':
        export()
    elif cmd == 'load':
        load()
    else:
        print('사용법: python deploy_essay.py [export|load]')
