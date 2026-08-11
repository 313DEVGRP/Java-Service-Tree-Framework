# Brief — claude-main / wiki 동시 편집 동기화

## Worker 행동 규약 (고정 — 삭제 금지)
- 요청 범위만 최소로. 사변적 추상화·기능 추가 금지
- 외과수술식 수정: 기존 스타일 유지, 무관 코드 비접촉
- 사용자 대화 채널 없음: 가정은 명시하고, 불확실·불일치는 result의 Issues/Caveats에 표면화

## Execution Context
```yaml
target_repo: <root>/Java-Service-Tree-Framework-Frontend-Web
write_scope: none
```
`<root>` = `C:\Users\www\IdeaProjects\Java-Service-Tree-Framework`

## Objective
wiki 동시 편집의 ① 중복 삽입 ② 내용 유실·오반영 원인을 코드 근거로 규명하고 개선안 제시.

## Input
`tasks/wiki-concurrent-edit-sync/sources/analysis-scope.md` — 읽을 파일·선행 가설 4건·기존 방어 흔적. 먼저 읽을 것.

## Constraints
- 근거는 `파일:줄번호`로. 코드에 있는 것만
- 항목마다 **사실**(코드 확인)/**가설**(추론) 구분
- 원인마다 재현 시나리오를 이벤트 순서로
- 개선안은 단기 완화/근본 해결 구분 + 영향범위·난이도

## Output Format
Markdown, 응답 텍스트로 반환(파일 쓰기 금지). 섹션: `요약` `동기화 구조` `원인 A: 중복 삽입` `원인 B: 내용 유실·오반영` `개선안` `Issues/Caveats`. 원인 항목마다 `근거(파일:줄)`·`사실|가설`·`재현 시나리오`.

## Do NOT
- 파일 수정·생성 (읽기 전용)
- 코드에 없는 함수·설정 지어내기
- CRDT/OT 일반론 나열 — 이 코드에 붙은 지적으로
