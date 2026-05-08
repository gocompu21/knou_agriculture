from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from bbs.models import NoticeOpenLog


class Command(BaseCommand):
    help = "30일 이전의 메일 열람 기록(NoticeOpenLog)을 자동 삭제"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days", type=int, default=30,
            help="이 일수보다 오래된 기록을 삭제 (기본 30)",
        )

    def handle(self, *args, **opts):
        days = opts["days"]
        cutoff = timezone.now() - timedelta(days=days)
        qs = NoticeOpenLog.objects.filter(opened_at__lt=cutoff)
        cnt = qs.count()
        deleted, _ = qs.delete()
        self.stdout.write(
            self.style.SUCCESS(f"{deleted}건 삭제 (cutoff: {cutoff:%Y-%m-%d %H:%M}, days={days})")
        )
