# -*- coding: utf-8 -*-
"""손상된 구분기호를 법령 표기(ㆍ)로 되돌린다.

★ 일괄 정규화는 하지 않는다. 조사 결과:
    '•' 89회 — 대부분 [box] 안 불릿 목록. 바꾸면 목록이 깨진다
    '·' 537회 — '흡수·정화' 같은 정상 병렬 표기
    '∙' 54회 — U+2219 BULLET OPERATOR. 전부 법령 용어 자리에만 나타난다
               ('생태∙경관보전지역', '시∙도지사', '도시∙군기본계획')

  '∙' 만 손상으로 판정한 근거
    - 2020-2, 2021-2 두 회차에만 나타난다 (특정 추출 경로 문제)
    - 54건 전부가 법령 원문이 'ㆍ' 를 쓰는 자리다
    - 같은 회차 안에 정상 'ㆍ' 가 공존한다 (폰트 매핑 손상의 특징)

사용법:
    python fix_symbols.py            # 확인만
    python fix_symbols.py --apply
    python fix_symbols.py --restore
"""
import io, json, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import GisaQuestion

BACKUP = "_symbols_backup.json"
FIELDS = ["text", "choice_1", "choice_2", "choice_3", "choice_4"]
BAD = "\u2219"   # ∙ BULLET OPERATOR
GOOD = "\u318d"  # ㆍ 한글 가운뎃점


def main():
    if "--restore" in sys.argv:
        rows = json.load(open(BACKUP, encoding="utf-8"))
        for r in rows:
            q = GisaQuestion.objects.filter(pk=r["pk"]).first()
            if q:
                setattr(q, r["field"], r["before"])
                q.save(update_fields=[r["field"]])
        print("복원 %d건" % len(rows))
        return

    apply = "--apply" in sys.argv
    changes, hits = [], 0
    for q in (GisaQuestion.objects.filter(exam__certification__name="자연생태복원기사")
              .select_related("exam").iterator(chunk_size=500)):
        for f in FIELDS:
            v = getattr(q, f) or ""
            if BAD not in v:
                continue
            hits += v.count(BAD)
            changes.append({
                "pk": q.pk,
                "ref": "%d-%d-%d" % (q.exam.year, q.exam.round, q.number),
                "field": f, "before": v, "after": v.replace(BAD, GOOD)})

    print("대상 %d개 필드 · %d곳" % (len(changes), hits))
    for c in changes[:8]:
        i = c["before"].find(BAD)
        print("   %-10s %-9s …%s…" % (c["ref"], c["field"],
              c["before"][max(0, i - 16):i + 16].replace("\n", " ")))

    if not apply:
        print()
        print("확인만 (--apply 로 반영)")
        return

    json.dump(changes, open(BACKUP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for c in changes:
        q = GisaQuestion.objects.get(pk=c["pk"])
        setattr(q, c["field"], c["after"])
        q.save(update_fields=[c["field"]])
    print()
    print("반영 완료 %d개 필드 (백업 %s)" % (len(changes), BACKUP))


main()
