from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import EmailVerificationToken


class Command(BaseCommand):
    help = "7일 이상 미승인·미인증인 비활성 회원 자동 삭제"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days", type=int, default=7,
            help="이 일수보다 오래된 미인증·미승인 회원 삭제 (기본 7)",
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="실제로 삭제하지 않고 대상만 출력",
        )

    def handle(self, *args, **opts):
        days = opts["days"]
        dry = opts["dry_run"]
        cutoff = timezone.now() - timedelta(days=days)

        # is_active=False 이면서 가입한 지 N일이 지난 사용자
        # (관리자 미승인 + 승인됐지만 메일 인증 안 한 케이스 모두 포함)
        targets = User.objects.filter(
            is_active=False,
            date_joined__lt=cutoff,
        )
        cnt = targets.count()
        self.stdout.write(f"삭제 대상: {cnt}명 (cutoff: {cutoff:%Y-%m-%d %H:%M})")
        for u in targets[:30]:
            approved = getattr(getattr(u, 'profile', None), 'is_approved', False)
            status = '승인됨/미인증' if approved else '미승인'
            self.stdout.write(f"  - {u.username} | {u.email} | 가입 {u.date_joined:%Y-%m-%d %H:%M} | {status}")

        if dry:
            self.stdout.write(self.style.WARNING("dry-run 모드: 실제 삭제 안 함"))
            return

        deleted, _ = targets.delete()
        self.stdout.write(self.style.SUCCESS(f"{deleted}건 삭제 완료"))
