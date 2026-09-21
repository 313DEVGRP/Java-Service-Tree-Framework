#!/usr/bin/env bash
# 발견된 Spring 프로젝트 전부에 카탈로그 파이프라인을 돌리고 PDF 까지 만든다.
#   bash run_all.sh [task-root] [repo]
#   예) bash .claude/skills/api-catalog/scripts/run_all.sh tasks/api-catalog
#       bash .claude/skills/api-catalog/scripts/run_all.sh tasks/x Java-Service-Tree-Framework-AI
set -u
S="$(cd "$(dirname "$0")" && pwd)"
TASKROOT="${1:-tasks/api-catalog}"
ONLY="${2:-}"
EDGE="/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
STAMP="$(date +%Y%m%d)"

if [ -n "$ONLY" ]; then REPOS="$ONLY"; else REPOS="$(python "$S/discover.py" --names)"; fi

FAIL=0
for R in $REPOS; do
  export CATALOG_REPO="$R" CATALOG_TASK="$TASKROOT/$R"
  mkdir -p "$CATALOG_TASK/sources" "$CATALOG_TASK/artifacts"

  ERR=""
  for STEP in expand_inherit call_chain api_catalog csv_long api_doc; do
    if ! python "$S/$STEP.py" >/dev/null 2>"$CATALOG_TASK/.err"; then ERR="$STEP"; break; fi
  done
  if [ -n "$ERR" ]; then
    echo "[실패] $R — $ERR"; sed -n '$p' "$CATALOG_TASK/.err"; FAIL=1; continue
  fi
  rm -f "$CATALOG_TASK/.err"

  SHORT="${R#Java-Service-Tree-Framework-}"
  MD="$(ls "$CATALOG_TASK"/artifacts/*.md 2>/dev/null | head -1)"
  PDF="$CATALOG_TASK/artifacts/API카탈로그_${SHORT}_${STAMP}.pdf"

  if [ -n "$MD" ] && [ -x "$EDGE" ]; then
    HTML="$CATALOG_TASK/artifacts/.render.html"
    python "$S/render.py" "$MD" "$HTML" \
      "API 카탈로그 — $SHORT" "엔드포인트 · 호출 체인 · Feign" "v1.0" >/dev/null
    "$EDGE" --headless=new --disable-gpu --no-pdf-header-footer \
      --print-to-pdf="$(cygpath -w "$PWD/$PDF")" "$(cygpath -w "$PWD/$HTML")" >/dev/null 2>&1
    rm -f "$HTML" "$MD" "$CATALOG_TASK/artifacts/_catalog.json"
  fi

  python "$S/summary.py"
done

# 게이트웨이 라우트가 있으면 함께 안내
if python "$S/routes.py" >/dev/null 2>&1; then
  echo
  python "$S/routes.py" | head -3
  echo "  ... 전체는  python $S/routes.py"
fi

unset CATALOG_REPO CATALOG_TASK
exit $FAIL
