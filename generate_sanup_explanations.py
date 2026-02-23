"""식물보호산업기사 2,880문제 해설을 병렬로 생성하는 스크립트."""
import io
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

CERT = '식물보호산업기사'
WORKERS = 100
DELAY = 0.3
MODEL = 'gemini-2.5-flash'

# 36회차 × 4과목 = 144 단위
EXAMS = [
    (2002, 1), (2002, 4), (2003, 1), (2003, 4), (2004, 1), (2004, 4),
    (2005, 1), (2005, 2), (2005, 4), (2006, 1), (2006, 4), (2007, 1),
    (2008, 1), (2008, 4), (2009, 4), (2010, 4), (2011, 1), (2011, 4),
    (2012, 1), (2012, 4), (2013, 4), (2014, 4), (2015, 1), (2015, 4),
    (2016, 1), (2016, 4), (2017, 1), (2017, 4), (2018, 1), (2018, 2),
    (2018, 4), (2019, 1), (2019, 2), (2019, 4), (2020, 2), (2020, 3),
]

SUBJECTS = ['식물병리학', '해충학', '농약학', '잡초방제학']


def run_task(year, round_num, subject):
    cmd = [
        sys.executable, 'manage.py', 'generate_gisa_explanations',
        '--cert', CERT, '--subject', subject,
        '--year', str(year), '--round', str(round_num),
        '--delay', str(DELAY), '--model', MODEL,
    ]
    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding='utf-8', errors='replace',
    )
    lines = result.stdout.strip().split('\n')
    summary = lines[-1] if lines else '(no output)'
    return year, round_num, subject, summary, result.returncode


def main():
    tasks = [(y, r, s) for y, r in EXAMS for s in SUBJECTS]
    print(f'=== 식물보호산업기사 해설 생성: {len(tasks)}개 단위, {WORKERS}개 병렬 ===\n', flush=True)

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {
            executor.submit(run_task, y, r, s): (y, r, s)
            for y, r, s in tasks
        }

        done = 0
        for future in as_completed(futures):
            year, rnd, subj, summary, code = future.result()
            done += 1
            status = 'OK' if code == 0 else f'ERR({code})'
            print(f'[{done}/{len(tasks)}] {year}-{rnd} {subj}: {status} — {summary}', flush=True)

    print(f'\n=== 완료: {done}/{len(tasks)} ===')


if __name__ == '__main__':
    main()
