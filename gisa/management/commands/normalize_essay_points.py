# -*- coding: utf-8 -*-
"""기출 회차별 배점 합계를 45점으로 정규화한다.

유형별 기본 배점(계산·서술·표그림 4 / 열거 3 / 빈칸·단답 2)으로 매긴 뒤
회차 합계가 45점이 되도록 0.5점 단위로 조정한다. 조정은 배점이 큰 문항부터
가감하여 유형 간 상대적 무게를 유지한다.

예상문제는 회차 개념이 없으므로 유형별 기본 배점을 그대로 둔다.

사용:
  python manage.py normalize_essay_points
  python manage.py normalize_essay_points --dry-run
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from gisa.models import Certification, GisaEssayQuestion

TARGET = 45.0
STEP = 0.5
MIN_POINTS = 1.0


class Command(BaseCommand):
    help = '기출 회차별 필답 배점 합계를 45점으로 맞춘다'

    def add_arguments(self, parser):
        parser.add_argument('--cert', default='자연생태복원기사')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **opt):
        cert = Certification.objects.filter(name=opt['cert']).first()
        if not cert:
            self.stderr.write(f'자격증 없음: {opt["cert"]}')
            return

        rounds = (GisaEssayQuestion.objects
                  .filter(certification=cert, source='기출')
                  .values_list('year', 'round').distinct().order_by('year', 'round'))

        for year, rnd in rounds:
            qs = list(GisaEssayQuestion.objects.filter(
                certification=cert, source='기출', year=year, round=rnd).order_by('number'))
            if not qs:
                continue

            pts = {q.pk: float(q.points) for q in qs}
            total = sum(pts.values())
            diff = TARGET - total

            # 배점이 큰 문항부터(동점이면 번호 순) 0.5씩 가감
            order = sorted(qs, key=lambda q: (-pts[q.pk], q.number))
            guard = 0
            while abs(diff) >= 0.01 and guard < 10000:
                progressed = False
                for q in order:
                    if abs(diff) < 0.01:
                        break
                    if diff > 0:
                        pts[q.pk] += STEP
                        diff -= STEP
                        progressed = True
                    elif pts[q.pk] - STEP >= MIN_POINTS:
                        pts[q.pk] -= STEP
                        diff += STEP
                        progressed = True
                guard += 1
                if not progressed:
                    break

            new_total = sum(pts.values())
            changed = [q for q in qs if abs(pts[q.pk] - float(q.points)) >= 0.01]
            self.stdout.write(
                f'{year}-{rnd}: {total:g} -> {new_total:g}점 ({len(qs)}문항, {len(changed)}건 조정)')

            if opt['dry_run']:
                continue
            with transaction.atomic():
                for q in changed:
                    q.points = pts[q.pk]
                    q.save(update_fields=['points'])

        if opt['dry_run']:
            self.stdout.write(self.style.WARNING('[dry-run] 저장하지 않음'))
        else:
            self.stdout.write(self.style.SUCCESS('배점 정규화 완료'))
