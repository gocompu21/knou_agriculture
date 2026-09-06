"""잡초방제학(4학년, 방송대) A+ 문제집 127문항을 exam.Question 으로 적재한다.

원본: 사용자가 준 A+ 문제집 PDF 4권을 직접 읽어 손으로 옮긴 _weed_questions_aplus.json
연도 배정 규칙
  - 태그 23년 → 2023, 24년 → 2024 (두 태그가 다 있으면 두 연도에 모두 등록)
  - 태그 25   → 2025 (카페 복원 응시기 25건과 대조해 2025년 출제가 확인된 문항)
  - lec(인강 예제, 출제연도 미확인) → 2025 에 "[인강] " 접두어로 등록
문항번호는 연도 안에서 문제집 순서대로 1부터 매긴다.

사용법
  python load_weed_questions.py            # 검증 + 배정표만 출력
  python load_weed_questions.py --apply    # 기존 잡초방제학 문항 백업 후 교체
"""
import json
import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
sys.stdout.reconfigure(encoding="utf-8")

from exam.models import Attempt, Question  # noqa: E402
from main.models import Subject  # noqa: E402

SRC = "_weed_questions_aplus.json"
BACKUP = "_weed_questions_backup_before_aplus.json"
MAP = "_weed_qmap.json"

subject = Subject.objects.get(name="잡초방제학", grade=4)
items = json.load(open(SRC, encoding="utf-8"))

# ── 검증 ──────────────────────────────────────────────
nos = [it["no"] for it in items]
assert nos == list(range(1, 128)), "문항 번호가 1~127 연속이 아님"
for it in items:
    assert len(it["c"]) == 4 and all(c.strip() for c in it["c"]), f"Q{it['no']} 보기 4개 아님"
    assert it["ans"] in "1234", f"Q{it['no']} 정답 이상"
    assert len(it["ce"]) == 4, f"Q{it['no']} 선지 해설 4개 아님"
    assert it["exp"].strip(), f"Q{it['no']} 해설 없음"
    assert it["text"].strip(), f"Q{it['no']} 문제 없음"

# ── 연도 배정 ──────────────────────────────────────────
plan = {2023: [], 2024: [], 2025: []}
for it in items:
    tags = set(it.get("tags", []))
    if "23" in tags:
        plan[2023].append(it)
    if "24" in tags:
        plan[2024].append(it)
    if "25" in tags or it.get("lec"):
        plan[2025].append(it)

qmap = {}
rows = []
for year, lst in plan.items():
    for i, it in enumerate(lst, 1):
        qmap.setdefault(it["no"], []).append(f"{year}-{i}")
        rows.append((year, i, it["no"], it.get("lec", False)))

unassigned = [it["no"] for it in items if it["no"] not in qmap]
assert not unassigned, f"연도 미배정 문항: {unassigned}"

print("연도별 문항 수:", {y: len(l) for y, l in plan.items()})
print("문항 → 연도-번호 배정표")
for no in range(1, 128):
    print(f"  Q{no:3d}: {', '.join(qmap[no])}")

json.dump(qmap, open(MAP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"배정표 저장: {MAP}")

if "--apply" not in sys.argv:
    print("(검증만 함. --apply 로 반영)")
    sys.exit(0)

# ── 반영 ──────────────────────────────────────────────
old = Question.objects.filter(subject=subject)
n_att = Attempt.objects.filter(question__subject=subject).count()
if n_att:
    print(f"응시 기록 {n_att}건이 있어 중단합니다. 먼저 확인하세요.")
    sys.exit(1)

backup = [
    {k: getattr(q, k) for k in (
        "year", "number", "text", "choice_1", "choice_2", "choice_3", "choice_4",
        "answer", "explanation", "choice_1_exp", "choice_2_exp", "choice_3_exp",
        "choice_4_exp")}
    for q in old.order_by("year", "number")
]
json.dump(backup, open(BACKUP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"기존 {len(backup)}문항 백업: {BACKUP}")
old.delete()

created = 0
for year, lst in plan.items():
    for i, it in enumerate(lst, 1):
        text = it["text"]
        if it.get("lec"):
            text = "[인강] " + text
        # 정답 선지에는 정답 설명을 넣는다 (프로젝트 규칙)
        ce = list(it["ce"])
        ce[int(it["ans"]) - 1] = it["exp"]
        Question.objects.create(
            subject=subject, year=year, number=i, text=text,
            choice_1=it["c"][0], choice_2=it["c"][1],
            choice_3=it["c"][2], choice_4=it["c"][3],
            answer=it["ans"], explanation=it["exp"],
            choice_1_exp=ce[0], choice_2_exp=ce[1],
            choice_3_exp=ce[2], choice_4_exp=ce[3],
            created_by_name="A+ 문제집",
        )
        created += 1
print(f"생성 {created}문항 완료")
