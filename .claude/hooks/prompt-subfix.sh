#!/usr/bin/env bash
# UserPromptSubmit hook — 사용자 프롬프트 뒤(subfix)에 붙일 지시를 추가 컨텍스트로 넣는다.
# (hook 은 프롬프트 원문을 바꿀 수 없어 hookSpecificOutput.additionalContext 로 함께 전달한다)
cat <<'JSON'
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "[prompt-subfix] 작업 대상 모듈에 이미 구현된 기존 코드를 전부 분석하고,\n이미 구현된 코드 관례를 일관되게 유지하는 방향으로 설계를 우선한다.\n( 이미 읽은 코드는 분석을 skip 한다 )\n위 요구사항을 대상으로 작업을 만들고 진행한다.\n승인이나 결정이 필요한 내용은 나에게 물어보지 말고 우선 진행을 하고,\n로그에 임의 결정한 사항을 정리해서 남긴다.\n작업 대상 모듈에는 /docs/ai/ 밑에 재사용 가능한 하네스가 있으니 참고해서 작업을 진행한다."
  }
}
JSON
