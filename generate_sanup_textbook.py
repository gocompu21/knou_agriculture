"""Gemini API로 식물보호산업기사 쪽집게 노트를 생성하는 스크립트.

사용법:
    python generate_sanup_textbook.py --subject 식물병리학 --step classify
    python generate_sanup_textbook.py --subject 해충학 --step generate --parallel
    python generate_sanup_textbook.py --subject 해충학 --step verify
    python generate_sanup_textbook.py --subject 해충학 --step save
    python generate_sanup_textbook.py --subject 해충학 --step all --parallel
"""
import io
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings
from google import genai
from pydantic import BaseModel, Field

MODEL = 'gemini-3.1-pro-preview'
CERT_ID = 2  # 식물보호산업기사

# 과목별 설정
SUBJECT_CONFIG = {
    '식물병리학': {'subject_id': 6, 'prefix': 'sanup_pathology'},
    '해충학':     {'subject_id': 7, 'prefix': 'sanup_entomology'},
    '농약학':     {'subject_id': 8, 'prefix': 'sanup_pesticide'},
    '잡초방제학': {'subject_id': 9, 'prefix': 'sanup_weed'},
}


def get_paths(subject_name):
    cfg = SUBJECT_CONFIG[subject_name]
    prefix = cfg['prefix']
    return {
        'subject_id': cfg['subject_id'],
        'questions_file': f'data/{prefix}_questions.json',
        'chapters_file': f'data/{prefix}_chapters.json',
        'output_dir': f'data/{prefix}_notes',
    }


def create_client():
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")
    return genai.Client(api_key=api_key)


def load_questions(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ── Step 1: 챕터 분류 ──────────────────────────────────────────────

class ChapterItem(BaseModel):
    title: str = Field(description="챕터 제목 (예: 제1장. 식물병의 기초 개념)")
    questions: list[str] = Field(description="해당 챕터에 배정된 문제 참조 목록 (YYYY-R-N 형식)")


class ChapterClassification(BaseModel):
    chapters: list[ChapterItem] = Field(description="챕터 목록")


def step_classify(subject_name, paths):
    client = create_client()
    questions = load_questions(paths['questions_file'])

    q_list = []
    for q in questions:
        ref = f"{q['year']}-{q['round']}-{q['number']}"
        q_list.append(f"[{ref}] {q['text']} ①{q['c1']} ②{q['c2']} ③{q['c3']} ④{q['c4']}")

    prompt = f"""당신은 식물보호산업기사 시험 전문가이다.
아래는 식물보호산업기사 {subject_name} 기출문제 {len(questions)}문항이다.

이 문제들을 분석하여 10~15개의 챕터(장)로 분류하라.

규칙:
1. 각 챕터는 시험에서 반복 출제되는 핵심 주제를 기준으로 구성
2. 챕터 제목은 "제N장. 제목" 형식 (예: "제1장. 곤충의 외부 형태")
3. 모든 {len(questions)}문제가 반드시 하나의 챕터에 배정되어야 함 (누락 없이)
4. 각 챕터에 해당 문제의 참조번호(YYYY-R-N)를 배정
5. 비슷한 주제의 문제는 같은 챕터로 묶을 것
6. 챕터 순서는 기초 → 심화 순으로 배치

문제 목록:
{chr(10).join(q_list)}

JSON 형식으로 응답하라."""

    print(f'[{subject_name}] 챕터 분류 요청 중... ({len(questions)}문제, 모델: {MODEL})')
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": ChapterClassification,
        },
    )
    result = ChapterClassification.model_validate_json(response.text)

    with open(paths['chapters_file'], 'w', encoding='utf-8') as f:
        json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)

    total_assigned = sum(len(ch.questions) for ch in result.chapters)
    print(f'\n분류 완료: {len(result.chapters)}개 챕터, {total_assigned}/{len(questions)}문제 배정')
    for i, ch in enumerate(result.chapters, 1):
        print(f'  {ch.title}: {len(ch.questions)}문제')

    if total_assigned < len(questions):
        print(f'\n⚠️ {len(questions) - total_assigned}문제 누락!')


# ── Step 2: 장별 노트 생성 ─────────────────────────────────────────

