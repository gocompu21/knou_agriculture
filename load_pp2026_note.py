# -*- coding: utf-8 -*-
"""산업기사 2026-1회를 식물보호 실기 쪽집게 노트(`topics`)에 반영한다.

1. **신규 주제 3개 추가** — 유성포자·영양번식·불화수소. 출제가 한 번뿐이라
   빈도 규칙(2회 이상)으로는 노트에 오르지 못하므로 글을 써서 붙인다
   (`build_textbook` 은 정리 자료가 붙은 주제를 빈도와 무관하게 싣는다).
2. **모든 주제의 회차를 DB 와 맞춘다** — 주제키가 적힌 항목마다 `## N회` 와
   `**출제**` 줄을 `freq_rounds` 와 실제 출제 회차로 다시 쓴다. 회차가 늘 때마다
   손으로 고치다 보면 어긋난다(실제로 세 주제가 어긋난 채 남아 있었다).

    python load_pp2026_note.py            # 검증만
    python load_pp2026_note.py --apply    # DB 반영
"""
import os
import re
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.getcwd())
sys.stdout.reconfigure(encoding='utf-8')

import django  # noqa: E402

django.setup()

from gisa.models import Certification, GisaEssayNote, GisaEssayQuestion  # noqa: E402
from gisa.essay_topics import siblings  # noqa: E402

NEW = """
## 1회 · 식물병리 · 곰팡이의 유성포자와 무성포자

**출제** 2026-1
**주제키** 8849bcf1dbdb4f4e

### 개념
곰팡이의 **유성포자**는 **난포자·접합포자·자낭포자·담자포자**의 넷이고, **무성포자**는 유주포자·분생포자·포자낭포자·후막포자다. 유성포자가 무엇이냐가 곧 분류 체계여서, 난포자를 만들면 난균류, 접합포자면 접합균류, 자낭포자면 자낭균류, 담자포자면 담자균류다.

### 배경
두 갈래는 **하는 일이 다르다**. 유성포자는 두 핵이 만나 감수분열을 거치므로 유전적으로 다양한 자손을 만들고, 대개 두꺼운 벽을 지녀 불리한 계절을 넘긴다. 그래서 병환에서 유성포자는 흔히 **1차 전염원**이 된다 — 사과 검은별무늬병균이 떨어진 잎에서 자낭포자로 겨울을 나고 봄비에 날아 첫 감염을 일으키는 것이 전형이다.

무성포자는 감수분열 없이 빠르고 많이 만들어져 한 철에 여러 번 감염을 되풀이하는 **2차 전염원**이다. 유주포자는 꼬리(편모)가 있어 물속을 헤엄치므로 물이 많은 조건에서 번지는 난균류(역병·노균병)의 특징이 되고, 분생포자는 가장 흔한 무성포자로 바람에 날려 퍼진다. 후막포자는 벽이 두꺼워 무성포자이면서도 오래 견딘다.

곧 **"유성포자는 한 해를 넘기고, 무성포자는 한 철에 번진다"**로 잡아 두면 두 갈래가 헷갈리지 않는다. **불완전균류**는 유성세대가 아직 밝혀지지 않아 분생포자만 알려진 무리를 가리키는 편의적인 분류다.

### 시험에서는
"유성포자 3가지"를 물었으므로 넷 가운데 셋만 쓰면 된다. 난포자·자낭포자·담자포자가 가장 무난하다. 유성포자와 무성포자를 바꿔 내거나, 포자 이름을 주고 어느 분류군인지 묻는 꼴로도 나오므로 **포자 ↔ 분류군**의 짝을 통째로 외운다.

## 1회 · 관개·재배관리 · 영양번식

**출제** 2026-1
**주제키** 4fc013b1c631f1dc

### 개념
**영양번식(무성번식)**은 씨앗이 아니라 잎·줄기·뿌리 같은 **영양기관의 일부**로 새 개체를 얻는 번식 방법이다. 어버이와 유전적으로 똑같은 개체(클론)를 얻는다는 것이 가장 큰 특징이다.

### 배경
값어치는 **형질이 그대로 이어진다**는 데 있다. 씨앗으로 심으면 감수분열과 수정을 거치며 형질이 흩어져 같은 품종이 나오지 않지만, 가지를 잘라 꽂으면 어버이와 똑같은 나무가 된다. 사과·배·포도 같은 과수와 감자·고구마·마늘, 국화·카네이션이 모두 영양번식으로 이어지는 까닭이다. 씨앗이 잘 맺히지 않거나 발아가 어려운 작물을 늘리는 길이기도 하고, 어린 시기를 건너뛰어 **일찍 꽃이 피고 열매가 달린다**는 이점도 크다.

방법은 **분주(포기나누기)·삽목(꺾꽂이)·접목(접붙이기)·취목(휘묻이)**이 기본이고 여기에 조직배양이 더해진다. 접목은 뿌리를 맡는 **대목**과 열매를 맡는 **접수**를 따로 골라, 대목으로 토양병과 선충에 견디게 하거나 나무 크기를 줄인다(왜성대목).

약점도 분명하다. 개체들이 유전적으로 똑같아 **한 병해가 돌면 통째로 무너지고**, 바이러스처럼 모주에 든 병원체가 그대로 이어진다. 그래서 생장점 배양으로 **무병주(virus-free)**를 만들어 보급한다.

### 시험에서는
정의를 쓰는 서술형이다. **'종자가 아닌 영양기관으로'**와 **'어버이와 같은 형질(클론)'** 두 가지가 들어가야 온전한 답이 된다. 네 가지 방법을 함께 쓰라고 할 수 있으니 분주·삽목·접목·취목을 붙여 외운다.

## 1회 · 광·온도·대기 · 불화수소(HF)에 강한 식물과 약한 식물

**출제** 2026-1
**주제키** 744b15a62b0f8846

### 개념
불화수소(HF)에 **강한 식물**은 목화·단풍나무·배나무·담배·콩이고, **약한(민감한) 식물**은 글라디올러스·옥수수·자두·살구나무·복숭아나무·포도나무다. 민감한 종은 오염을 알아내는 **지표식물**로 쓴다.

### 배경
HF는 대기오염물질 가운데 **가장 낮은 농도에서 피해를 내는** 물질이다. 아황산가스가 ppm 단위에서 문제가 되는 데 견주어 HF는 **ppb(10억분율) 단위**에서도 피해가 나타나며, 알루미늄 제련·유리·벽돌·인산비료 공장 둘레에서 문제가 된다.

피해 증상이 독특해 진단의 열쇠가 된다. 기공으로 들어온 불소는 증산류를 타고 **잎 끝과 가장자리에 쌓이므로**, 그 부분이 갈색으로 타 들어가고 건전부와의 경계에 짙은 띠가 생긴다. 잎맥 사이가 표백되는 아황산가스 피해, 잎 뒷면이 은백색으로 변하는 오존 피해, 잎 뒷면에 광택 있는 반점이 생기는 PAN 피해와 이 점에서 갈린다.

과수 가운데 **핵과류(살구·복숭아·자두)가 특히 약하다**는 점을 묶어 두면 보기에서 고르기 쉽다. 글라디올러스는 국제적으로 쓰이는 HF 지표식물이다.

### 시험에서는
보기를 주고 강한 것 또는 약한 것을 고르게 한다(26-1회 산업기사는 강한 것 2가지). 오염물질별 지표식물을 묶어 물을 수도 있으니 함께 외운다 — **아황산가스는 알팔파·메밀, 오존은 담배·시금치, PAN은 강낭콩·페튜니아, 불화수소는 글라디올러스·옥수수**다.
"""


