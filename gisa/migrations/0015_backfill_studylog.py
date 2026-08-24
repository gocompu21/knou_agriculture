# 기존 학습모드 기록(GisaAttempt.mode='study')을 학습기록(GisaStudyLog)으로 이관한다.
# 학습모드는 그동안 오답 선택(또는 '오답노트 보내기')만 GisaAttempt 에 남겼으므로
# 실제 풀어본 양보다 적은 하한값이지만, 진도율의 출발점으로 쓴다.
from django.db import migrations


def backfill(apps, schema_editor):
    GisaAttempt = apps.get_model("gisa", "GisaAttempt")
    GisaStudyLog = apps.get_model("gisa", "GisaStudyLog")
    # auto_now_add 가 bulk_create 시 현재 시각으로 덮어쓰므로 원래 시각을 살리기 위해 끈다
    GisaStudyLog._meta.get_field("created_at").auto_now_add = False
    rows = GisaAttempt.objects.filter(mode="study").values_list(
        "user_id", "question_id", "created_at"
    )
    batch = []
    for user_id, question_id, created_at in rows.iterator():
        batch.append(GisaStudyLog(user_id=user_id, question_id=question_id, created_at=created_at))
        if len(batch) >= 1000:
            GisaStudyLog.objects.bulk_create(batch)
            batch = []
    if batch:
        GisaStudyLog.objects.bulk_create(batch)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("gisa", "0014_gisastudylog"),
    ]

    operations = [
        migrations.RunPython(backfill, noop),
    ]
