"""쪽집게 노트의 특정 절 머리에 이미지 한 줄을 끼워 넣는다 (로컬·서버 공용, 멱등).

  python insert_note_image.py --subject 잡초방제학 --grade 4 --order 3 --sec 3.1 \
      --url /media/notes/s51/seedbank.jpg --alt "종자은행 인포그래픽"

절 제목 줄("### 3.1 …") 바로 다음 빈 줄 뒤에 `![alt](url)` 를 넣는다. 같은 url 이
이미 있으면 아무것도 하지 않는다. DB 의 현재 내용(관리자가 편집기로 고친 것 포함)을
그대로 두고 한 줄만 더한다.
"""
import argparse
import os
import re
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
sys.stdout.reconfigure(encoding="utf-8")

from exam.models import StudyNote  # noqa: E402
from main.models import Subject  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--subject", required=True)
ap.add_argument("--grade", type=int, required=True)
ap.add_argument("--order", type=int, required=True)
ap.add_argument("--sec", required=True)
ap.add_argument("--url", required=True)
ap.add_argument("--alt", default="")
ap.add_argument("--after", default="", help="이 문자열이 든 줄 바로 뒤에 넣는다 (없으면 절 머리)")
a = ap.parse_args()

subject = Subject.objects.get(name=a.subject, grade=a.grade)
note = StudyNote.objects.get(subject=subject, order=a.order)
if a.url in note.content:
    print("이미 있음:", a.url)
    sys.exit(0)

lines = note.content.split("\n")
idx = next((i for i, l in enumerate(lines)
            if re.match(rf"^###\s+{re.escape(a.sec)}(\s|$)", l.strip())), None)
if idx is None:
    print("절을 찾지 못함:", a.sec)
    sys.exit(1)
ins = f"![{a.alt}]({a.url})"
# 다음 절 제목 전까지가 이 절의 범위
end = next((i for i in range(idx + 1, len(lines)) if lines[i].startswith("### ")), len(lines))
if a.after == "@last-image":
    # 절 안의 마지막 이미지 줄 뒤에 넣는다 (이미지가 없으면 절 머리)
    last = next((i for i in range(end - 1, idx, -1) if lines[i].lstrip().startswith("![")), None)
    if last is None:
        a.after = ""
    else:
        lines[last + 1:last + 1] = ["", ins]
        a.after = None
if a.after:
    # 같은 절 안에서 --after 문자열이 든 줄 뒤에 넣는다
    j = next((i for i in range(idx + 1, len(lines))
              if a.after in lines[i] and not lines[i].startswith("### ")), None)
    if j is None:
        print("--after 줄을 찾지 못함:", a.after)
        sys.exit(1)
    lines[j + 1:j + 1] = ["", ins]
elif a.after == "":
    # 제목 다음 빈 줄을 지나 첫 본문 앞에 넣는다
    j = idx + 1
    while j < len(lines) and not lines[j].strip():
        j += 1
    lines[j:j] = [ins, ""]
note.content = "\n".join(lines)
note.save(update_fields=["content", "updated_at"])
print(f"넣음: {note.title} / {a.sec} 절 머리에 {ins}")
