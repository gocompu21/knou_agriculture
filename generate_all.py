"""모든 과목의 해설을 병렬로 생성하는 스크립트."""
import io
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# Windows CP949 인코딩 에러 방지
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# (과목명, 학년) 목록 — 동명 과목은 학년으로 구분
SUBJECTS = [
    ('글쓰기', 1), ('농학원론', 1), ('생물과학', 1), ('생활과건강', 1),
    ('세계의역사', 1), ('숲과삶', 1), ('심리학에게묻다', 1), ('원예학', 1),
    ('인간과과학', 1), ('인간과교육', 1), ('재배학원론', 1), ('축산학', 1),
    ('컴퓨터의이해', 1),
    ('농업생물화학', 2), ('농업유전학', 2), ('동서양고전의이해', 2),
    ('생활속의경제', 2), ('세상읽기와논술', 2), ('재배식물생리학', 2),
    ('철학의이해', 2), ('취미와예술', 2), ('한국사의이해', 2),
    ('글쓰기', 3), ('농축산환경학', 3), ('동물사료학', 3), ('생물통계학', 3),
    ('생활원예', 3), ('세상읽기와논술', 3), ('식물의학', 3), ('식용작물학1', 3),
    ('원예작물학1', 3), ('인간과교육', 3), ('자원식물학', 3), ('재배식물육종학', 3),
    ('토양학', 3), ('푸드마케팅', 3), ('환경친화형농업', 3),
    ('농업경영학', 4), ('농축산식품이용학', 4), ('생활과건강', 4),
    ('시설원예학', 4), ('식물분류학', 4), ('식용작물학2', 4),
    ('원예작물학2', 4), ('푸드마케팅', 4),
]

WORKERS = 45       # 동시 실행 수 (전과목 동시)
DELAY = 1.0        # API 호출 간 대기(초) — 45개 병렬이므로 넉넉하게
MODEL = 'gemini-2.5-flash'


def run_subject(name, grade):
    """한 과목의 해설 생성을 subprocess로 실행."""
    cmd = [
        sys.executable, 'manage.py', 'generate_explanations',
        '--subject', name, '--grade', str(grade),
        '--delay', str(DELAY), '--model', MODEL,
    ]
    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding='utf-8', errors='replace',
    )
    # 마지막 줄(완료 요약)만 반환
    lines = result.stdout.strip().split('\n')
    summary = lines[-1] if lines else '(no output)'
    return name, grade, summary, result.returncode


def main():
    print(f'=== 해설 생성 시작: {len(SUBJECTS)}개 과목, {WORKERS}개 병렬 ===\n')

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {
            executor.submit(run_subject, name, grade): (name, grade)
            for name, grade in SUBJECTS
        }

        done_count = 0
        for future in as_completed(futures):
            name, grade, summary, code = future.result()
            done_count += 1
            status = 'OK' if code == 0 else f'ERR({code})'
            print(f'[{done_count}/{len(SUBJECTS)}] [{grade}학년] {name}: {status} — {summary}')

    print(f'\n=== 완료: {done_count}개 과목 처리 ===')


if __name__ == '__main__':
    main()
