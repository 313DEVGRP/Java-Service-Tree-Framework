#!/bin/bash
# knot drain — inbox 일괄 ingest → lint → 리포트 (배포판).
# 기본 OFF: 자동으로 돌지 않는다. cron/launchd가 부를 때만 동작(설치 setup에서 등록).
#
# 검증된 정본 패턴 계승(맨바닥 재작성 금지):
#   - 건당 1처리 → 1커밋, idempotent(재개 = 재실행)
#   - 진척 판정 = "새 커밋 생김 + inbox 감소". 미충족이면 러너 조용한 실패·쿼터로 보고 중단
#   - 진척 없으면 git reset --hard + clean -fd 로 미완성분 무손상 복구(원본은 inbox에 남음)
#   - MAX_ITER 무한루프 방지, 시작 가드(트리 더티면 중단·reset 안 함)
#
# 알림 3단(아래 notify()):
#   ① 바닥(항상): STATUS 파일 + knot log.md 요약 커밋 + 실패 시 non-zero exit
#   ② 기본 push(제로설정): OS 데스크톱 알림(mac osascript / linux notify-send)
#   ③ 선택: vault 밖 외부 채널(KNOT_NOTIFY_CMD env 또는 ~/.config/knot/notify.sh)
#
# 보안: 이 스크립트는 공개 vault에 포함된다. 비밀값·웹훅·토큰·개인경로 0.
#       외부 알림 설정은 vault 밖에만 두고 여기선 "참조"만 한다.
set -u

# --- 설정 (env 또는 플래그로 주입; 번들에 사용자값을 박지 않는다) ---
RUNNER="${KNOT_RUNNER:-agy}"        # agy(기본·권장) | claude | codex | gemini | 임의 CLI
MODEL="${KNOT_MODEL:-}"             # agy 등 per-call 모델 핀(비우면 러너 기본값)
MAX_ITER="${KNOT_MAX_ITER:-25}"

while [ $# -gt 0 ]; do
  case "$1" in
    --runner)   RUNNER="$2"; shift 2 ;;
    --model)    MODEL="$2"; shift 2 ;;
    --max-iter) MAX_ITER="$2"; shift 2 ;;
    -h|--help)  echo "사용: drain.sh [--runner agy|claude|codex|gemini] [--model <핀>] [--max-iter N]"; exit 0 ;;
    *)          echo "알 수 없는 인자: $1" >&2; exit 2 ;;
  esac
done

# --- vault 위치 ($KNOT_VAULT 기준) ---
VAULT="${KNOT_VAULT:-}"
if [ -z "$VAULT" ] || [ ! -d "$VAULT" ]; then
  echo "KNOT_VAULT 미설정 또는 디렉토리 없음" >&2
  exit 1
fi
cd "$VAULT" || exit 1

STATE="$VAULT/.knot"               # 런타임 상태(.gitignore 처리) — 트리 클린 유지
mkdir -p "$STATE"
STATUS="$STATE/drain-status.txt"
RUNLOG="$STATE/drain.log"
PROMPT="schema.md와 prompts/ingest.md를 정독하고 그대로 실행하라"

# 러너 1회 호출 — 모델 핀은 agy의 --model로 per-call 지정(공백 포함 이름 보존, bash 3.2 안전)
run_ingest() {
  case "$RUNNER" in
    agy)
      if [ -n "$MODEL" ]; then
        agy --model "$MODEL" --dangerously-skip-permissions --print-timeout 9m -p "$PROMPT"
      else
        agy --dangerously-skip-permissions --print-timeout 9m -p "$PROMPT"
      fi ;;
    claude) claude -p "$PROMPT" --dangerously-skip-permissions ;;
    codex)  codex exec "$PROMPT" ;;
    gemini) gemini -p "$PROMPT" ;;
    *)      "$RUNNER" -p "$PROMPT" ;;
  esac
}

# ②③ 알림 — 비밀값은 스크립트에 없다. ③은 vault 밖 설정을 참조만.
notify() {
  local msg="$1"
  if command -v osascript >/dev/null 2>&1; then
    osascript -e "display notification \"${msg//\"/}\" with title \"knot drain\"" >/dev/null 2>&1 || true
  elif command -v notify-send >/dev/null 2>&1; then
    notify-send "knot drain" "$msg" >/dev/null 2>&1 || true
  fi
  if [ -n "${KNOT_NOTIFY_CMD:-}" ]; then
    printf '%s\n' "$msg" | sh -c "$KNOT_NOTIFY_CMD" >/dev/null 2>&1 || true
  elif [ -x "$HOME/.config/knot/notify.sh" ]; then
    "$HOME/.config/knot/notify.sh" "$msg" >/dev/null 2>&1 || true
  fi
}

