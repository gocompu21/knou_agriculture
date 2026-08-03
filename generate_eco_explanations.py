"""자연생태복원기사 3,160문제 해설을 병렬로 생성하는 스크립트.

회차·과목 목록은 DB에서 자동으로 읽는다(2022년 4과목 개편 자동 반영).

사용법:
    python generate_eco_explanations.py              # 해설 없는 문제만
    python generate_eco_explanations.py --force      # 기존 해설 덮어쓰기
    python generate_eco_explanations.py --year 2012  # 특정 연도만
"""
import io
import os
import sys
import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

CERT = '자연생태복원기사'
WORKERS = 40          # 동시 실행 수 (PostgreSQL 커넥션 한도 고려)
DELAY = 0.5           # API 호출 간격(초)
MODEL = 'gemini-3-flash-preview'


def load_units(year_filter=None):
    """DB에서 (연도, 회차, 과목) 단위 목록을 만든다. 해설이 필요한 것만."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    import django
    django.setup()
    from gisa.models import GisaQuestion

    qs = GisaQuestion.objects.filter(exam__certification__name=CERT)
    if year_filter:
        qs = qs.filter(exam__year=year_filter)

    rows = (qs.values('exam__year', 'exam__round', 'subject__name')
              .distinct()
              .order_by('exam__year', 'exam__round', 'subject__name'))
    return [(r['exam__year'], r['exam__round'], r['subject__name']) for r in rows]


def run_task(year, round_num, subject, force):
    cmd = [
        sys.executable, 'manage.py', 'generate_gisa_explanations',
        '--cert', CERT, '--subject', subject,
        '--year', str(year), '--round', str(round_num),
        '--delay', str(DELAY), '--model', MODEL,
    ]
    if force:
        cmd.append('--force')
    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding='utf-8', errors='replace',
    )
    lines = (result.stdout or '').strip().split('\n')
    summary = lines[-1] if lines and lines[-1] else '(no output)'
    if result.returncode != 0:
        err = (result.stderr or '').strip().split('\n')
        summary = (err[-1] if err else summary)[:150]
    return year, round_num, subject, summary, result.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--force', action='store_true', help='기존 해설 덮어쓰기')
    ap.add_argument('--year', type=int, help='특정 연도만')
    ap.add_argument('--workers', type=int, default=WORKERS)
    args = ap.parse_args()

    tasks = load_units(args.year)
    if not tasks:
        print('대상 없음')
        return

    print('=== %s 해설 생성: %d개 단위, %d개 병렬 (model=%s) ===\n'
          % (CERT, len(tasks), args.workers, MODEL), flush=True)

    ok = err = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {
            ex.submit(run_task, y, r, s, args.force): (y, r, s)
            for y, r, s in tasks
        }
        done = 0
        for fut in as_completed(futures):
            year, rnd, subj, summary, code = fut.result()
            done += 1
            if code == 0:
                ok += 1
                status = 'OK'
            else:
                err += 1
                status = 'ERR(%d)' % code
            print('[%d/%d] %d-%d %s: %s — %s'
                  % (done, len(tasks), year, rnd, subj, status, summary), flush=True)

    print('\n=== 완료: 성공 %d / 실패 %d (총 %d) ===' % (ok, err, len(tasks)))
    if err:
        print('실패분은 다시 실행하면 남은 문제만 처리됩니다.')


if __name__ == '__main__':
    main()
