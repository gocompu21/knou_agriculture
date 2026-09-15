# -*- coding: utf-8 -*-
"""조경 실기 쪽집게 노트의 주제별 정리글(`topics`)을 조립·검증해 넣는다.

분류별로 따로 쓴 파일(`_ls_note/g4.md` …)을 이어 붙이되, 머리글이 DB 와 맞는지
하나라도 어긋나면 넣지 않는다 — 눈으로는 못 잡는 종류의 실수다.

  - `## N회 · 분류 · 제목` 의 N 이 그 주제의 기출 시험지 수와 같은가
  - 분류 이름·제목이 `_ls_topics.json` 과 같은가
  - `**주제키**` 가 실제 문항에 달린 키인가, 한 주제가 두 번 나오지 않는가

  python load_ls_topics_note.py            # 검사 + _ls_topics_note.md 생성
  python load_ls_topics_note.py --apply    # 위 + GisaEssayNote(조경기사, slug=topics) 갱신

노트는 조경기사에만 단다. `build_textbook` 이 묶음(조경산업기사 포함)의 노트를
모두 읽으므로 산업기사 화면에도 같은 주제가 나온다. 분류 파일을 추가하면
PARTS 에 넣고 다시 돌린다.
"""
import hashlib
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django  # noqa: E402

django.setup()

from gisa.models import Certification, GisaEssayNote, GisaEssayQuestion  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS_DIR = os.path.join(HERE, '_ls_note')
OUT = os.path.join(HERE, '_ls_topics_note.md')

INTRO = """# 조경(산업)기사 실기 — 주제별 학습 정리

2023~2026년 필답형 기출(조경기사·조경산업기사)과 학원예상 문항을 **같은 기준표·같은
공식을 묻는 주제**로 묶어 정리했습니다. 조경 실기는 한 번 나온 기준표에서 **다른 칸**이
다음 시험에 나오는 일이 잦으므로, 기출에 나온 칸만이 아니라 표 전체를 함께 봅니다.

주제 머리의 회수는 그 주제가 나온 **기출 시험지 수**(기사·산업기사 합산)이고, 학원예상
문항은 회수에 넣지 않고 주제 안에 함께 펼쳐 둡니다.
"""


def main():
    apply_ = '--apply' in sys.argv
    data = json.load(io.open(os.path.join(HERE, '_ls_topics.json'), encoding='utf-8'))
    gname = dict(data['groups'])
    by_key = {}
    for t in data['topics']:
        by_key[hashlib.md5(t['id'].encode('utf-8')).hexdigest()[:16]] = t

    parts = sorted(f for f in os.listdir(PARTS_DIR) if re.fullmatch(r'g\d+\.md', f))
    head_re = re.compile(r'^## (\d+)회 · (.+?) · (.+)$', re.M)
    errors, seen, blocks = [], set(), []
    for fn in parts:
        text = io.open(os.path.join(PARTS_DIR, fn), encoding='utf-8').read().strip()
        chunks = re.split(r'(?=^## \d+회 · )', text, flags=re.M)
        if chunks and not chunks[0].startswith('## '):
            if chunks[0].strip():
                errors.append(f'{fn}: 첫 주제 앞에 다른 글이 있다')
            chunks = chunks[1:]
        for ch in chunks:
            m = head_re.match(ch)
            km = re.search(r'^\*\*주제키\*\*\s*([0-9a-f]{16})\s*$', ch, re.M)
            if not (m and km):
                errors.append(f'{fn}: 머리글·주제키를 읽지 못함 — {ch[:40]!r}')
                continue
            freq, group, title = int(m.group(1)), m.group(2), m.group(3).strip()
            key = km.group(1)
            t = by_key.get(key)
            if not t:
                errors.append(f'{fn}: 모르는 주제키 {key} ({title})')
                continue
            if key in seen:
                errors.append(f'{fn}: 주제 중복 {title}')
            seen.add(key)
            real = len({(q.certification_id, q.year, q.round) for q in
                        GisaEssayQuestion.objects.filter(topic_key=key, source='기출')})
            if not GisaEssayQuestion.objects.filter(topic_key=key).exists():
                errors.append(f'{fn}: 문항에 달리지 않은 주제키 {key} — load_ls_topics.py --apply 먼저')
            if freq != real:
                errors.append(f'{fn}: {title} 회수 {freq} ≠ 시험지 {real}')
            if group != gname[t['g']]:
                errors.append(f'{fn}: {title} 분류 {group} ≠ {gname[t["g"]]}')
            if title != t['title']:
                errors.append(f'{fn}: 제목 다름 {title!r} ≠ {t["title"]!r}')
            for sec in ('### 핵심 정리', '### 왜 그런가', '### 시험에서는'):
                if sec not in ch:
                    errors.append(f'{fn}: {title} — "{sec}" 절이 없다')
            if '$' in ch:
                errors.append(f'{fn}: {title} — LaTeX($) 가 남아 있다')
            blocks.append(ch.strip())

    if errors:
        print('\n'.join(errors))
        return 1

    content = INTRO.strip() + '\n\n' + '\n\n'.join(blocks) + '\n'
    with io.open(OUT, 'w', encoding='utf-8') as f:
        f.write(content)
    covered = {}
    for k in seen:
        covered.setdefault(gname[by_key[k]['g']], 0)
        covered[gname[by_key[k]['g']]] += 1
    print(f'주제 {len(blocks)}개 · {len(content):,}자 → {os.path.basename(OUT)}')
    for g, n in covered.items():
        total = sum(1 for t in data['topics'] if gname[t['g']] == g)
        print(f'  {g}: {n}/{total}')

    if apply_:
        cert = Certification.objects.get(name='조경기사')
        note, created = GisaEssayNote.objects.update_or_create(
            certification=cert, slug='topics',
            defaults={'title': '주제별 학습 정리', 'content': content, 'order': 1,
                      'summary': '기출·학원예상을 기준표·공식 단위로 묶은 정리'})
        print('노트 %s' % ('생성' if created else '갱신'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
