# -*- coding: utf-8 -*-
"""기사시험 문항별 기출 빈출도 등급(1~5) 산출.

정의
  쪽집게 노트의 절/항에 연결된 기출 문항 수 = 그 **주제**의 출제 빈도.
  한 문항이 여러 절에 걸리면 그중 **가장 빈출인 절**의 값을 그 문항의 점수로 삼는다.
  (부수적으로 언급된 절보다 주력 주제가 그 문항의 성격을 규정한다)

  "같은 문제가 몇 번 나왔나"(문항 반복)는 채택하지 않았다.
  자연생태복원기사 실측에서 66%가 1회성이라 ★1에 몰려 변별력이 없었다.

등급
  절대 구간으로 자르면 특정 등급에 쏠리므로(실측 ★5=32%),
  실제 점수 분포를 목표 비중(TARGET)으로 잘라 경계를 자동 결정한다.

사용법:
    python calc_freq_tier.py 자연생태복원기사             # 계산·분포만
    python calc_freq_tier.py 자연생태복원기사 --apply     # DB 저장
    python calc_freq_tier.py --all --apply                # 노트 있는 자격증 전체
"""
import argparse
import io
import os
import sys
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from gisa.models import Certification, GisaQuestion, GisaTextbook
from gisa.views import parse_study_guide

# 노트가 완성돼 등급을 매길 수 있는 자격증
ALL_CERTS = [
    "자연생태복원기사",
    "식물보호기사",
    "식물보호산업기사",
    "조경기사",
]

# 목표 비중 (★5 가 가장 적고 아래로 갈수록 넓다).
# 절대 구간(11개+/7~10개…)으로 자르면 ★5 가 32% 로 쏠려 변별력이 없어
# 실제 점수 분포를 이 비중으로 잘라 경계를 자동 결정한다.
TARGET = [(5, 0.10), (4, 0.20), (3, 0.30), (2, 0.25), (1, 0.15)]


def build_cutoffs(scores):
    """점수 목록에서 목표 비중에 맞는 (하한, 등급) 경계를 만든다."""
    ordered = sorted(scores, reverse=True)
    n = len(ordered)
    cuts = []
    idx = 0
    for tier, share in TARGET[:-1]:
        idx += int(round(n * share))
        idx = min(idx, n - 1)
        cuts.append((ordered[idx], tier))
    # 같은 점수가 경계에 걸치면 상위 등급이 부풀 수 있으므로
    # 경계값이 겹치면 아래 등급 쪽으로 한 칸 내린다
    fixed = []
    prev = None
    for lo, tier in cuts:
        if prev is not None and lo >= prev:
            lo = prev - 1
        fixed.append((max(lo, 1), tier))
        prev = lo
    return fixed


def tier_of(n, cutoffs):
    for lo, t in cutoffs:
        if n >= lo:
            return t
    return 1


# 한 문항이 두 계통의 노트에 모두 걸리면 중복 계상돼 상위 등급으로 쏠린다.
# 자연생태복원기사는 2022년 개편으로 구/신 노트가 공존하므로,
# 현재 노출 중인 통합 4과목만 센다(구 체계 포함 시 실측 ★5 가 52%).
# 나머지 자격증은 노트 계통이 하나뿐이라 제한이 필요 없다.
ACTIVE_NOTES = {
    "자연생태복원기사": {
        "생태환경조사분석",
        "생태복원계획",
        "생태복원설계·시공",
        "생태복원 사후관리·평가",
    },
}


def collect_ref_scores(cert):
    """ref -> 그 ref 가 걸린 절 중 최대 문항수"""
    best = defaultdict(int)
    n_sec = 0

    tb_qs = GisaTextbook.objects.filter(certification=cert)
    only = ACTIVE_NOTES.get(cert.name)
    if only:
        tb_qs = tb_qs.filter(subject__name__in=only)

    for tb in tb_qs.select_related("subject"):
        for ch in parse_study_guide(tb.content):
            stack = []
            for s in ch.get("sections", []):
                stack.append(s)
                stack.extend(s.get("subsections") or [])
            for node in stack:
                refs = node.get("questions") or []
                if not refs:
                    continue
                n_sec += 1
                k = len(refs)
                for r in refs:
                    if k > best[r]:
                        best[r] = k
    return best, n_sec


