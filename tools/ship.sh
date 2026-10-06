#!/usr/bin/env bash
# 고친 것을 한 번에 내보낸다 — 검사 → 커밋 → main 푸시 → 서버 배포(2026-10, 대표님과 하네스 이야기 3번).
# CLAUDE.md 의 '고치면 묻지 않고 커밋 → main → 서버 배포' 를 매번 손으로 치던 것을 묶었다.
#
#   bash tools/ship.sh "커밋 제목"                 # 바뀐 것 모두 커밋하고 배포
#   bash tools/ship.sh "커밋 제목" --no-restart    # 문서만 바꿨을 때(gunicorn 재시작 생략)
#   bash tools/ship.sh --deploy                    # 커밋 없이 서버만 맞춘다(이미 푸시한 뒤)
#
# - 바뀐 템플릿(.html)이 있으면 그 안의 JS 를 먼저 node --check 로 검사하고, 오류면 멈춘다
# - 커밋 끝에는 Co-Authored-By 줄을 붙인다
# - 서버에서 마이그레이션이 필요하면 따로 돌릴 것(이 스크립트는 하지 않는다 — 서버 DB 를 바꾸는 일이라)
set -e
cd "$(git rev-parse --show-toplevel)"
SSH=(ssh -o ServerAliveInterval=60 -i 'C:\AWS\knou_key2.pem' ubuntu@hanulstudy.kr)
RESTART=1; MSG=""; DEPLOY_ONLY=0
for a in "$@"; do
  case "$a" in
    --no-restart) RESTART=0 ;;
    --deploy) DEPLOY_ONLY=1 ;;
    *) MSG="$a" ;;
  esac
done

deploy() {
  local cmd='cd ~/knou_agriculture && git pull -q'
  [ "$RESTART" = 1 ] && cmd="$cmd && sudo systemctl restart gunicorn"
  "${SSH[@]}" "$cmd && git log -1 --oneline"
}

if [ "$DEPLOY_ONLY" = 1 ]; then deploy; exit 0; fi
[ -n "$MSG" ] || { echo "커밋 제목을 주세요: bash tools/ship.sh \"제목\""; exit 1; }

# 1) 바뀐 템플릿의 JS 검사
HOOK="$HOME/.claude/hooks/jscheck_template.py"
for f in $( { git diff --name-only; git diff --name-only --cached; git ls-files --others --exclude-standard; } | sort -u | grep -E '^templates/.*\.html$' || true ); do
  [ -f "$f" ] || continue
  if [ -f "$HOOK" ]; then
    printf '{"tool_input":{"file_path":"%s"}}' "$(cygpath -m "$PWD/$f" 2>/dev/null || echo "$PWD/$f")" | python "$HOOK" || { echo "✕ $f JS 문법 오류 — 멈춥니다"; exit 1; }
  fi
done
echo "✓ 템플릿 JS 검사"

# 2) 커밋 → main
git add -A
if git diff --cached --quiet; then echo "커밋할 것이 없습니다 — 배포만 합니다"; else
  git commit -q -m "$MSG

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
  echo "✓ 커밋 $(git log -1 --format=%h)"
fi
git fetch -q && git rebase -q origin/main && git push -q origin HEAD:main
echo "✓ main 푸시"

# 3) 서버
deploy
echo "✓ 서버 배포"
