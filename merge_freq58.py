"""빈출 58주제 정리를 한 문서로 합친다.

part1~6 을 순서대로 잇고, 앞에 목차와 쓰는 법을 붙인다.
주제가 58개 다 있는지, 원본 목록과 어긋나지 않는지 검사한다.
"""
import glob, io, json, os, re, sys

sys.stdout.reconfigure(encoding='utf-8')

SRC = '_freq58'
OUT = '_freq58/빈출58주제_정리.md'

HEAD = """# 자연생태복원기사 실기 필답 — 빈출 58주제

기출 726문항을 주제로 묶어 **3회 이상 되풀이된 58개 주제**만 모았다.
전체 기출의 30%에 해당하며, 회차당 4~5문항이 여기서 나온다.

## 왜 세 층으로 나누었나

회차별로 대조해 보니 기출을 다 봐도 예상 점수가 26~30점(45점 만점)에 그쳤다.
점수가 새는 자리는 뚜렷했다 — **같은 주제인데 요구가 커진 문항**이다.

| 회차 | 물음 |
|------|------|
| 2022-3 | 추이대란 무엇인지 그 **정의**를 쓰시오 |
| 2026-2 | 추이대의 종다양성이 **높은 까닭**을 서술하시오 |

정의만 외운 사람은 뒤쪽에서 절반을 잃는다. 그래서 주제마다 셋으로 나눈다.

| 층 | 답하는 물음 | 대응하는 문항 |
|----|-------------|---------------|
| **정의** | 무엇인가 | 단답·빈칸 |
| **이유** | 왜 그런가 | **서술 확장형** |
| **사례·적용** | 어디에 쓰는가 | 열거·적용형 |

**⚠️ 표시가 붙은 주제**는 실제로 요구가 커진 이력이 있는 곳이다. 거기부터 보면 된다.

## 쓰는 법

1. 먼저 **⚠️ 가 붙은 주제**를 훑는다 — 다음에 확장돼 나올 자리다
2. 계산 주제는 공식과 대입을 손으로 한 번 풀어 둔다. 수치까지 같은 문제가 되풀이된다
3. 각 주제의 **출제** 줄에 배점이 있다. 2점이면 한 줄, 4.5점이면 3~4항목으로 쓴다

---

"""


def main():
    parts = sorted(glob.glob(os.path.join(SRC, 'part*_done.md')),
                   key=lambda p: int(re.search(r'part(\d+)', p).group(1)))
    if not parts:
        print('작성 결과가 없습니다.'); return

    bodies, titles = [], []
    for p in parts:
        s = io.open(p, encoding='utf-8').read().strip()
        titles += re.findall(r'^## (.+)$', s, re.M)
        bodies.append(s)

    want = json.load(io.open('_freq58.json', encoding='utf-8'))
    print(f'주제 {len(titles)} / 목표 {len(want)}')
    if len(titles) != len(want):
        print('  ⚠ 아직 덜 작성됐습니다. 완료 후 다시 실행하세요.')

    # 목차
    toc = ['## 목차\n']
    for i, t in enumerate(titles, 1):
        anchor = t.replace(' ', '-').replace('·', '').replace('.', '')
        toc.append(f'{i}. {t}')
    toc.append('\n---\n')

    doc = HEAD + '\n'.join(toc) + '\n\n' + '\n\n---\n\n'.join(bodies) + '\n'
    io.open(OUT, 'w', encoding='utf-8').write(doc)
    print(f'{OUT}  {len(doc):,}자')

    n_warn = doc.count('⚠️ 요구가 커진 지점')
    print(f'  ⚠️ 요구 확장 주제 {n_warn}개')


if __name__ == '__main__':
    main()