def _generate_one_chapter(client, subject_name, ch, ch_idx, total, q_map, output_dir):
    """단일 챕터 노트 생성 (병렬 호출용)."""
    output_file = os.path.join(output_dir, f'ch{ch_idx:02d}.md')
    if os.path.exists(output_file):
        print(f'[{ch_idx}/{total}] {ch["title"]} — 이미 존재, 건너뜀')
        return ch_idx, 'skipped'

    ch_questions = []
    for ref in ch['questions']:
        if ref in q_map:
            q = q_map[ref]
            ch_questions.append(
                f"[{ref}] {q['text']}\n  ①{q['c1']} ②{q['c2']} ③{q['c3']} ④{q['c4']}\n  정답: {q['answer']}"
            )

    ch_num = ch_idx
    prompt = f"""당신은 식물보호산업기사 시험 전문 교수이다.
아래는 "{ch['title']}" 범주에 해당하는 기출문제 {len(ch_questions)}문항이다.

이 문제들의 핵심 내용을 바탕으로 **교재형 학습 노트**를 작성하라.

작성 규칙:
1. 마크다운 형식: `## {ch['title']}` 로 시작
2. 절 제목: `### {ch_num}.M 절제목` (예: ### {ch_num}.1 곤충의 머리)
3. 필요시 항 제목: `#### {ch_num}.M.K 항제목`
4. **교재형 서술문** 스타일 — 불렛(-)은 열거가 필요한 곳만 사용, 나머지는 자연스러운 문장 서술
5. 핵심 용어는 **볼드** 처리
6. 각 절 끝에 반드시 `**관련 문제**: (YYYY-R-N), (YYYY-R-N)` 형식으로 관련 문제 참조 추가
7. 장 끝에 `### 핵심 키워드 요약` 테이블 추가 (| 키워드 | 핵심 포인트 |)
8. 시험에 나올 수 있는 핵심 내용을 빠짐없이 포함
9. 문제에서 다루는 모든 개념, 용어, 분류체계를 노트에 반영
10. 공부팁, 인사말, 머리말 없이 본문만 작성

기출문제:
{chr(10).join(ch_questions)}
"""

    print(f'[{ch_idx}/{total}] {ch["title"]} ({len(ch_questions)}문제) 생성 중...', flush=True)
    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
        content = response.text
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        lines = content.count('\n') + 1
        print(f'[{ch_idx}/{total}] {ch["title"]} — OK ({lines}줄)')
        return ch_idx, 'ok'
    except Exception as e:
        print(f'[{ch_idx}/{total}] {ch["title"]} — 실패: {e}')
        return ch_idx, f'fail: {e}'


def step_generate(subject_name, paths, parallel=False):
    client = create_client()
    questions = load_questions(paths['questions_file'])

    with open(paths['chapters_file'], 'r', encoding='utf-8') as f:
        chapters_data = json.load(f)

    chapters = chapters_data['chapters']
    os.makedirs(paths['output_dir'], exist_ok=True)

    q_map = {}
    for q in questions:
        ref = f"{q['year']}-{q['round']}-{q['number']}"
        q_map[ref] = q

    if parallel:
        print(f'[{subject_name}] 병렬 생성 모드 ({len(chapters)}장, workers=20)')
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {}
            for i, ch in enumerate(chapters, 1):
                fut = executor.submit(
                    _generate_one_chapter, client, subject_name,
                    ch, i, len(chapters), q_map, paths['output_dir']
                )
                futures[fut] = i

            for fut in as_completed(futures):
                ch_idx, status = fut.result()
    else:
        for i, ch in enumerate(chapters, 1):
            _generate_one_chapter(client, subject_name, ch, i, len(chapters), q_map, paths['output_dir'])
            if i < len(chapters):
                time.sleep(2)

    print(f'\n[{subject_name}] 노트 생성 완료. 파일: {paths["output_dir"]}/')


# ── Step 3: 커버리지 보완 ──────────────────────────────────────────

