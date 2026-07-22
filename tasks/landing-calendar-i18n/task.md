# landing_calendar 다국어(i18n) 지원 추가

## 메타

```yaml
status: done
created: 2026-07-22
updated: 2026-07-22
priority: medium
```

## Goal

`Java-Service-Tree-Framework-Frontend-Web` 모듈의 `arms/html/landing_calendar` 페이지에 영어·한국어·중국어·일본어 4개 언어를 지원하는 언어팩 기능을 추가한다.

## Constraints

- 대상 페이지: `Java-Service-Tree-Framework-Frontend-Web/arms/html/landing_calendar/content-container.html`
- 기존 스타일·구조 유지. 요청 범위(다국어 언어팩) 밖의 리팩토링 금지 (외과수술식)
- 코드베이스 기존 패턴(vanilla JS · jQuery · Bootstrap · FullCalendar) 준수. 새 프레임워크·빌드 단계 도입 금지
- 지원 언어: en, ko, zh, ja (4개)
- 시크릿·환경별 URL 하드코딩 금지

## Acceptance Criteria

- [x] 페이지 내 사용자 노출 문자열(제목·설명·캘린더 UI 라벨)이 언어팩으로 분리됨 (data-lc-i18n + LANDING_I18N 사전)
- [x] en / ko / zh / ja 4개 언어 전환이 동작함 (셀렉터 + 전용 저장키)
- [x] FullCalendar 로케일(요일·버튼 등)도 선택 언어와 연동됨 (locales-all + setOption locale)
- [x] 기존 레이아웃·스타일 회귀 없음 (추가 CSS만·전역 common.js 미변경)

## Worker Plan

```yaml
# claude-main만 승인 게이트 대상. frontend-expert는 2계층 도메인 서브에이전트라
# workers_approved 게이트 대상이 아니나, 실제 호출이 발생하므로 투명성 위해 기록.
workers_approved:
  - worker: claude-main
    approved_at: 2026-07-22
    purpose: 언어팩(en/ko/zh/ja) 기능 설계·구현 (strategist)
    approved_by: user

planned_workers:
  - role: claude-main
    purpose: 언어팩 지원 기능 추가 (설계·구현)
  - role: frontend-expert   # 2계층 도메인 서브에이전트 (승인 게이트 밖)
    purpose: 언어팩 기능 리뷰 → 변경점 있으면 claude-main에 1회 수정 요청
```

## Context Snapshot

<!-- 상세: tasks/landing-calendar-i18n/context.md -->

대상 페이지는 FullCalendar 기반 주간 캘린더 목업. 현재 문자열이 HTML에 하드코딩되어 있음
("Weekly Schedule", "주간 캘린더", 설명문, blockquote 안내문 등 — en/ko 혼재).
다국어 전환 UI + 언어팩 사전 + FullCalendar locale 연동이 필요.

## Notes

- 흐름: claude-main(구현) → frontend-expert(리뷰, 최대 1회 수정 요청) → claude-main(반영)
- Producer-Reviewer 토폴로지. 단 reviewer가 codex-critic이 아닌 도메인 서브에이전트(frontend-expert)
- frontend-expert는 직접 파일 쓰기 가능하나, 본 흐름에서는 "리뷰 후 claude-main에 수정 요청" 역할로 한정
