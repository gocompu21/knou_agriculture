# -*- coding: utf-8 -*-
"""실기 필답형 문항 JSON → GisaEssayQuestion import

사용:
  python manage.py import_essay_questions                      # 기본 JSON 적재
  python manage.py import_essay_questions --json <경로>
  python manage.py import_essay_questions --images <디렉토리>   # 이미지도 함께
  python manage.py import_essay_questions --dry-run
"""
import os
import json

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from gisa.models import Certification, GisaEssayQuestion

DEFAULT_JSON = '_eco_essay_questions.json'
DEFAULT_IMG_DIR = os.path.join('_eco_essay_parsed', 'images')
DEFAULT_CERT = '자연생태복원기사'

# 유형별 배점 — 회차 합계가 45점에 가깝도록 배분
POINTS_BY_TYPE = {
    '계산': 4,
    '서술': 4,
    '표그림': 4,
    '열거': 3,
    '빈칸': 2,
    '단답': 2,
}

# 출제기준(2025~2027) 주요항목 8개 — 키워드로 문항을 자동 분류
STD_MAJORS = {
    1: ('생태복원 구상', ['목표종', '공간구상', '사업목표', '핵심구역', '완충구역', '전이', '프로그래밍', '컨셉']),
    2: ('생태기반환경복원 계획', ['토지이용', '동선', '지형복원', '토양', '표토', '수환경', '수리', '수문', '절토', '성토', '객토']),
    3: ('복원 후 관리계획', ['유지관리', '관리계획', '순응적', '이용자 관리', '관리목표']),
    4: ('서식지 복원계획', ['서식지', '숲복원', '초지', '습지', '비탈면', '생태통로', '하천', '인공지반', '벽면녹화', '서식처']),
    5: ('생태시설물 계획', ['관찰시설', '체험시설', '전시', '편의시설', '보전시설', '관리시설', '탐조', '데크']),
    6: ('모니터링 계획', ['모니터링']),
    7: ('생태복원 현장관리', ['공정', '예산', '품질', '안전', '공사', '내역', '품셈', '시방']),
    8: ('생태계 종합평가', ['비오톱', '가치평가', '생태자연도', '녹지자연도', '평가등급', '종다양', '군집', '식생조사',
                       '경관생태', '천이', '개체군', '먹이', '생물다양성']),
}


def guess_std_major(q):
    """문제문·답에서 키워드를 찾아 출제기준 주요항목을 추정한다."""
    blob = (q.get('text', '') + ' ' + ' '.join(q.get('answer_items') or []) +
            ' ' + q.get('answer_text', ''))
    best, best_hits = 0, 0
    for no, (_name, kws) in STD_MAJORS.items():
        hits = sum(1 for kw in kws if kw in blob)
        if hits > best_hits:
            best, best_hits = no, hits
    return best


class Command(BaseCommand):
    help = '실기 필답형 문항 JSON을 GisaEssayQuestion으로 적재한다'

    def add_arguments(self, parser):
        parser.add_argument('--json', default=DEFAULT_JSON)
        parser.add_argument('--images', default=DEFAULT_IMG_DIR,
                            help='크롭 이미지 디렉토리. --no-images로 생략 가능')
        parser.add_argument('--no-images', action='store_true')
        parser.add_argument('--cert', default=DEFAULT_CERT)
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **opt):
        path = opt['json']
        if not os.path.exists(path):
            self.stderr.write(f'JSON 없음: {path}')
            return
        with open(path, encoding='utf-8') as f:
            rows = json.load(f)

        cert = Certification.objects.filter(name=opt['cert']).first()
        if not cert:
            self.stderr.write(f'자격증 없음: {opt["cert"]}')
            return

        img_dir = None if opt['no_images'] else opt['images']
        created = updated = img_count = 0
        by_source = {}

        with transaction.atomic():
            for r in rows:
                source = r['source']
                section = r.get('section') or ''
                # 기출은 section을 "기출"로 통일 (unique_together 키 안정화)
                if source == '기출':
                    section = '기출'

                points = POINTS_BY_TYPE.get(r.get('type'), 3)
                defaults = {
                    'qtype': r.get('type', '서술'),
                    'text': r.get('text', ''),
                    'answer_items': r.get('answer_items') or [],
                    'answer_text': r.get('answer_text', ''),
                    'reference': r.get('reference', ''),
                    'notes': r.get('notes', ''),
                    'points': points,
                    'std_major': guess_std_major(r),
                }

                if opt['dry_run']:
                    by_source[source] = by_source.get(source, 0) + 1
                    continue

                obj, is_new = GisaEssayQuestion.objects.update_or_create(
                    certification=cert,
                    source=source,
                    section=section,
                    year=r.get('year'),
                    round=r.get('round'),
                    number=r['number'],
                    defaults=defaults,
                )
                created += is_new
                updated += (not is_new)
                by_source[source] = by_source.get(source, 0) + 1

                # 이미지 연결 (role별로 한 장씩만 — 여러 장이면 첫 장)
                if img_dir:
                    for im in (r.get('images') or []):
                        fname = im.get('file')
                        if not fname:
                            continue
                        fpath = os.path.join(img_dir, fname)
                        if not os.path.exists(fpath):
                            continue
                        role = im.get('role', 'answer')
                        field = {'question': 'text_image',
                                 'answer': 'answer_image',
                                 'reference': 'reference_image'}.get(role)
                        if not field or getattr(obj, field):
                            continue
                        with open(fpath, 'rb') as fh:
                            getattr(obj, field).save(fname, File(fh), save=False)
                        img_count += 1
                    obj.save()

        if opt['dry_run']:
            self.stdout.write(f'[dry-run] 대상 {len(rows)}문항 {by_source}')
            return

        self.stdout.write(self.style.SUCCESS(
            f'적재 완료: 신규 {created} / 갱신 {updated} / 이미지 {img_count}장'))
        self.stdout.write(f'출처별: {by_source}')
