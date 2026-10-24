"""AI 모임 사전 설문(/poll/) — 한울회와 별개 모임. 상세는 docs/AI설문.md."""
import csv
import time
from collections import Counter, OrderedDict

from django.contrib.auth.decorators import user_passes_test
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache

from .models import PollResponse
from .questions import CIRCLED, PARTS, QMAP, QUESTIONS, csv_columns, other_index, parse_post

staff_required = user_passes_test(lambda u: u.is_active and u.is_staff)

# 도배 방지 — 교실 와이파이는 수강생 전원이 같은 공인 IP 로 나가므로 IP 한도는 넉넉히,
# 한 브라우저(쿠키)는 30초에 한 번만.
IP_LIMIT, IP_WINDOW = 20, 60
COOKIE_GAP = 30


def _client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return (xff.split(",")[0].strip() if xff else "") or request.META.get("REMOTE_ADDR", "")


def _rate_limited(request):
    last = request.get_signed_cookie("poll_last", default=None, salt="poll", max_age=3600)
    if last and time.time() - float(last) < COOKIE_GAP:
        return True
    key = "poll_ip_" + _client_ip(request)
    n = cache.get(key, 0)
    if n >= IP_LIMIT:
        return True
    cache.set(key, n + 1, IP_WINDOW)
    return False


def _parts_with_questions():
    parts = []
    for i, p in enumerate(PARTS):
        parts.append({**p, "questions": [q for q in QUESTIONS if q["part"] == i]})
    return parts


@never_cache
def survey(request):
    errors, answers, notice = {}, {}, ""
    if request.method == "POST":
        name, answers, errors = parse_post(request.POST)
        if not errors:
            if _rate_limited(request):
                notice = "방금 제출하셨습니다. 30초쯤 뒤에 다시 눌러 주세요."
            else:
                PollResponse.objects.create(name=name, answers=answers)
                resp = redirect("poll:thanks")
                resp.set_signed_cookie("poll_last", str(time.time()), salt="poll", max_age=3600, samesite="Lax")
                return resp
        else:
            notice = "빠진 문항이 있습니다. 빨간 표시를 확인해 주세요."
    return render(request, "poll/survey.html", {
        "parts": _parts_with_questions(), "errors": errors, "answers": answers,
        "notice": notice, "circled": CIRCLED,
    })


def thanks(request):
    return render(request, "poll/thanks.html")


def _survey_url(request):
    url = request.build_absolute_uri("/poll/s/")
    if "hanulstudy.kr" in url and url.startswith("http://"):
        url = "https://" + url[len("http://"):]
    return url


def _latest_by_name():
    """이름별 마지막 응답만(이름 앞뒤 공백·대소문자 무시)."""
    seen = OrderedDict()
    for r in PollResponse.objects.order_by("-created_at"):
        k = r.name.strip().lower()
        if k not in seen:
            seen[k] = r
    return list(seen.values())


def qr(request):
    import segno

    url = _survey_url(request)
    svg = segno.make(url, error="m").svg_inline(scale=10, border=2, dark="#111", light="#fff")
    return render(request, "poll/qr.html", {"url": url, "svg": svg, "count": len(_latest_by_name())})


@never_cache
def count(request):
    return JsonResponse({"count": len(_latest_by_name()), "total": PollResponse.objects.count()})


# ── 통계 ──────────────────────────────────────────────

LEVEL_RULE = [
    ("활용 중", "6번이 '일주일에 몇 번' 이상이고, 4번이 '문서 작성도 한다' 이상"),
    ("입문", "6번이 '써 본 적 없다'·'몇 번 해 봤다'이거나, 4번이 '전화·카톡 정도만'"),
    ("써 봄", "그 밖의 경우(예: 한 달에 몇 번, 또는 자주 쓰지만 컴퓨터는 검색·유튜브 정도)"),
]


def classify(ans):
    q4, q6 = QMAP["q4"]["choices"], QMAP["q6"]["choices"]
    a4 = q4.index(ans["q4"]) if ans.get("q4") in q4 else -1
    a6 = q6.index(ans["q6"]) if ans.get("q6") in q6 else -1
    if a6 < 0 and a4 < 0:
        return "미응답"
    if a6 >= 3 and a4 >= 2:
        return "활용 중"
    if (0 <= a6 <= 1) or a4 == 0:
        return "입문"
    return "써 봄"


