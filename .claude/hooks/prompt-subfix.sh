#!/usr/bin/env bash
# UserPromptSubmit hook — 사용자 프롬프트 뒤(subfix)에 붙일 지시를 추가 컨텍스트로 넣는다.
# (hook 은 프롬프트 원문을 바꿀 수 없어 hookSpecificOutput.additionalContext 로 함께 전달한다)
cat <<'JSON'
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "[prompt-subfix] 대상 모듈의 기존 코드를 전부 분석해 기존 관례를 따르는 설계를 우선한다(이미 읽은 코드는 skip). 이 요구로 작업을 만들어 진행한다. 승인·결정 사항은 묻지 말고 먼저 진행한 뒤, 임의로 정한 내용을 로그에 남긴다. 모듈의 /docs/ai/ 하네스를 참고한다."
  }
}
JSON