def main():
    apply_ = '--apply' in sys.argv
    note = GisaEssayNote.objects.get(certification__name='식물보호기사', slug='topics')
    text = note.content

    added = [k for k in re.findall(r'^\*\*주제키\*\* ([0-9a-f]+)$', NEW, flags=re.M)
             if k not in text]
    if added:
        text = text.rstrip() + '\n' + NEW.rstrip() + '\n'
    print('정리 글 추가:', len(added), '주제', added)

    # 주제키가 적힌 항목마다 회차를 DB 와 맞춘다. 손으로 고치다 보면 어긋난다.
    pool = list(Certification.objects.filter(name__in=siblings('식물보호기사')))
    lines = text.split('\n')
    fixed = 0
    for i, ln in enumerate(lines):
        m = re.match(r'^\*\*주제키\*\* ([0-9a-f]+)$', ln.strip())
        if not m:
            continue
        key = m.group(1)
        qs = GisaEssayQuestion.objects.filter(certification__in=pool,
                                              source='기출', topic_key=key)
        if not qs.exists():
            print('DB 에 없는 주제키:', key)
            return 1
        # 회차 목록은 급수를 합쳐 **연도-회차로 중복을 지운다**(노트의 종전 표기법)
        rounds = sorted({(q.year, q.round) for q in qs}, reverse=True)
        freq = max(q.freq_rounds for q in qs)
        head = next(j for j in range(i, -1, -1) if lines[j].startswith('## '))
        out = next(j for j in range(head, i) if lines[j].startswith('**출제** '))
        new_head = re.sub(r'^## \d+회', '## %d회' % freq, lines[head])
        new_out = '**출제** ' + ' '.join('%d-%d' % r for r in rounds)
        if new_head != lines[head] or new_out != lines[out]:
            fixed += 1
            print(f'{key} {lines[head][3:].split("·")[0].strip()} → {freq}회 '
                  f'| {lines[head][3:][:40]}')
            lines[head], lines[out] = new_head, new_out
    text = '\n'.join(lines)
    print('회차 갱신:', fixed, '주제')

    print(f'\n{len(note.content):,}자 → {len(text):,}자')
    if not apply_:
        print('(검증만 했다. --apply 를 붙여야 DB 에 들어간다)')
        return 0
    note.content = text
    note.save(update_fields=['content', 'updated_at'])
    print('반영했다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
