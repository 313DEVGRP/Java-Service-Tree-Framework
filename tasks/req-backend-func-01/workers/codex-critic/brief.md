# Brief — codex-critic / REQ-BACKEND-FUNC-01

## Worker 행동 규약 (고정)

- 요청 범위만 최소로. 사변적 추상화·기능 추가 금지
- 외과수술식 수정: 기존 스타일 유지, 무관 코드 비접촉
- 사용자 대화 채널 없음: 가정은 명시하고, 불확실·불일치는 result의 Issues/Caveats에 표면화

## Execution Context

```yaml
target_repo: /Users/leemingyu/dev/Java-Service-Tree-Framework/Java-Service-Tree-Framework-Backend-Core
write_scope: none
```

## Objective

비평 모드. 산출 CSV 가 Backend-Core 소스와 맞는지 대조하고 위반만 지적한다.

## Input

```
산출물: tasks/req-backend-func-01/artifacts/backend-core_endpoints_flat.csv
기준:   tasks/req-backend-func-01/task.md (Acceptance Criteria)
추출물: tasks/req-backend-func-01/sources/endpoints_expanded.csv
        tasks/req-backend-func-01/sources/inventory.json
감사:   tasks/req-backend-func-01/workers/claude-main/result.md
```

## 점검 항목

1. 자체 선언 엔드포인트 누락 — 소스 `@*Mapping` 과 CSV 자체 선언 행을 대조. 누락은 파일:라인으로.
2. 상속분 중복 — 같은 부모 매핑이 컨트롤러마다 반복되면 위반. 1회 기재 + 상속 컨트롤러 열거인지.
3. 컬럼 충족 — controllerClass · endpoint · package 가 모든 행에 채워졌는지. 빈칸은 no 로.
4. package 값이 선언파일 실제 패키지와 일치하는지 표본 10건 확인.
5. 경로 조합(클래스 base + 메서드 path) 정확성 표본 10건 확인.

## Constraints

- 읽기 전용(`--sandbox read-only`). 파일 쓰기·코드 실행 변경 금지
- 구조 개선 권고·리팩토링 제안 금지. 이 산출물은 레퍼런스다
- 지적은 재현 근거(파일:라인 또는 CSV 행번호) 없이 쓰지 않는다

## Output Format

응답 본문 = result.md 원문. 섹션: 판정(수락/조건부/거부) / 위반 목록(등급·근거·행번호) /
표본 검증 결과 / Issues

## Do NOT

- 개선 권고·설계 비평
- 근거 없는 추정 지적
