import json

with open("카페글_시험문제.json", "r", encoding="utf-8") as f:
    data = json.load(f)

questions = data["questions"]
subjects = {}
for q in questions:
    subj = q.get("과목", "미분류")
    subjects[subj] = subjects.get(subj, 0) + 1

with open("통합_결과.txt", "w", encoding="utf-8") as out:
    out.write(f"총 문제수: {len(questions)}\n")
    out.write(f"총 과목수: {len(subjects)}개\n\n")
    out.write(f"{'='*50}\n")
    out.write(f"과목별 문제 수:\n")
    out.write(f"{'='*50}\n")
    for k, v in sorted(subjects.items(), key=lambda x: -x[1]):
        out.write(f"  {k}: {v}개\n")

print("통합_결과.txt 저장 완료")
