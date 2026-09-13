import sys
sys.stdout.reconfigure(encoding='utf-8')
import fitz
p = r"C:/Users/gocom/Documents/카카오톡 받은 파일/조경실기2_20260913 (1).pdf"
d = fitz.open(p)
print('fitz 쪽수:', len(d), '| 손상?', d.is_repaired if hasattr(d,'is_repaired') else '-')
print('첫 쪽 크기:', d[0].rect)
try:
    from pypdf import PdfReader
    print('pypdf 쪽수:', len(PdfReader(p).pages))
except Exception as e:
    print('pypdf 없음:', e)
