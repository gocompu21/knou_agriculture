"""잡초방제학(4학년) 쪽집게 노트 15장을 StudyNote 로 적재한다.

_weed_notes_part1.md ~ part3.md 를 이어 붙여 `## 제N장.` 단위로 잘라
(subject, order) 기준 update_or_create 한다.
관련 문제 참조 (YYYY-N) 가 실제 Question 에 있는지, 등록된 문항이 노트에서
한 번도 참조되지 않았는지 검사한다.

  python load_weed_notes.py          # 검증만
  python load_weed_notes.py --apply  # DB 반영
"""
import os
import re
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
sys.stdout.reconfigure(encoding="utf-8")

from exam.models import Question, StudyNote  # noqa: E402
from main.models import Subject  # noqa: E402

PARTS = ["_weed_notes_part1.md", "_weed_notes_part2.md", "_weed_notes_part3.md"]
subject = Subject.objects.get(name="잡초방제학", grade=4)

text = "\n\n".join(open(p, encoding="utf-8").read().strip() for p in PARTS) + "\n"
open("_weed_notes_aplus.md", "w", encoding="utf-8").write(text)

chunks = re.split(r"(?m)^(?=## 제\d+장\.)", text)
chunks = [c.strip() for c in chunks if c.strip()]
chapters = []
for c in chunks:
    m = re.match(r"## (제(\d+)장\..*)", c)
    assert m, c[:40]
    chapters.append((int(m.group(2)), m.group(1).strip(), c + "\n"))
orders = [o for o, _, _ in chapters]
assert orders == list(range(1, 16)), orders

# 참조 검증
existing = {f"{y}-{n}" for y, n in Question.objects.filter(subject=subject).values_list("year", "number")}
refs = set()
bad = []
for _, title, body in chapters:
    for line in body.split("\n"):
        if "**관련 문제**" in line:
            for r in re.findall(r"\((\d{4}-\d+)\)", line):
                refs.add(r)
                if r not in existing:
                    bad.append((title, r))
    # 절마다 관련 문제 줄이 있는지
    secs = re.findall(r"(?m)^### (?!핵심)(.+)$", body)
    n_ref_lines = body.count("**관련 문제**")
    if n_ref_lines != len(secs):
        print(f"  주의: {title} 절 {len(secs)}개, 관련 문제 줄 {n_ref_lines}개")

unref = sorted(existing - refs, key=lambda s: (int(s.split('-')[0]), int(s.split('-')[1])))
print(f"장 {len(chapters)}개, 참조 {len(refs)}개, 등록 문항 {len(existing)}개")
print("없는 문항 참조:", bad or "없음")
print("참조되지 않은 문항:", unref or "없음")
if bad:
    sys.exit(1)

if "--apply" not in sys.argv:
    print("(검증만 함. --apply 로 반영)")
    sys.exit(0)

for order, title, body in chapters:
    StudyNote.objects.update_or_create(
        subject=subject, order=order,
        defaults={"title": title, "content": body})
extra = StudyNote.objects.filter(subject=subject, order__gt=15)
if extra.exists():
    print("order>15 노트 삭제:", extra.count())
    extra.delete()
print("StudyNote 반영 완료:", StudyNote.objects.filter(subject=subject).count(), "장")
