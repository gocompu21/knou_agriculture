# -*- coding: utf-8 -*-
"""용언 어간과 어미 사이가 갈라진 자리를 되붙인다.

예) "이동통로가 단절되 거나" -> "단절되거나"

앞선 두 스크립트로는 안 잡힌다.
  fix_split_words.py  문장 끝 어미(것 은? / 한 다.)
  fix_mid_split.py    앞 조각이 1글자이고 단독 사용 안 되는 글자(휴 양형)
여기서는 앞 조각이 '되'처럼 흔한 글자라 1글자 기준으로는 못 거른다.

판별
  "...A B" 에서 A는 공백 앞 어절 전체(예: '단절되'), B는 뒤 어절.
  A가 단독 어절로는 거의 안 쓰이는데(사전 2회 미만)
  A+B 를 붙인 형태가 사전에 여러 번 나오면 조판 흔적으로 본다.

  '역할을 하는' 같은 정상 표기는 A='역할을' 이 사전에 흔해서 걸러진다.

사용법:
    python fix_stem_split.py            # 확인만
    python fix_stem_split.py --apply
    python fix_stem_split.py --restore
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
BACKUP = "_stem_split_backup.json"

TOKEN = re.compile(r"[가-힣]+")
# 앞 어절(2글자 이상) + 공백 + 뒤 어절
PAIR = re.compile(r"(?<![가-힣])([가-힣]{2,10}) ([가-힣]{2,8})(?![가-힣])")


def build():
    vocab = Counter()
    for tb in GisaTextbook.objects.all():
        for w in TOKEN.findall(tb.content or ""):
            vocab[w] += 1
    for q in GisaQuestion.objects.all().only(*FIELDS).iterator(chunk_size=500):
        for f in FIELDS:
            for w in TOKEN.findall(getattr(q, f) or ""):
                vocab[w] += 1
    return vocab


def fix(text, vocab, stat=None):
    """어절 목록을 훑으며 인접한 두 어절을 붙일지 판단한다.

    정규식 순차 매칭으로는 '이동통로가 단절되' 가 먼저 짝지어져
    '단절되 거나' 를 검사조차 못 한다. 그래서 어절 단위로 직접 훑는다.
    """
    parts = text.split(" ")
    if len(parts) < 2:
        return text
    out = [parts[0]]
    for nxt in parts[1:]:
        prev = out[-1]
        # 한글로만 이루어진 어절끼리만 대상
        if (prev and nxt and TOKEN.fullmatch(prev) and TOKEN.fullmatch(nxt)
                and 2 <= len(prev) <= 10 and 2 <= len(nxt) <= 8):
            joined = prev + nxt
            if (vocab.get(prev, 0) < 2 and vocab.get(joined, 0) >= 5
                    and len(joined) <= 12):
                out[-1] = joined
                if stat is not None:
                    stat[joined] += 1
                continue
        out.append(nxt)
    return " ".join(out)


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
    vocab = build()
    print("어휘 %d개" % len(vocab))

    stat, changes = Counter(), []
    for q in (GisaQuestion.objects.all()
              .select_related("exam", "exam__certification").iterator(chunk_size=500)):
        for f in FIELDS:
            v = getattr(q, f) or ""
            if not v:
                continue
            out = fix(v, vocab, stat)
            if out != v:
                changes.append({
                    "pk": q.pk, "cert": q.exam.certification.name,
                    "ref": "%d-%d-%d" % (q.exam.year, q.exam.round, q.number),
                    "field": f, "before": v, "after": out})

    print()
    print("수정 대상 %d개 필드 · %d곳" % (len(changes), sum(stat.values())))
    for w, n in stat.most_common(30):
        print("   %-14s %d곳 (사전%d)" % (w, n, vocab.get(w, 0)))

    if not apply:
        json.dump(changes[:120], open("_stem_split_preview.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print()
        print("확인만 (--apply 로 반영) · 미리보기 _stem_split_preview.json")
        return

    json.dump(changes, open(BACKUP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for ch in changes:
        q = GisaQuestion.objects.get(pk=ch["pk"])
        setattr(q, ch["field"], ch["after"])
        q.save(update_fields=[ch["field"]])
    print()
    print("반영 완료 %d개 필드 (백업 %s)" % (len(changes), BACKUP))


main()
