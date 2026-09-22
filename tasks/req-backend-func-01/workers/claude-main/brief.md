# Brief — claude-main / REQ-BACKEND-FUNC-01

## Worker 행동 규약 (고정)

- 요청 범위만 최소로. 사변적 추상화·기능 추가 금지
- 외과수술식 수정: 기존 스타일 유지, 무관 코드 비접촉
- 사용자 대화 채널 없음: 가정은 명시하고, 불확실·불일치는 result의 Issues/Caveats에 표면화

## Execution Context

```yaml
target_repo: /Users/leemingyu/dev/Java-Service-Tree-Framework/Java-Service-Tree-Framework-Backend-Core
write_scope: tasks-only
```

## Objective

엔드포인트 추출물의 누락 감사 + 컨트롤러별 플랫 CSV 변환 스펙·코드. 파일 생성은 Orchestrator 가 한다.

## Input

```
task:   tasks/req-backend-func-01/task.md
req:    tasks/req-backend-func-01/sources/request.md
추출물: tasks/req-backend-func-01/sources/endpoints_expanded.csv (92컨트롤러/자체360/상속821)
        tasks/req-backend-func-01/sources/inventory.json
규약:   .claude/skills/api-catalog/SKILL.md (추출기·함정 6종·기준값 필독)
```

## 할 일

1. 누락 감사 — 추출기 정규식이 놓칠 자체 선언 엔드포인트를 소스에서 확인.
   점검: 경로 배열 · 클래스 다중 경로 · `@Controller` 없는 매핑 · 인터페이스 선언.
   놓친 건은 파일:라인으로 열거.
2. 컬럼 스펙 — controllerClass · endpoint · package 필수. 자체 선언 1건 1행,
   상속분은 컨트롤러마다 반복 금지(부모 매핑 1행 + 상속 컨트롤러 열거).
3. 변환 코드 — 위 스펙대로 추출물을 읽어 CSV 를 쓰는 python(표준 라이브러리만)을 코드블록으로.

## Constraints

- 읽기 전용. 저장소 수정·빌드·테스트 실행 금지
- 레퍼런스다. 비평·결함 지적·개선 권고 금지
- 추출물에 없는 엔드포인트 창작 금지

## Output Format

응답 본문 = result.md 원문. 섹션: 누락 감사 / 컬럼 스펙 / 변환 코드 / 예상 행수 /
Verification Checklist / Issues

## Do NOT

- 파일 쓰기 (저장소·엑셀·tasks/ 전부)
- 상속분을 컨트롤러마다 반복하는 스펙
