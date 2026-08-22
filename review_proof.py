# -*- coding: utf-8 -*-
"""교정 제안을 사람이 검토하기 좋게 정리한다. DB 는 건드리지 않는다."""
import glob, io, json, os, re, sys, difflib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

kind_filter = None
conf_filter = None
limit = 40
for a in sys.argv[1:]:
    if a.startswith("--kind="): kind_filter = a.split("=", 1)[1]
    if a.startswith("--conf="): conf_filter = a.split("=", 1)[1]
    if a.startswith("--limit="): limit = int(a.split("=", 1)[1])

rows = []
for fp in sorted(glob.glob("_proof/*_fix.json")):
    d = json.load(open(fp, encoding="utf-8"))
    for f in d.get("fixes", []):
        if kind_filter and f.get("kind") != kind_filter: continue
        if conf_filter and f.get("confidence") != conf_filter: continue
        rows.append(f)

def diff_span(b, a):
    """바뀐 부분만 앞뒤 문맥과 함께 보여준다."""
    sm = difflib.SequenceMatcher(None, b, a)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal": continue
        pre = b[max(0, i1 - 20):i1]
        post = b[i2:i2 + 20]
        out.append("…%s[%s→%s]%s…" % (pre, b[i1:i2] or "∅", a[j1:j2] or "∅", post))
    return " / ".join(out[:3])

print("제안 %d건 (kind=%s conf=%s)" % (len(rows), kind_filter or "전체", conf_filter or "전체"))
print()
for f in rows[:limit]:
    print("%-11s %-10s [%s/%s]" % (f.get("ref"), f.get("field"), f.get("kind"), f.get("confidence")))
    print("   %s" % diff_span(f.get("before", ""), f.get("after", "")).replace("\n", " "))
    if f.get("note"): print("   ↳ %s" % f["note"])