TOTAL=$(ls inbox/ 2>/dev/null | wc -l | tr -d ' ')
DONE=0
STOP_REASON=""
echo "[$(date '+%F %T')] drain 시작 — runner=$RUNNER inbox ${TOTAL}건" >> "$RUNLOG"

for ((i=1; i<=MAX_ITER; i++)); do
  COUNT=$(ls inbox/ 2>/dev/null | wc -l | tr -d ' ')
  [ "$COUNT" -eq 0 ] && break
  if [ -n "$(git status --porcelain)" ]; then
    STOP_REASON="시작 가드 실패: 트리 더티(외부 변경 가능성, reset 안 함)"
    break
  fi
  HEAD_BEFORE=$(git rev-parse HEAD 2>/dev/null || echo none)
  NEXT=$(ls inbox/ | head -1)
  echo "[$(date '+%F %T')] [$i] 처리: $NEXT (잔여 $COUNT)" >> "$RUNLOG"
  run_ingest >> "$RUNLOG" 2>&1
  HEAD_AFTER=$(git rev-parse HEAD 2>/dev/null || echo none)
  NEWCOUNT=$(ls inbox/ 2>/dev/null | wc -l | tr -d ' ')
  if [ "$HEAD_AFTER" = "$HEAD_BEFORE" ] || [ "$NEWCOUNT" -ge "$COUNT" ]; then
    git reset --hard HEAD >> "$RUNLOG" 2>&1
    git clean -fd >> "$RUNLOG" 2>&1
    STOP_REASON="진척 없음($NEXT: 새 커밋/inbox 감소 미충족 — 러너 조용한 실패·쿼터 가능성). reset 복원"
    break
  fi
  DONE=$((DONE+1))
  echo "[$(date '+%F %T')] [$i] 완료: $NEXT → $(git log --oneline -1)" >> "$RUNLOG"
  sleep 5
done

REMAIN=$(ls inbox/ 2>/dev/null | wc -l | tr -d ' ')
[ -z "$STOP_REASON" ] && [ "$REMAIN" -gt 0 ] && STOP_REASON="MAX_ITER($MAX_ITER) 도달"

# lint(기계 검사) — 트리 클린일 때만
LINT_LINE=""
if [ -z "$(git status --porcelain)" ] && [ -f scripts/lint.py ]; then
  if python3 scripts/lint.py >> "$RUNLOG" 2>&1; then LINT_LINE="lint OK"; else LINT_LINE="lint ERROR(상세 .knot/drain.log)"; fi
fi

SUMMARY="knot drain: 성공 $DONE/$TOTAL, 잔여 $REMAIN. ${STOP_REASON:-전건 완료}.${LINT_LINE:+ $LINT_LINE}"

# ① 바닥: STATUS 파일(항상)
{
  echo "drain 종료 $(date '+%F %T')"
  echo "runner=$RUNNER  성공 $DONE/$TOTAL  잔여 inbox $REMAIN"
  if [ -n "$STOP_REASON" ]; then echo "중단: $STOP_REASON"; echo "재개: drain.sh 재실행"; else echo "전건 완료"; fi
  [ -n "$LINT_LINE" ] && echo "$LINT_LINE"
  echo "HEAD: $(git log --oneline -1 2>/dev/null)"
} > "$STATUS"

# ① 바닥: knot log.md 요약 append + 커밋(트리 클린 + 실제 처리분 있을 때만)
if [ "$DONE" -gt 0 ] && [ -z "$(git status --porcelain)" ]; then
  {
    echo ""
    echo "## [$(date '+%F')] drain — inbox ingest $DONE/$TOTAL (runner=$RUNNER)"
    echo ""
    if [ -n "$STOP_REASON" ]; then echo "- 중단: $STOP_REASON (잔여 ${REMAIN}건, 재개=재실행)"; else echo "- 전건 완료(잔여 0)"; fi
  } >> log.md
  git add log.md
  git commit -q -m "drain: inbox ingest $DONE/$TOTAL" || true
fi

# ②③ 알림
notify "$SUMMARY"
echo "[$(date '+%F %T')] $SUMMARY" >> "$RUNLOG"

# ① 바닥: 진척 0인데 처리할 게 남았으면(쿼터·시작가드 등) 실패 신호 — cron이 조용히 죽지 않게
if [ "$DONE" -eq 0 ] && [ "$REMAIN" -gt 0 ]; then
  exit 1
fi
exit 0
