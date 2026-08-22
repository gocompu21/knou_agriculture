# -*- coding: utf-8 -*-
"""낱자로 갈라진 자리를 되붙인다. 예) "목 표 달성" -> "목표 달성"

★ 이 유형은 자동 판별이 불가능하다.
   같은 문자열이라도 문맥에 따라 정반대이기 때문이다.
     "효과, 목 표 달성"  -> 조판 흔적 (붙여야 함)
     "수목 표면에 달라붙는" -> 정상 (붙이면 망가짐)
     "순환 경로를 갖지 않는다" -> 정상
   1글자 어절 연속을 기계적으로 붙이면 '볼 수', '이 중', '더 큰',
   '둘 다' 같은 정상 표기까지 605곳 넘게 망가진다(실측).

   그래서 **앞뒤 단어를 포함한 구체적 문맥**을 지정해 치환한다.
   새 사례가 나오면 CASES 에 문맥과 함께 추가한다.

사용법:
    python fix_char_split.py            # 확인만
    python fix_char_split.py --apply
"""
import io, json, os, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import GisaQuestion

BACKUP = "_char_split_backup.json"

# (찾을 문맥, 바꿀 문맥) — 앞뒤 단어를 포함해 오탐을 막는다
CASES = [
    ("목 표 달성", "목표 달성"),
    ("목표종 서 식 여부", "목표종 서식 여부"),
    ("토 양의 부적절", "토양의 부적절"),
    ("토 양생성", "토양생성"),
    ("수 질의 용수", "수질의 용수"),
    ("생 태계 보호", "생태계 보호"),
    ("해양생 태계", "해양생태계"),
    ("모니 터링", "모니터링"),
]

FIELDS = ["text", "choice_1", "choice_2", "choice_3", "choice_4",
          "explanation", "choice_1_exp", "choice_2_exp",
          "choice_3_exp", "choice_4_exp"]


def main():
    apply = "--apply" in sys.argv
    changes = []
    for q in (GisaQuestion.objects.all()
              .select_related("exam").iterator(chunk_size=500)):
        for f in FIELDS:
            v = getattr(q, f) or ""
            if not v:
                continue
            out = v
            for a, b in CASES:
                if a in out:
                    out = out.replace(a, b)
            if out != v:
                changes.append({
                    "pk": q.pk,
                    "ref": "%d-%d-%d" % (q.exam.year, q.exam.round, q.number),
                    "field": f, "before": v, "after": out})

    print("수정 대상 %d개 필드" % len(changes))
    for c in changes:
        i = 0
        for a, b in CASES:
            j = c["before"].find(a)
            if j >= 0:
                i = j
                break
        print("  %-10s [%s]" % (c["ref"], c["field"]))
        print("     전 ...%s..." % c["before"][max(0, i - 26):i + 26].replace("\n", " "))
        print("     후 ...%s..." % c["after"][max(0, i - 26):i + 26].replace("\n", " "))

    if not apply:
        print()
        print("확인만 (--apply 로 반영)")
        return

    json.dump(changes, open(BACKUP, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    for c in changes:
        q = GisaQuestion.objects.get(pk=c["pk"])
        setattr(q, c["field"], c["after"])
        q.save(update_fields=[c["field"]])
    print()
    print("반영 완료 %d개 필드 (백업 %s)" % (len(changes), BACKUP))


main()
