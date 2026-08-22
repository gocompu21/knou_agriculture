# -*- coding: utf-8 -*-
"""반영한 B(글자 변경) 268건을 원본 PDF와 대조한다.

PDF 는 최종 판정 기준이 아니다. comcbt PDF 자체가 복원본이라
원본 단계에서 이미 오류가 있다(예: '생몰종', '법류', '화경정책기본법').
여기서는 '우리가 바꾼 글자가 PDF 에 실제로 어떻게 있었는지'만 확인하고,
판정은 사람/에이전트가 문맥을 보고 한다.

출력: _pdf_verify.json  (회차별 배치로 나눠 에이전트에게 넘긴다)
"""
import io, json, os, re, sys, difflib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
import fitz

PDF_DIR = "data/comcbt"
_cache = {}


def pdf_text(rk):
    if rk in _cache:
        return _cache[rk]
    path = os.path.join(PDF_DIR, "자연생태복원기사%s.pdf" % rk)
    if not os.path.exists(path):
        _cache[rk] = None
        return None
    doc = fitz.open(path)
    t = "\n".join(p.get_text() for p in doc)
    doc.close()
    _cache[rk] = t
    return t


def norm(s):
    return re.sub(r"\s+", "", s or "")


rows = json.load(open("_proof_B_safe.json", encoding="utf-8"))["fixes"]
out = []
no_pdf = 0
for f in rows:
    ref = f["ref"]
    rk = ref.rsplit("-", 1)[0]
    num = ref.rsplit("-", 1)[1]
    t = pdf_text(rk)
    if t is None:
        no_pdf += 1
        continue
    b, a = f["before"], f["after"]
    # 바뀐 조각 추출
    changes = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, b, a).get_opcodes():
        if tag == "equal":
            continue
        changes.append({
            "old": b[i1:i2], "new": a[j1:j2],
            "ctx_before": b[max(0, i1 - 18):i2 + 18],
            "ctx_after": a[max(0, j1 - 18):j2 + 18],
        })
    if not changes:
        continue
    # PDF 에 옛 형태가 있는지 / 새 형태가 있는지
    nt = norm(t)
    for c in changes:
        key_old = norm(c["ctx_before"])
        key_new = norm(c["ctx_after"])
        c["in_pdf_old"] = key_old[:26] in nt if len(key_old) >= 8 else None
        c["in_pdf_new"] = key_new[:26] in nt if len(key_new) >= 8 else None
    out.append({
        "ref": ref, "round": rk, "number": int(num),
        "field": f["field"], "kind": f.get("kind"),
        "note": f.get("note", ""),
        "changes": changes,
    })

json.dump({"items": out}, open("_pdf_verify.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("대조 대상 %d건 (PDF 없음 %d건 제외)" % (len(out), no_pdf))

# 요약: PDF 에 '옛 형태'가 있던 비율
both = sum(1 for x in out for c in x["changes"] if c.get("in_pdf_old"))
newf = sum(1 for x in out for c in x["changes"] if c.get("in_pdf_new"))
tot = sum(len(x["changes"]) for x in out)
print("변경 조각 %d개 중" % tot)
print("  PDF 에 '수정 전' 형태 존재: %d" % both)
print("  PDF 에 '수정 후' 형태 존재: %d" % newf)