def step_verify(subject_name, paths):
    client = create_client()
    questions = load_questions(paths['questions_file'])

    q_map = {}
    all_refs = set()
    for q in questions:
        ref = f"{q['year']}-{q['round']}-{q['number']}"
        all_refs.add(ref)
        q_map[ref] = q

    note_refs = set()
    for fname in sorted(os.listdir(paths['output_dir'])):
        if not fname.endswith('.md'):
            continue
        with open(os.path.join(paths['output_dir'], fname), 'r', encoding='utf-8') as f:
            content = f.read()
        refs = re.findall(r'\((\d{4}-\d+-\d+)\)', content)
        note_refs.update(refs)

    missing = sorted(all_refs - note_refs)
    print(f'[{subject_name}] 커버리지: {len(note_refs)}/{len(all_refs)} ({len(note_refs)/len(all_refs)*100:.1f}%)')
    print(f'[{subject_name}] 누락 문제: {len(missing)}개')

    if not missing:
        print(f'[{subject_name}] 보완 불필요!')
        return

    supplement_file = os.path.join(paths['output_dir'], 'supplement.md')
    if os.path.exists(supplement_file):
        print(f'[{subject_name}] 보완 파일 이미 존재: {supplement_file}')
        return

    missing_questions = []
    for ref in missing:
        if ref in q_map:
            q = q_map[ref]
            missing_questions.append(
                f"[{ref}] {q['text']}\n  ①{q['c1']} ②{q['c2']} ③{q['c3']} ④{q['c4']}\n  정답: {q['answer']}"
            )

    prompt = f"""당신은 식물보호산업기사 시험 전문 교수이다.
아래는 기존 학습 노트에서 누락된 기출문제 {len(missing_questions)}문항이다.

이 문제들의 핵심 내용을 기존 장(chapter)의 보충 자료로 작성하라.

작성 규칙:
1. `## 보충 학습 자료` 로 시작
2. 주제별로 `### 보충 N. 주제명` 으로 그룹화
3. **교재형 서술문** 스타일 — 불렛(-)은 열거가 필요한 곳만 사용
4. 핵심 용어는 **볼드** 처리
5. 각 주제 끝에 반드시 `**관련 문제**: (YYYY-R-N), (YYYY-R-N)` 형식으로 관련 문제 참조 추가
6. 모든 {len(missing_questions)}문항의 참조번호가 반드시 포함되어야 함 (누락 금지)
7. 공부팁, 인사말 없이 본문만 작성

누락 기출문제:
{chr(10).join(missing_questions)}
"""

    print(f'[{subject_name}] 보완 노트 생성 중 ({len(missing_questions)}문제)...', end='', flush=True)
    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
        content = response.text
        with open(supplement_file, 'w', encoding='utf-8') as f:
            f.write(content)
        new_refs = re.findall(r'\((\d{4}-\d+-\d+)\)', content)
        covered = set(new_refs) & set(missing)
        still_missing = set(missing) - set(new_refs)
        lines = content.count('\n') + 1
        print(f' OK ({lines}줄)')
        print(f'[{subject_name}] 보완 결과: {len(covered)}/{len(missing)}개 커버')
        if still_missing:
            print(f'[{subject_name}] 여전히 누락: {len(still_missing)}개')
    except Exception as e:
        print(f' 실패: {e}')


# ── Step 4: DB 저장 ────────────────────────────────────────────────

def step_save(subject_name, paths):
    from gisa.models import GisaTextbook, Certification, GisaSubject

    cert = Certification.objects.get(pk=CERT_ID)
    subject = GisaSubject.objects.get(pk=paths['subject_id'])

    parts = []
    parts.append(f'# {subject_name} 핵심정리\n')
    parts.append(f'> 식물보호산업기사 기출문제 720문항(2002~2020) 기반 학습 교재\n')
    parts.append('---\n')

    md_files = sorted(
        f for f in os.listdir(paths['output_dir']) if f.endswith('.md')
    )

    for fname in md_files:
        filepath = os.path.join(paths['output_dir'], fname)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        parts.append(content)
        parts.append('\n---\n')

    full_content = '\n'.join(parts)
    lines = full_content.count('\n') + 1

    obj, created = GisaTextbook.objects.update_or_create(
        certification=cert,
        subject=subject,
        defaults={'content': full_content},
    )

    action = '생성' if created else '업데이트'
    print(f'[{subject_name}] GisaTextbook {action} 완료 ({lines}줄)')

    refs = re.findall(r'\((\d{4}-\d+-\d+)\)', full_content)
    unique_refs = set(refs)
    print(f'[{subject_name}] 관련 문제 참조: {len(unique_refs)}개 고유 참조')


# ── Main ────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Gemini API로 쪽집게 노트 생성')
    parser.add_argument('--subject', required=True, choices=list(SUBJECT_CONFIG.keys()))
    parser.add_argument('--step', choices=['classify', 'generate', 'verify', 'save', 'all'], default='all')
    parser.add_argument('--parallel', action='store_true', help='장별 노트를 병렬로 생성')
    args = parser.parse_args()

    subject_name = args.subject
    paths = get_paths(subject_name)

    if args.step in ('classify', 'all'):
        step_classify(subject_name, paths)
    if args.step in ('generate', 'all'):
        step_generate(subject_name, paths, parallel=args.parallel)
    if args.step in ('verify', 'all'):
        step_verify(subject_name, paths)
    if args.step in ('save', 'all'):
        step_save(subject_name, paths)


if __name__ == '__main__':
    main()