def _dist(rows, q, key=None):
    """보기별 [(보기, 수, %)] — 고른 사람 수 기준 %."""
    key = key or q["id"]
    c = Counter()
    answered = 0
    for a in rows:
        v = a.get(key)
        if not v:
            continue
        answered += 1
        for x in (v if isinstance(v, list) else [v]):
            c[x] += 1
    out = []
    for i, ch in enumerate(q["choices"]):
        n = c.get(ch, 0)
        out.append({"label": ch, "mark": CIRCLED[i] if i < len(CIRCLED) else "", "n": n,
                    "pct": round(n * 100 / answered) if answered else 0})
    return answered, out


def _ranked(dist):
    return sorted([d for d in dist if d["n"]], key=lambda d: -d["n"])


def _display(ans, key):
    v = ans.get(key, "")
    return ", ".join(v) if isinstance(v, list) else v


@staff_required
def stats(request):
    latest = _latest_by_name()
    rows = [r.answers for r in latest]
    n = len(rows)

    charts = []
    for q in QUESTIONS:
        if q["type"] in ("single", "multi"):
            answered, dist = _dist(rows, q)
            others = [a.get(q["id"] + "_other") for a in rows if a.get(q["id"] + "_other")]
            charts.append({"q": q, "answered": answered, "dist": dist, "others": others})

    # 수준 분류
    levels = OrderedDict((k, []) for k in ("입문", "써 봄", "활용 중", "미응답"))
    for r in latest:
        levels[classify(r.answers)].append(r)
    level_rows = [{"name": k, "people": v, "n": len(v), "pct": round(len(v) * 100 / n) if n else 0}
                  for k, v in levels.items() if k != "미응답" or v]

    # 9번 이해도
    q9 = QMAP["q9"]
    understanding = []
    for i, it in enumerate(q9["items"], 1):
        key = f"q9_{i}"
        vals = [a.get(key) for a in rows if a.get(key)]
        tot = len(vals)
        right = sum(1 for v in vals if v == it["answer"])
        dunno = sum(1 for v in vals if v == "모르겠다")
        wrong = tot - right - dunno
        pct = (lambda x: round(x * 100 / tot) if tot else 0)
        understanding.append({**it, "tot": tot, "right": right, "wrong": wrong, "dunno": dunno,
                              "right_pct": pct(right), "wrong_pct": pct(wrong), "dunno_pct": pct(dunno)})

    # 10번 용어
    q10 = QMAP["q10"]
    terms = []
    for i, it in enumerate(q10["items"], 1):
        key = f"q10_{i}"
        vals = [a.get(key) for a in rows if a.get(key)]
        tot = len(vals)
        cnt = Counter(vals)
        segs = [{"label": ch, "n": cnt.get(ch, 0), "pct": round(cnt.get(ch, 0) * 100 / tot) if tot else 0}
                for ch in q10["choices"]]
        terms.append({"text": it["text"], "tot": tot, "segs": segs, "new_pct": segs[0]["pct"]})

    _, d11 = _dist(rows, QMAP["q11"])
    _, d13 = _dist(rows, QMAP["q13"])
    _, d14 = _dist(rows, QMAP["q14"])

    texts = []
    for qid in ("q12", "q16"):
        q = QMAP[qid]
        texts.append({"q": q, "items": [(r.name, r.answers.get(qid)) for r in latest if r.answers.get(qid)]})

    cols = [(h, k) for h, k in csv_columns() if k != "q1"]
    table = [{"r": r, "level": classify(r.answers), "cells": [_display(r.answers, k) for _, k in cols]}
             for r in latest]

    return render(request, "poll/stats.html", {
        "n": n, "total": PollResponse.objects.count(), "charts": charts,
        "levels": level_rows, "level_rule": LEVEL_RULE,
        "understanding": understanding, "terms": terms,
        "rank11": _ranked(d11), "rank13": _ranked(d13), "dist14": d14,
        "texts": texts, "cols": cols, "table": table, "now": timezone.localtime(),
    })


@staff_required
def stats_csv(request):
    """CSV — 기본은 이름별 마지막 응답, ?all=1 이면 모든 제출."""
    if request.GET.get("all"):
        objs = list(PollResponse.objects.order_by("created_at"))
    else:
        objs = sorted(_latest_by_name(), key=lambda r: r.created_at)
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = (
        f"attachment; filename*=UTF-8''ai_poll_{timezone.localtime():%Y%m%d_%H%M}.csv")
    resp.write("﻿")
    w = csv.writer(resp)
    cols = csv_columns()
    w.writerow(["제출 시각", "수준"] + [h for h, _ in cols])
    for r in objs:
        w.writerow([timezone.localtime(r.created_at).strftime("%Y-%m-%d %H:%M:%S"), classify(r.answers)]
                   + [_display(r.answers, k) for _, k in cols])
    return resp
