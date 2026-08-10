# Brief — claude-main / wiki 동기화 개선 SRS (2단계)

<!-- 호출 당시 경로는 tasks/wiki-sync-srs/ 였음. 폴더 통합 후 경로만 정정. log.md 2026-08-07 17:16 [DECISION] 참조 -->

## Worker 행동 규약 (고정 — 삭제 금지)
- 요청 범위만 최소로. 사변적 추상화·기능 추가 금지
- 외과수술식 수정: 기존 스타일 유지, 무관 코드 비접촉
- 사용자 대화 채널 없음: 가정은 명시하고, 불확실·불일치는 result의 Issues/Caveats에 표면화

## Execution Context
```yaml
target_repo: N/A
write_scope: none   # 파일 쓰지 말 것. 응답 텍스트로만 반환
```

## Objective
원인 분석서를 입력으로 **wiki 동시 편집 동기화 개선 SRS**를 작성한다.

## Input
```
tasks/wiki-concurrent-edit-sync/workers/claude-main/result.md   # 분석 원문(정본)
tasks/wiki-concurrent-edit-sync/sources/analysis-scope.md       # 대상 파일·범위
tasks/wiki-concurrent-edit-sync/task.md                         # Goal·수용기준
```
근거 확인 필요 시 실제 코드도 읽을 것.

## Constraints
- 분석서에 없는 사실 창작 금지. **가설** 표기 항목(B-3·B-4·B-5·Caveat 7)은 **선행 조사 항목**으로 분리
- 원인 11건(A-1~A-4, B-1~B-7) **전건** 추적. 누락 시 사유 명시
- 요구사항은 구현 지시가 아닌 "무엇을 만족해야 하는가"로. 각각 **검증 가능한 수용 기준** 필수
- 기존 스택(CKEditor4+STOMP/SockJS+Spring) 전제. 프레임워크 교체 금지

## Output Format
Markdown, 응답 텍스트 반환. 섹션: `1.개요` `2.현행 시스템과 문제` `3.설계 목표·원칙` `4.기능 요구사항`(FR-nn: 설명·근거원인·수용기준·우선순위) `5.비기능 요구사항`(NFR-nn) `6.메시지 프로토콜 설계`(전후 스키마) `7.단계별 적용 계획` `8.검증 계획` `9.원인↔요구사항 추적표` `10.선행 조사 항목` `11.Issues/Caveats`

## Do NOT
- 파일 수정·생성
- 분석서에 없는 코드 사실 지어내기
- CRDT/OT 일반론 나열 — 이 시스템에 맞춘 요구사항으로
