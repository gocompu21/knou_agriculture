from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import EmailVerificationToken


class Command(BaseCommand):
    help = "24시간 이상 이메일 인증 안 한 비활성 회원 자동 삭제"

    def add_arguments(self, parser):
        parser.add_argument(
            "--hours", type=int, default=24,
            help="이 시간보다 오래된 미인증 회원 삭제 (기본 24)",
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="실제로 삭제하지 않고 대상만 출력",
        )

    def handle(self, *args, **opts):
        hours = opts["hours"]
        dry = opts["dry_run"]
        cutoff = timezone.now() - timedelta(hours=hours)

        targets = User.objects.filter(
            is_active=False,
            date_joined__lt=cutoff,
        )
        cnt = targets.count()
        self.stdout.write(f"삭제 대상: {cnt}명 (cutoff: {cutoff:%Y-%m-%d %H:%M})")
        for u in targets[:20]:
            self.stdout.write(f"  - {u.username} | {u.email} | 가입 {u.date_joined:%Y-%m-%d %H:%M}")

        if dry:
            self.stdout.write(self.style.WARNING("dry-run 모드: 실제 삭제 안 함"))
            return

        # CASCADE로 EmailVerificationToken도 함께 삭제됨
        deleted, _ = targets.delete()
        self.stdout.write(self.style.SUCCESS(f"{deleted}건 삭제 완료"))
