import os, django, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from exam.models import StudyNote, Question
from main.models import Subject

# Accept subject pk as command line argument, default to 8 (인간과교육 3학년)
subject_pk = int(sys.argv[1]) if len(sys.argv) > 1 else 8
subject = Subject.objects.get(pk=subject_pk)
print(f'Subject: {subject.name} (pk={subject.pk}, grade={subject.grade})')

# Read content from markdown file
md_file = f'data/{subject.name}_쪽집게노트.md'
with open(md_file, 'r', encoding='utf-8') as f:
    content = f.read()

note, created = StudyNote.objects.update_or_create(
    subject=subject,
    title='쪽집게 노트',
    defaults={
        'content': content,
        'order': 0,
    }
)

action = 'Created' if created else 'Updated'
print(f'{action}: {note}')
print(f'Content length: {len(content)} characters')
print(f'Content lines: {content.count(chr(10))}')

# Verify coverage
refs = re.findall(r'(\d{4})-기말-(\d+)', content)
unique_refs = set(refs)
print(f'Total unique question references: {len(unique_refs)}')

questions = Question.objects.filter(subject_id=subject_pk).order_by('year', 'number')
all_q = set((str(q.year), str(q.number)) for q in questions)
ref_set = set((y, n) for y, n in refs)
missing = all_q - ref_set
if missing:
    print(f'Missing {len(missing)} questions:')
    for y, n in sorted(missing):
        print(f'  {y}-기말-{n}')
else:
    print(f'All {len(all_q)} questions are referenced!')
