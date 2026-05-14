# MockGeneration: certification → subject 단위 변경
# 기존 레코드는 의미가 달라지므로 모두 삭제 후 스키마 재구성

from django.conf import settings
from django.db import migrations, models


def delete_old_rows(apps, schema_editor):
    MockGeneration = apps.get_model('gisa', 'MockGeneration')
    MockGeneration.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('gisa', '0010_mockgeneration'),
    ]

    operations = [
        # 1) 기존 데이터 삭제
        migrations.RunPython(delete_old_rows, migrations.RunPython.noop),

        # 2) unique_together 해제 후 certification 제거 + subject 추가
        migrations.AlterUniqueTogether(
            name='mockgeneration',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='mockgeneration',
            name='certification',
        ),
        migrations.AddField(
            model_name='mockgeneration',
            name='subject',
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
                related_name='mock_generations',
                to='gisa.gisasubject',
                verbose_name='과목',
            ),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='mockgeneration',
            unique_together={('user', 'subject')},
        ),
    ]
