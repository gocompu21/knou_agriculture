# -*- coding: utf-8 -*-
"""단어 중간이 갈라진 자리를 되붙인다. 예) "휴 양형" -> "휴양형"

fix_split_words.py 는 문장 끝 어미가 갈라진 경우(것 은? / 한 다.)를 다룬다.
이쪽은 단어 한가운데가 갈라져 어미 규칙에 안 걸리는 경우다.

판별
  "A B" 에서 A가 1글자이고
    - A가 조사·의존명사로 단독 사용되지 않으며 (SOLO 목록 + 실사용 빈도)
    - 붙인 AB 가 말뭉치에 2회 이상 나오고
    - B 단독 빈도가 AB 빈도보다 낮으면
  조판 흔적으로 본다.

말뭉치는 4개 자격증의 노트 + 전체 문항이다.

사용법:
    python fix_mid_split.py            # 확인만
    python fix_mid_split.py --apply    # DB 반영
    python fix_mid_split.py --restore  # 되돌리기
"""
import io, json, os, re, sys
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import GisaQuestion, GisaTextbook

FIELDS = ["text", "choice_1", "choice_2", "choice_3", "choice_4",
          "explanation", "choice_1_exp", "choice_2_exp",
          "choice_3_exp", "choice_4_exp"]
BACKUP = "_mid_split_backup.json"

W = re.compile(r"[가-힣]{2,10}")
# 단독 어절로 정상 사용되는 1글자 (조사·의존명사·수량 단위 등)
SOLO = set("것 수 등 및 때 곳 중 내 외 시 후 전 간 년 월 일 개 명 회 차 급 형 종 상 하 "
           "위 아 그 이 저 각 총 약 초 말 억 원 만 천 백 십 두 세 네 다 더 못 안 잘 또 "
           "즉 단 대 소 고 좀 봄 뜻 힘 물 흙 논 밭 산 강 숲 잎 알 새 벌 균 병 약 열 빛 "
           "폭 층 면 점 선 별 군 목 과 속 문 강 계 문 장 항 호 절 관 조 편 부 권 판 쪽".split())
SOLO_RE = re.compile(r"(?:^|[\s(\[])([가-힣])(?=[\s).,\]]|$)")
GAP = re.compile(r"(?<![가-힣])([가-힣]) ([가-힣]{1,8})")


def build():
    vocab, solo = Counter(), Counter()
    for tb in GisaTextbook.objects.all():
        for w in W.findall(tb.content or ""):
            vocab[w] += 1
    for q in GisaQuestion.objects.all().only(*FIELDS).iterator(chunk_size=500):
        for f in FIELDS:
            v = getattr(q, f) or ""
            for w in W.findall(v):
                vocab[w] += 1
            for m in SOLO_RE.finditer(v):
                solo[m.group(1)] += 1
    return vocab, solo


def fix(text, vocab, solo, stat=None):
    def rep(m):
        a, b = m.group(1), m.group(2)
        if a in SOLO or solo.get(a, 0) >= 8:
            return m.group(0)
        joined = a + b
        if vocab.get(joined, 0) < 2:
            return m.group(0)
        if vocab.get(b, 0) >= vocab.get(joined, 0):
            return m.group(0)
        if stat is not None:
            stat[joined] += 1
        return joined
    return GAP.sub(rep, text)


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
    print("말뭉치 구축 중...")
    vocab, solo = build()
    print("어휘 %d개" % len(vocab))

    stat, changes = Counter(), []
    for q in (GisaQuestion.objects.all()
              .select_related("exam", "exam__certification").iterator(chunk_size=500)):
        for f in FIELDS:
            v = getattr(q, f) or ""
            if not v:
                continue
            out = fix(v, vocab, solo, stat)
            if out != v:
                changes.append({
                    "pk": q.pk, "cert": q.exam.certification.name,
                    "ref": "%d-%d-%d" % (q.exam.year, q.exam.round, q.number),
                    "field": f, "before": v, "after": out})

    print()
    print("수정 대상 %d개 필드 · %d곳" % (len(changes), sum(stat.values())))
    for w, n in stat.most_common(20):
        print("   %-12s %d곳" % (w, n))

    if not apply:
        print()
        print("확인만 (--apply 로 반영)")
        return

    json.dump(changes, open(BACKUP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for ch in changes:
        q = GisaQuestion.objects.get(pk=ch["pk"])
        setattr(q, ch["field"], ch["after"])
        q.save(update_fields=[ch["field"]])
    print()
    print("반영 완료 %d개 필드 (백업 %s)" % (len(changes), BACKUP))


main()
