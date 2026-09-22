# Brief — codex-critic / REQ-MAPPING-FUNC-01

## Worker 행동 규약 (고정)

- 요청 범위만 최소로. 사변적 추상화·기능 추가 금지
- 외과수술식 수정: 기존 스타일 유지, 무관 코드 비접촉
- 사용자 대화 채널 없음: 가정은 명시하고, 불확실·불일치는 result의 Issues/Caveats에 표면화

## Execution Context

```yaml
target_repo: /Users/leemingyu/dev/Java-Service-Tree-Framework
write_scope: none
```

## Objective

비평 모드. 매핑 판정과 메뉴명의 오탐·미탐만 지적한다.

## Input

```
산출물: tasks/req-mapping-func-01/artifacts/fe-be_mapping-gaps.csv
기준:   tasks/req-mapping-func-01/task.md · sources/gateway-rules.md
생성기: .claude/skills/api-catalog/scripts/fe_be_gaps.py
입력:   tasks/req-backend-func-01/artifacts/backend-core_endpoints_flat.csv
        tasks/req-frontend-func-01/artifacts/frontend-web_api-calls_flat.csv
```

## 점검 항목

1. **오탐** — `FE→BE없음` 행 중 실제로는 백엔드에 있는 것. 표본 15건 대조.
2. **미탐** — 매핑 성립으로 빠진 것 중 실제 대응이 없는 것. 표본 10건.
3. **정규화** — 권한·서비스 세그먼트 변환이 규칙대로인지 표본 10건.
4. **메뉴명** — `menusource` 가 네비·header 인 행 10건을 html 과 대조. 틀린 것만.
5. **상속 표기** — `provider` 가 상속인 행이 백엔드 카탈로그 `kind=inherited` 와 일치하는지.
6. 매핑 성립 행 혼입·필수 컬럼 공란.

## Constraints

- 읽기 전용(`--sandbox read-only`). 파일 쓰기 금지
- 구조 개선 권고·리팩토링 제안 금지. 레퍼런스 산출물이다
- 지적은 재현 근거(CSV 행번호 또는 소스 파일:라인) 없이 쓰지 않는다

## Output Format

응답 본문 = result.md 원문. 섹션: 판정(수락/조건부/거부) / 오탐 / 미탐 / 표본 검증 / Issues

## Do NOT

- 개선 권고·설계 비평
- 근거 없는 추정 지적
