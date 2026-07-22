# landing_calendar 페이지 디자인 통일 (glass 디자인 시스템 적용)

## 메타

```yaml
status: done
created: 2026-07-22
updated: 2026-07-22
priority: medium
```

## Goal

`arms/html/landing_calendar/content-container.html`를 다른 landing_* 페이지의 공통 glass 디자인 시스템(색감·레이아웃)에 맞게 재디자인하되, FullCalendar 기능·언어선택·i18n을 100% 보존한다.

## Constraints

- 대상 파일: `Java-Service-Tree-Framework-Frontend-Web/arms/html/landing_calendar/content-container.html`
- FullCalendar 초기화 JS 동작, `#landing_calendar_lang` 언어 셀렉터, 목업 데이터 동작 유지
- 모든 `data-lc-i18n` 속성/키 그대로 유지 (i18n 파이프라인 비접촉)
- landing_* 공통 `.glass` 클래스(`arms/css/common.css`) 및 기존 위젯 구조 재사용
- 외과수술식: 디자인(CSS·마크업 구조)만 변경, 무관 코드·다른 페이지 비접촉

## Acceptance Criteria

- [x] claude-main이 참조 페이지 선정 + 액센트/레이아웃 디자인 방향 제안
- [x] frontend-expert가 제안대로 content-container.html 재디자인
- [x] FullCalendar 위젯 정상 렌더 (구조 파괴 없음 — #landing_calendar_view id·마운트 불변)
- [x] 모든 `data-lc-i18n` 키 보존(6키), 언어 셀렉터 동작 유지(id·option 4개 불변)
- [x] claude-main이 적용 결과 어울림 리뷰 → 판정 [개선 불필요], 재수정 0회
- [x] Verification Checklist 통과, log.md에 [VERIFICATION] 기록

## Worker Plan

```yaml
workers_approved:
  - worker: claude-main
    approved_at: 2026-07-22
    purpose: 참조 landing 페이지 기반 디자인 방향 제안 + 적용 결과 어울림 리뷰(개선 요청 판단)
    approved_by: user

planned_workers:
  - role: claude-main
    purpose: 디자인 방향(액센트·레이아웃) 제안 및 적용 결과 리뷰
# frontend-expert는 Orchestrator 내부 서브에이전트(worker pool 아님) — 디자인 구현·수정 담당
```

## Context Snapshot

현재 landing_calendar는 라이트 테마의 미니멀 페이지(FullCalendar timeGridWeek + 언어 셀렉터). 다른 landing_* 페이지들은 다크 glass 디자인 시스템(페이지별 액센트, header eyebrow/title/subtitle, KPI 카드, `.widget.glass`)을 공유. 목표는 캘린더 페이지를 이 공통 시스템에 편입시키되 기능은 유지. 참조 후보: landing_business(teal), 그 외 landing_* 다수. 상세: `context.md`.

## Notes

- 흐름: claude-main(방향 제안) → frontend-expert(구현) → claude-main(리뷰) → 필요 시 frontend-expert(재수정) → Verification
- 사용자 결정: 참조=일관성 우선(claude-main이 캘린더에 맞는 액센트 제안), 기능·i18n 100% 보존
