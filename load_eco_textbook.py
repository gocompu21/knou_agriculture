# -*- coding: utf-8 -*-
"""자연생태복원기사 쪽집게 노트 병합 + DB 저장 + 커버리지 검증.

사용법:
    python load_eco_textbook.py 환경생태학개론 env      # 병합 후 저장
    python load_eco_textbook.py 환경생태학개론 env --dry # 검증만
    python load_eco_textbook.py 생태환경조사분석 survey --dir <노트디렉토리>

--dir 를 생략하면 구 체계 노트 디렉토리(eco_notes)를 쓴다.
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from gisa.models import Certification, GisaSubject, GisaTextbook, GisaQuestion

CERT = "자연생태복원기사"
NOTE_DIR = (
    r"C:\Users\gocom\AppData\Local\Temp\claude"
    r"\c--Users-gocom-Documents-Antigravity-Django-BaseCamp-knou-agriculture"
    r"\7c55dddf-8e30-47d3-808a-796a5d5060bb\scratchpad\eco_notes"
)


def merge_parts(prefix, note_dir=None):
    """env_ch01_03.md, env_ch04_06.md ... 를 장 번호순으로 병합."""
    d = note_dir or NOTE_DIR
    parts = sorted(
        f for f in os.listdir(d)
        if f.startswith(prefix + "_ch") and f.endswith(".md")
    )
    if not parts:
        return None, []
    chunks = []
    for fn in parts:
        text = open(os.path.join(d, fn), encoding="utf-8").read().strip()
        chunks.append(text)
    return "\n\n---\n\n".join(chunks), parts


def check_coverage(content, subject_name):
    """노트가 참조한 기출 ref vs 실제 DB 문항 비교."""
    refs = set(re.findall(r"\((\d{4}-\d-\d{1,3})\)", content))
    subj = GisaSubject.objects.filter(
        certification__name=CERT, name=subject_name
    ).first()
    actual = set()
    for q in GisaQuestion.objects.filter(subject=subj).select_related("exam"):
        actual.add("%d-%d-%d" % (q.exam.year, q.exam.round, q.number))

    covered = refs & actual
    missing = actual - refs
    bogus = refs - actual
    return {
        "total": len(actual),
        "covered": len(covered),
        "missing": sorted(missing),
        "bogus": sorted(bogus),
        "pct": len(covered) / len(actual) * 100 if actual else 0,
    }


def check_structure(content):
    """마크다운 구조 점검."""
    return {
        "chapters": len(re.findall(r"(?m)^## 제\d+장", content)),
        "sections": len(re.findall(r"(?m)^### \d+\.\d+", content)),
        "subsections": len(re.findall(r"(?m)^#### \d+\.\d+\.\d+", content)),
        "keyword_tables": len(re.findall(r"(?m)^### 핵심 키워드 요약", content)),
        "chars": len(content),
        "lines": content.count("\n") + 1,
    }


def main():
    if len(sys.argv) < 3:
        print("사용법: python load_eco_textbook.py <과목명> <파일prefix> [--dry]")
        return
    subject_name, prefix = sys.argv[1], sys.argv[2]
    dry = "--dry" in sys.argv

    note_dir = NOTE_DIR
    if "--dir" in sys.argv:
        note_dir = sys.argv[sys.argv.index("--dir") + 1]

    content, parts = merge_parts(prefix, note_dir)
    if content is None:
        print("노트 파일 없음: %s_ch*.md in %s" % (prefix, note_dir))
        return

    print("병합 대상 %d개:" % len(parts))
    for p in parts:
        print("   ", p)

    st = check_structure(content)
    print("\n[구조] 장 %d · 절 %d · 항 %d · 키워드표 %d"
          % (st["chapters"], st["sections"], st["subsections"], st["keyword_tables"]))
    print("[분량] %s자 · %s줄" % (format(st["chars"], ","), format(st["lines"], ",")))

    cov = check_coverage(content, subject_name)
    print("\n[커버리지] %d/%d 문항 (%.1f%%)"
          % (cov["covered"], cov["total"], cov["pct"]))
    if cov["bogus"]:
        print("  ⚠ 존재하지 않는 ref %d개: %s"
              % (len(cov["bogus"]), ", ".join(cov["bogus"][:10])))
    if cov["missing"]:
        print("  미연결 %d개: %s%s"
              % (len(cov["missing"]), ", ".join(cov["missing"][:15]),
                 " ..." if len(cov["missing"]) > 15 else ""))

    if dry:
        print("\n(--dry: 저장하지 않음)")
        return

    cert = Certification.objects.get(name=CERT)
    subj = GisaSubject.objects.get(certification=cert, name=subject_name)
    tb, created = GisaTextbook.objects.update_or_create(
        certification=cert, subject=subj, defaults={"content": content}
    )
    print("\n저장 완료: %s %s (%s자)"
          % (subject_name, "생성" if created else "갱신", format(len(content), ",")))

    # 병합본을 파일로도 남김 (배포용)
    out = os.path.join(os.getcwd(), "_eco_textbook_%s.md" % prefix)
    open(out, "w", encoding="utf-8").write(content)
    print("병합본 저장: %s" % out)


if __name__ == "__main__":
    main()
