# Brief — codex-critic / REQ-FRONTEND-FUNC-01

## Worker 행동 규약 (고정)

- 요청 범위만 최소로. 사변적 추상화·기능 추가 금지
- 외과수술식 수정: 기존 스타일 유지, 무관 코드 비접촉
- 사용자 대화 채널 없음: 가정은 명시하고, 불확실·불일치는 result의 Issues/Caveats에 표면화

## Execution Context

```yaml
target_repo: /Users/leemingyu/dev/Java-Service-Tree-Framework/Java-Service-Tree-Framework-Frontend-Web
write_scope: none
```

## Objective

비평 모드. 산출 CSV 가 js 소스와 맞는지 대조하고 위반만 지적한다.

## Input

```
산출물: tasks/req-frontend-func-01/artifacts/
기준:   tasks/req-frontend-func-01/task.md (Acceptance Criteria)
스펙:   tasks/req-frontend-func-01/workers/claude-main/result.md
```

## 점검 항목

1. `/` 로 끝나는 apiurl 이 있는지. 있으면 행번호로.
2. 호출 지점 누락 — `$.ajax`·`$.get`·`$.post`·`fetch` 를 소스에서 세어 CSV 행수와 대조. 차이는 파일:라인으로.
3. 필수 3컬럼(menuname·jsfile·apiurl) 공란 행. 행번호로.
4. URL 복원 정확성 표본 10건 — 연결·템플릿로 조합된 건 위주로 소스와 대조.
5. 메뉴 매핑 표본 10건 — `page-navigation.html` 및 backoffice 메뉴 정의와 대조.
6. arms·backoffice 양쪽이 대상에 들어갔는지.

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
