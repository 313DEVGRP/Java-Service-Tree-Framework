#!/usr/bin/env bash
# ollama_api.sh — ollama worker의 HTTP API 어댑터 (자체호스팅 Ollama 데몬 추론).
# 사용: ollama_api.sh <brief-file>   (call_worker.sh가 api 경로로 호출)
# stdout = 모델 응답 텍스트, exit 0=성공.
#
# 백엔드: Ollama REST (/api/chat, stream=false). 원격 데몬이라 요금 쿼터는 없으나 네트워크 의존.
# brief에 <!-- SYSTEM -->…<!-- /SYSTEM --> 마커가 있으면 그 안쪽을 system 메시지로 분리한다.
# 설정 env(선택): OLLAMA_HOST(기본 http://mad.hyper-mig.com:11434), OLLAMA_MODEL(기본 gemma3).
# backends.json의 api.brief_pass=arg1 이므로 brief는 $1로 전달된다.
set -euo pipefail

BRIEF="${1:?usage: ollama_api.sh <brief-file>}"
[ -f "$BRIEF" ] || { echo "ollama_api: brief 없음: $BRIEF" >&2; exit 6; }

command -v jq   >/dev/null 2>&1 || { echo "ollama_api: jq 필요(JSON 조립·파싱)"  >&2; exit 5; }
command -v curl >/dev/null 2>&1 || { echo "ollama_api: curl 필요(REST 호출)"     >&2; exit 5; }

HOST="${OLLAMA_HOST:-http://mad.hyper-mig.com:11434}"
MODEL="${OLLAMA_MODEL:-gemma3}"

# /api/chat 사용 — 지시(system)와 점검 대상(user)을 분리한다.
# 소형 모델은 지시와 데이터가 한 텍스트에 섞이면 긴 쪽 문맥에 끌려 역할을 오인한다
# (2026-08-25 실측: 12,688자 brief에서 gemma3·qwen2.5:7b 모두 요구 형식 0/8 응답).
#
# 분리 규약: brief에 아래 마커가 있으면 그 안쪽을 system, 바깥을 user로 보낸다.
#   <!-- SYSTEM --> ... <!-- /SYSTEM -->
# 마커가 없으면 brief 전문을 user로 보낸다(기존 brief 하위호환 — 동작 변화 없음).
sys="$(sed -n '/<!-- SYSTEM -->/,/<!-- \/SYSTEM -->/p' "$BRIEF" \
        | sed '1d;$d')"
if [ -n "$sys" ]; then
  usr="$(sed '/<!-- SYSTEM -->/,/<!-- \/SYSTEM -->/d' "$BRIEF")"
else
  usr="$(cat "$BRIEF")"
fi

# jq로 안전하게 JSON 조립(따옴표·개행 이스케이프). system은 있을 때만 넣는다.
req="$(jq -n --arg m "$MODEL" --arg s "$sys" --arg u "$usr" \
        '{model:$m, stream:false,
          messages: (if ($s|length) > 0
                     then [{role:"system", content:$s}, {role:"user", content:$u}]
                     else [{role:"user", content:$u}] end)}')"

# 추론이 300s 안에 못 끝날 수 있어 curl 자체 타임아웃은 넉넉히(디스패처가 상위 타임아웃 관리).
resp="$(curl -sS --fail-with-body --max-time 290 \
          -X POST "$HOST/api/chat" \
          -H 'Content-Type: application/json' \
          -d "$req")" || {
  echo "ollama_api: 호출 실패 — $HOST 에 Ollama 데몬이 떠 있고 '$MODEL'이 pull 됐는지 확인(ollama list)." >&2
  exit 4
}

# /api/chat(stream=false) 응답의 .message.content 가 생성 텍스트.
echo "$resp" | jq -r '.message.content // empty'
