from django.db import migrations


COHORT_38_NAMES = [
    '이대진', '문선아', '강남복', '권윤영',
    '배기환', '서준호', '하임순', '황금희',
]


def set_cohort_38(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('accounts', 'UserProfile')
    for name in COHORT_38_NAMES:
        for u in User.objects.filter(first_name=name):
            profile, _ = UserProfile.objects.get_or_create(user=u)
            profile.cohort = 38
            profile.save(update_fields=['cohort'])


def reverse_set_cohort_38(apps, schema_editor):
    UserProfile = apps.get_model('accounts', 'UserProfile')
    UserProfile.objects.filter(cohort=38).update(cohort=None)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_userprofile_cohort'),
    ]

    operations = [
        migrations.RunPython(set_cohort_38, reverse_set_cohort_38),
    ]
