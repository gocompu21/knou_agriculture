"""
Django DB를 UTF-8 JSON으로 덤프하는 스크립트
Windows 인코딩 문제를 우회합니다.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
import io

output = io.StringIO()
call_command(
    'dumpdata',
    '--natural-foreign',
    '--natural-primary',
    '--exclude=contenttypes',
    '--exclude=auth.permission',
    '--indent=2',
    stdout=output,
)

with open('db_backup.json', 'w', encoding='utf-8') as f:
    f.write(output.getvalue())

print(f"✅ db_backup.json 저장 완료! ({os.path.getsize('db_backup.json'):,} bytes)")
