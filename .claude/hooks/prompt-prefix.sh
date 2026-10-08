#!/usr/bin/env bash
# UserPromptSubmit hook — 사용자 프롬프트 앞(prefix)에 붙일 지시를 추가 컨텍스트로 넣는다.
# (hook 은 프롬프트 원문을 바꿀 수 없어 hookSpecificOutput.additionalContext 로 함께 전달한다)
cat <<'JSON'
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "[prompt-prefix] Java-Service-Tree-Framework-Frontend-Web/docs/file 의 모든 파일(프로젝트 산출물)을 최대한 자세히 읽고 분석한다(이미 읽은 파일은 skip)."
  }
}
JSON
