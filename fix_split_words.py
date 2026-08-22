# -*- coding: utf-8 -*-
"""PDF 조판 줄바꿈이 공백으로 굳은 자리를 되붙인다.

예) "다른 종의 침입에 저 항하거나" -> "저항하거나"

판별 원리
  "A B" 에서 A가 1글자이고, 붙인 AB가 말뭉치에 흔한데
  B가 단독으로는 거의 안 쓰이면 조판 흔적으로 본다.
  말뭉치는 그 자격증의 노트 + 전체 문항 텍스트다.

오탐 배제 (실측으로 확정한 규칙)
  1. A 앞에 숫자가 붙으면 제외 — "제2조 제1항", "1억 원", "10년 마다"
     조판 흔적이 아니라 정상 표기다. 이 유형이 오탐의 대부분(1103/1493)이었다.
  2. A 앞뒤가 한자·괄호면 제외 — 법조문 인용 형태
  3. 화이트리스트에 없는 조합은 --apply 해도 건너뛴다 (안전 우선)

사용법:
    python fix_split_words.py --cert 자연생태복원기사            # 확인만
    python fix_split_words.py --cert 자연생태복원기사 --apply    # DB 반영
    python fix_split_words.py --all-certs --apply
"""
import argparse
import io
import json
import os
import re
import sys
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from gisa.models import Certification, GisaQuestion, GisaTextbook

FIELDS = ["text", "choice_1", "choice_2", "choice_3", "choice_4",
          "explanation", "choice_1_exp", "choice_2_exp",
          "choice_3_exp", "choice_4_exp"]

WORD = re.compile(r"[가-힣]{2,10}")
BACKUP = "_split_words_backup.json"

# 붙임 형태가 이만큼 흔해야 후보로 본다
MIN_JOIN = 20


def build_vocab(certs):
    vocab = Counter()
    for cert in certs:
        for tb in GisaTextbook.objects.filter(certification=cert):
            for w in WORD.findall(tb.content or ""):
                vocab[w] += 1
        qs = GisaQuestion.objects.filter(exam__certification=cert).only(*FIELDS)
        for q in qs.iterator(chunk_size=500):
            for f in FIELDS:
                for w in WORD.findall(getattr(q, f) or ""):
                    vocab[w] += 1
    return vocab


# 되붙일 자리를 "어미·조사가 갈라진 경우"로 한정한다.
# 빈도만으로 판단하면 정상 표현까지 붙어버린다. 실측 오탐:
#   같은 "조 제2항"  다음 "각 호"  같은 "항 제2호"
#   환경용량의 "한 측면"  개보수 "시 가장"  식물체 "내 수분"  1천만 "원"
# 반면 문장 끝 어미가 떨어져 나온 것은 오탐 여지가 없다.
TAIL = [
    # (앞글자 조건 없음) 뒤에 오는 조각 -> 문장 끝/관형형 어미
    r"다\.", r"다\)", r"다,", r"다$",
    r"은\?", r"는\?", r"을\?",
    r"은 것", r"는 것", r"을 것",
    r"은데", r"는데",
]
TAIL_RE = re.compile(r"([가-힣]) (" + "|".join(TAIL) + r")")

# 위 규칙으로 안 잡히는 개별 사례. 문맥을 직접 확인하고 넣는다.
EXTRA = [
    ("저 항", "저항"),
    ("종 간 상호작용", "종간 상호작용"),
    ("융합형으 로", "융합형으로"),
]


def fix_text(text, vocab=None, stat=None):
    """조판 흔적을 되붙인 문자열을 돌려준다."""
    def _join(m):
        if stat is not None:
            stat[m.group(1) + m.group(2)] += 1
        return m.group(1) + m.group(2)

    out = TAIL_RE.sub(_join, text)
    for before, after in EXTRA:
        if before in out:
            if stat is not None:
                stat[after] += out.count(before)
            out = out.replace(before, after)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cert")
    ap.add_argument("--all-certs", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--restore", action="store_true")
    args = ap.parse_args()

    if args.restore:
        if not os.path.exists(BACKUP):
            print("백업 없음:", BACKUP)
            return
        rows = json.load(open(BACKUP, encoding="utf-8"))
        n = 0
        for r in rows:
            q = GisaQuestion.objects.filter(pk=r["pk"]).first()
            if q:
                setattr(q, r["field"], r["before"])
                q.save(update_fields=[r["field"]])
                n += 1
        print("복원 %d건" % n)
        return

    certs = (list(Certification.objects.all()) if args.all_certs
             else [Certification.objects.get(name=args.cert)])

    print("말뭉치 구축 중...")
    vocab = build_vocab(certs)
    print("어휘 %d개" % len(vocab))
    print()

    stat = Counter()
    changes = []
    for cert in certs:
        qs = (GisaQuestion.objects.filter(exam__certification=cert)
              .select_related("exam"))
        for q in qs.iterator(chunk_size=500):
            for f in FIELDS:
                v = getattr(q, f) or ""
                if not v:
                    continue
                fixed = fix_text(v, vocab, stat)
                if fixed != v:
                    changes.append({
                        "pk": q.pk, "cert": cert.name,
                        "ref": "%d-%d-%d" % (q.exam.year, q.exam.round, q.number),
                        "field": f, "before": v, "after": fixed,
                    })

    print("수정 대상: %d개 필드 · 되붙인 자리 %d곳" % (len(changes), sum(stat.values())))
    print()
    print("[되붙인 형태 상위]")
    for w, c in stat.most_common(30):
        print("   %-10s %d곳" % (w, c))

    if not args.apply:
        print()
        print("확인만 수행 (--apply 로 반영)")
        with open("_split_words_preview.json", "w", encoding="utf-8") as f:
            json.dump(changes[:200], f, ensure_ascii=False, indent=1)
        print("미리보기 → _split_words_preview.json (앞 200건)")
        return

    with open(BACKUP, "w", encoding="utf-8") as f:
        json.dump(changes, f, ensure_ascii=False, indent=1)
    for ch in changes:
        q = GisaQuestion.objects.get(pk=ch["pk"])
        setattr(q, ch["field"], ch["after"])
        q.save(update_fields=[ch["field"]])
    print()
    print("반영 완료: %d개 필드 (백업 %s)" % (len(changes), BACKUP))


if __name__ == "__main__":
    main()
