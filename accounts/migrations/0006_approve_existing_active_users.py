from django.db import migrations
from django.utils import timezone


def approve_existing_active_users(apps, schema_editor):
    """기존 활성 사용자 전원을 자동 승인 처리.
    새 가입자만 관리자 승인 절차를 거치도록 한다."""
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('accounts', 'UserProfile')
    now = timezone.now()
    for u in User.objects.filter(is_active=True):
        profile, _ = UserProfile.objects.get_or_create(user=u)
        if not profile.is_approved:
            profile.is_approved = True
            profile.approved_at = now
            profile.save(update_fields=['is_approved', 'approved_at'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_userprofile_approved_at_userprofile_approved_by_and_more'),
    ]

    operations = [
        migrations.RunPython(approve_existing_active_users, noop_reverse),
    ]
