# -*- coding: utf-8 -*-
"""쪽집게 노트 안에서 같은 내용이 두 절에 중복 서술된 곳을 찾아 배치로 낸다.

4과목 통합 노트를 만들 때 구 체계 5과목을 병합하면서 같은 주제가
서로 다른 장에 각각 들어간 경우가 있다.

판정: 35자 이상 문장을 정규화(한글·숫자만)해 앞 60자가 같으면 중복으로 본다.
      '핵심 키워드 요약' 절은 장마다 반복되는 형식이라 제외한다.

사용법:
    python dump_note_dups.py --out-dir _dedup --min 2
"""
import argparse
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from gisa.models import Certification, GisaTextbook
from gisa.views import parse_study_guide

CERT = "자연생태복원기사"
SUBJECTS = {
    "생태환경조사분석": "survey",
    "생태복원계획": "plan",
    "생태복원설계·시공": "design",
    "생태복원 사후관리·평가": "mgmt",
}

TAG = re.compile(r"<[^>]+>")


def sentences(html):
    text = re.sub(r"\s+", " ", TAG.sub(" ", html or ""))
    return [s.strip() for s in re.split(r"[.。]\s+", text) if len(s.strip()) >= 35]


def norm(s):
    return re.sub(r"[^가-힣0-9]", "", s)


def collect(tb):
    """(절제목, html, refs, 장제목) 목록"""
    out = []
    for ch in parse_study_guide(tb.content):
        for sec in ch.get("sections", []):
            out.append((sec["title"], sec.get("content_html", ""),
                        sec.get("questions") or [], ch["title"]))
            for sub in sec.get("subsections") or []:
                out.append((sub["title"], sub.get("content_html", ""),
                            sub.get("questions") or [], ch["title"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--min", type=int, default=2,
                    help="이 문장 수 이상 겹치는 절 쌍만 낸다")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    cert = Certification.objects.get(name=CERT)
    grand = 0

    for name, pre in SUBJECTS.items():
        tb = GisaTextbook.objects.get(certification=cert, subject__name=name)
        nodes = collect(tb)

        idx = defaultdict(set)
        for title, html, _refs, _ch in nodes:
            if "키워드 요약" in title:
                continue
            for s in sentences(html):
                n = norm(s)
                if len(n) < 25:
                    continue
                idx[n[:60]].add(title)

        pair_hits = defaultdict(list)
        for key, titles in idx.items():
            if len(titles) < 2:
                continue
            ts = sorted(titles)
            for i in range(len(ts)):
                for j in range(i + 1, len(ts)):
                    pair_hits[(ts[i], ts[j])].append(key)

        info = {t: (h, r, c) for t, h, r, c in nodes}
        items = []
        for (a, b), keys in sorted(pair_hits.items(), key=lambda kv: -len(kv[1])):
            if len(keys) < args.min:
                continue
            ha, ra, ca = info.get(a, ("", [], ""))
            hb, rb, cb = info.get(b, ("", [], ""))
            items.append({
                "overlap": len(keys),
                "a": {"chapter": ca, "title": a, "refs": ra,
                      "chars": len(TAG.sub("", ha)), "html": ha},
                "b": {"chapter": cb, "title": b, "refs": rb,
                      "chars": len(TAG.sub("", hb)), "html": hb},
            })

        fp = os.path.join(args.out_dir, "%s_dups.json" % pre)
        with open(fp, "w", encoding="utf-8") as f:
            json.dump({"subject": name, "file": "%s.md" % pre, "pairs": items},
                      f, ensure_ascii=False, indent=1)
        grand += len(items)
        print("%-22s 절쌍 %3d개 → %s" % (name, len(items), os.path.basename(fp)))
        for it in items[:5]:
            print("    %2d문장  %s ↔ %s"
                  % (it["overlap"], it["a"]["title"][:32], it["b"]["title"][:32]))

    print()
    print("총 %d개 절쌍 · 출력 %s" % (grand, os.path.abspath(args.out_dir)))


if __name__ == "__main__":
    main()