def run(cert_name, apply=False):
    cert = Certification.objects.get(name=cert_name)
    print("=" * 64)
    print("■ %s" % cert.name)
    print("=" * 64)
    best, n_sec = collect_ref_scores(cert)
    print("노트에서 수집한 절/항: %d개 · 고유 ref %d개" % (n_sec, len(best)))
    print()

    qs = (GisaQuestion.objects
          .filter(exam__certification=cert)
          .exclude(exam__exam_type="최신")
          .select_related("exam", "subject"))

    qs = list(qs)
    scored = []
    unmatched = 0
    for q in qs:
        ref = "%d-%d-%d" % (q.exam.year, q.exam.round, q.number)
        score = best.get(ref, 0)
        if not score:
            unmatched += 1
        scored.append((q, score))

    # 등급은 **과목 안에서** 매긴다.
    #
    # 노트의 절 크기가 자격증·과목마다 크게 달라(식물보호기사 잡초방제학은
    # 244문항짜리 절이 있고 조경기사는 최대 29개) 절대 문항수로 자르면
    # 한 과목이 상위 등급을 독식한다. 실측에서 잡초방제학이 ★4↑ 88.8%,
    # 재배학원론이 0.0% 로 갈렸다.
    #
    # 과목별로 잘라야 "이 과목 안에서 어디를 먼저 볼까"라는
    # 실제 학습 판단에 맞고, 과목마다 같은 비율로 ★5 가 나온다.
    by_subject_scores = defaultdict(list)
    for q, score in scored:
        by_subject_scores[q.subject_id].append(score)
    subj_cutoffs = {
        sid: build_cutoffs(vals) for sid, vals in by_subject_scores.items()
    }

    sample = sorted(subj_cutoffs.items())[0][1] if subj_cutoffs else []
    print("[등급 경계] 과목별로 산출 (예: %s · 나머지 ★1)"
          % " · ".join("★%d=%d개+" % (t, lo) for lo, t in sample))
    print()

    dist = Counter()
    by_subj = defaultdict(Counter)
    updates = []
    for q, score in scored:
        cutoffs = subj_cutoffs[q.subject_id]
        t = tier_of(score, cutoffs) if score else 1
        dist[t] += 1
        by_subj[q.subject.name][t] += 1
        updates.append((q.pk, t, score))

    total = sum(dist.values())
    print("[등급 분포]")
    for t in (5, 4, 3, 2, 1):
        n = dist[t]
        bar = "#" * int(n / total * 50)
        print("  %s %5d문항 (%4.1f%%) %s"
              % ("★" * t + "☆" * (5 - t), n, n / total * 100, bar))
    print("  노트 미연결(→★1 처리): %d문항" % unmatched)
    print()

    print("[과목별 평균 등급]")
    for s in sorted(by_subj, key=lambda x: -sum(k * v for k, v in by_subj[x].items()) / max(sum(by_subj[x].values()), 1)):
        c = by_subj[s]
        n = sum(c.values())
        avg = sum(k * v for k, v in c.items()) / n
        top = c[5] + c[4]
        print("  %-22s 평균 %.2f · ★4↑ %3d개(%4.1f%%) · %d문항"
              % (s, avg, top, top / n * 100, n))

    if apply:
        from django.db import transaction
        with transaction.atomic():
            for pk, t, _ in updates:
                GisaQuestion.objects.filter(pk=pk).update(freq_tier=t)
        print()
        print("DB 저장 완료: %d문항" % len(updates))
    else:
        print()
        print("계산만 수행 (--apply 로 DB 저장)")
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cert", nargs="?", help="자격증명 (--all 이면 생략)")
    ap.add_argument("--all", action="store_true", help="노트가 있는 자격증 전체")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if args.all:
        targets = ALL_CERTS
    elif args.cert:
        targets = [args.cert]
    else:
        ap.error("자격증명을 지정하거나 --all 을 쓸 것")

    for name in targets:
        try:
            run(name, apply=args.apply)
        except Certification.DoesNotExist:
            print("[자격증 없음] %s\n" % name)


if __name__ == "__main__":
    main()
