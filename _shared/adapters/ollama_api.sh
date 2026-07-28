#!/usr/bin/env bash
# ollama_api.sh — ollama worker의 HTTP API 어댑터 (localhost 로컬 추론).
# 사용: ollama_api.sh <brief-file>   (call_worker.sh가 api 경로로 호출)
# stdout = 모델 응답 텍스트, exit 0=성공.
#
# 백엔드: Ollama REST (/api/generate, stream=false). 원격 데몬이라 요금 쿼터는 없으나 네트워크 의존.
# 설정 env(선택): OLLAMA_HOST(기본 http://mad.hyper-mig.com:11434), OLLAMA_MODEL(기본 gemma3).
# backends.json의 api.brief_pass=arg1 이므로 brief는 $1로 전달된다.
set -euo pipefail

BRIEF="${1:?usage: ollama_api.sh <brief-file>}"
[ -f "$BRIEF" ] || { echo "ollama_api: brief 없음: $BRIEF" >&2; exit 6; }

command -v jq   >/dev/null 2>&1 || { echo "ollama_api: jq 필요(JSON 조립·파싱)"  >&2; exit 5; }
command -v curl >/dev/null 2>&1 || { echo "ollama_api: curl 필요(REST 호출)"     >&2; exit 5; }

HOST="${OLLAMA_HOST:-http://mad.hyper-mig.com:11434}"
MODEL="${OLLAMA_MODEL:-gemma3}"

# brief 전문을 prompt로. jq로 안전하게 JSON 조립(따옴표·개행 이스케이프).
req="$(jq -n --arg m "$MODEL" --rawfile p "$BRIEF" \
        '{model:$m, prompt:$p, stream:false}')"

# 로컬 추론은 300s 안에 못 끝날 수 있어 curl 자체 타임아웃은 넉넉히(디스패처가 상위 타임아웃 관리).
resp="$(curl -sS --fail-with-body --max-time 290 \
          -X POST "$HOST/api/generate" \
          -H 'Content-Type: application/json' \
          -d "$req")" || {
  echo "ollama_api: 호출 실패 — $HOST 에 Ollama 데몬이 떠 있고 '$MODEL'이 pull 됐는지 확인(ollama list)." >&2
  exit 4
}

# /api/generate(stream=false) 응답의 .response 가 생성 텍스트.
echo "$resp" | jq -r '.response // empty'
