# -*- coding: utf-8 -*-
"""원본 PDF에서 특정 문항의 텍스트를 뽑아 DB 값과 대조한다.

comcbt PDF(2012~2022)는 텍스트 레이어가 있어 정확한 대조가 된다.
문제·보기 교정에서 판단이 갈렸던 항목의 근거를 확인하는 데 쓴다.

사용법:
    python check_pdf.py 2016-3 53
    python check_pdf.py 2017-2 88 --raw
"""
import io, os, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import GisaQuestion

import fitz

PDF_DIR = "data/comcbt"


def load_pdf_text(round_key):
    path = os.path.join(PDF_DIR, "자연생태복원기사%s.pdf" % round_key)
    if not os.path.exists(path):
        return None, path
    doc = fitz.open(path)
    text = "\n".join(p.get_text() for p in doc)
    doc.close()
    return text, path


def find_question(text, num):
    """문항번호로 시작하는 블록을 잘라낸다."""
    # "53. " 또는 "53 " 로 시작하는 줄부터 다음 번호 직전까지
    pat = re.compile(r"(?m)^\s*%d\s*[.．]\s*(.+?)(?=^\s*%d\s*[.．]\s)" % (num, num + 1), re.S)
    m = pat.search(text)
    if m:
        return m.group(0)
    # 마지막 문항이면 뒤가 없다
    pat2 = re.compile(r"(?m)^\s*%d\s*[.．]\s*(.{0,700})" % num, re.S)
    m2 = pat2.search(text)
    return m2.group(0) if m2 else None


def main():
    if len(sys.argv) < 3:
        print("사용법: python check_pdf.py <회차> <문항번호>")
        print("  예:   python check_pdf.py 2016-3 53")
        return
    rk, num = sys.argv[1], int(sys.argv[2])
    y, r = (int(x) for x in rk.split("-"))

    text, path = load_pdf_text(rk)
    if text is None:
        print("PDF 없음:", path)
        return

    q = GisaQuestion.objects.filter(
        exam__certification__name="자연생태복원기사",
        exam__year=y, exam__round=r, number=num).first()

    print("=" * 66)
    print("PDF: %s" % os.path.basename(path))
    print("=" * 66)
    blk = find_question(text, num)
    if blk:
        print(re.sub(r"\n{2,}", "\n", blk.strip())[:900])
    else:
        print("(문항 블록을 못 찾음 — --raw 로 전체 검색)")

    if q:
        print()
        print("-" * 66)
        print("DB 현재값")
        print("-" * 66)
        print("문제:", q.text)
        for i in range(1, 5):
            print("  %d) %s" % (i, getattr(q, "choice_%d" % i)))
        print("정답:", q.answer)


main()
