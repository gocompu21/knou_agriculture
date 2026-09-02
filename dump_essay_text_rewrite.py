"""필답 문제문 재서술용 배치 추출.

문제문을 베껴 쓴 티가 나지 않게 다듬기 위한 작업 파일을 만든다.
용어·수치·묻는 내용은 그대로 두고 어미·조사·문장 끊기만 바꾸는 것이 목적이라,
에이전트가 원문과 나란히 보며 판단할 수 있도록 원문을 그대로 담는다.
"""
import argparse, json, os, sys, django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from gisa.models import GisaEssayQuestion as Q

BATCH = 40   # 한 에이전트가 감당할 만한 크기


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out-dir', default='_essay_textrw')
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    # 회차·영역이 섞이지 않게 출처 단위로 묶어 순서대로 자른다
    qs = list(Q.objects.order_by('source', 'section', 'year', 'round', 'number'))

    batches, cur = [], []
    for q in qs:
        cur.append(q)
        if len(cur) >= BATCH:
            batches.append(cur); cur = []
    if cur:
        batches.append(cur)

    for i, group in enumerate(batches, 1):
        rows = [{
            'pk': q.pk,
            'label': f'{q.label} {q.number}번' if q.source == '기출' else f'{q.section} {q.number}',
            'qtype': q.qtype,
            'text': q.text or '',
            # 답을 함께 보여야 무엇을 묻는 문제인지 알고 문장을 다듬을 수 있다
            'answer_hint': (q.answer_items or [])[:3],
        } for q in group]
        p = os.path.join(args.out_dir, f'batch_{i:02d}.json')
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(rows, f, ensure_ascii=False, indent=1)
        print(f'{p}  {len(rows)}건')

    print(f'\n총 {len(batches)}배치 / {len(qs)}문항')


if __name__ == '__main__':
    main()
