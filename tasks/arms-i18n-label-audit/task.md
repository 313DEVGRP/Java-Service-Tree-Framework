# arms/html 언어팩 미적용 라벨 감사 (REQ-F-001)

## 메타

```yaml
status: done
created: 2026-07-28
updated: 2026-07-28
priority: medium
req_id: REQ-F-001
```

## Goal

`arms/html` 하위 화면의 사용자 노출 라벨을 언어팩(ko/en/jp) 적용 여부로 분류하고, 미적용 라벨 목록을 근거 경로와 함께 리포트 문서로 `artifacts/`에 산출한다.

## Constraints

- 대상 repo(`Java-Service-Tree-Framework-Frontend-Web`)에 대한 쓰기 작업 금지 — read-only
- `write_scope: tasks-only` — 산출물은 `tasks/arms-i18n-label-audit/` 내부에만
- 라벨 수정·언어팩 키 추가 등 실제 코드 변경 금지 (리포트만)

## Acceptance Criteria

- [x] `arms/html` 폴더 전체(164개 html)를 대상으로 조사했음이 리포트에 명시 — §요약·§3
- [x] `arms/js` 하위 파일을 참고해 언어팩 적용 메커니즘(`data-locale` + `bindLocaleText`)을 근거로 판정 — §2.1 호출 경로 추적
- [x] 라벨을 ① 언어팩 적용 ② 미적용(하드코딩) 으로 구분한 목록 제공 — 태깅 110 / 미태깅 9,533
- [x] 3개 언어(ko/en/jp)별 커버리지 상태 구분 — §4. jp는 0바이트 + `ja`/`jp` 파일명 불일치까지 규명
- [x] JS에서 동적으로 주입되는 문자열도 별도 항목으로 구분 — §6. 1,833건 / 118파일
- [x] 산출물이 `tasks/arms-i18n-label-audit/artifacts/` 에 존재 — 리포트 315줄 + 재현 스크립트 2개 + 상세 JSON
- [x] 리포트에 기재된 파일 경로가 실제 존재 — Orchestrator가 핵심 4건 독립 실측 (log 17:03)
- [x] 리포트 구성은 폴더·화면 단위 집계표 + 화면별 대표 사례 + 우선순위 (전건 나열 아님 — 사용자 결정 2026-07-28)
- [ ] **미충족**: ollama 보조 검증 — 호출은 정상이나 산출물이 비평 요건 미달(`workers/ollama/result.md` 참조). 리포트 사실관계는 Orchestrator 독립 실측으로 대체 확인했으나 "제3자 관점 누락 점검"은 미확보

## Worker Plan

```yaml
# 모든 worker는 사용 전 승인 필요. 비어있으면 호출 금지.
workers_approved:
- worker: claude-main
  approved_at: 2026-07-28
  purpose: arms/html·arms/js 조사 후 미적용 라벨 분류 리포트 작성 (strategist)
  approved_by: user
  write_scope: tasks-only
- worker: ollama
  approved_at: 2026-07-28
  purpose: claude-main 리포트의 분류 기준·누락 관점 보조 검증 (reviewer)
  approved_by: user
  write_scope: none

planned_workers:
- role: claude-main
  purpose: arms/html·arms/js 조사 후 미적용 라벨 분류 리포트 작성 (strategist — 분석·요약)
- role: ollama
  purpose: 리포트 분류 기준·누락 관점 자체호스팅 보조 검증 (reviewer)
```

## Context Snapshot

언어팩은 `arms/js/common.js`의 `setLocale()` → `bindLocaleText()`가 `[data-locale]` 속성을 가진 DOM만 치환하는 구조. 폴백 소스는 `arms/locales/{ko,en,jp}.json`. 사전 정찰 결과 164개 html 중 `data-locale`이 존재하는 파일은 6개뿐이고 대부분이 공유 템플릿(navigation·sidebar·header)에 집중 → 개별 화면 라벨은 사실상 미적용 상태로 추정. 전체는 `context.md` 참조.

## Notes

- `arms/locales/jp.json`은 0바이트(빈 파일) — 일본어는 키 존재 여부와 무관하게 전량 미적용.
- 1차 언어팩 소스는 Global-Config API(`/auth-anon/yml/language-config/packs/language/{locale}`), `arms/locales/*.json`은 폴백. 리포트는 폴백 파일 기준으로 판정하고 이 이중 소스를 caveat로 남긴다.
